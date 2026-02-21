"""
Backfill script: Look up MBIDs for artists, then fetch setlists from Setlist.fm for all shows.
Rate limits: MusicBrainz 1 req/sec, Setlist.fm ~2 req/sec
"""
import os
import sys
import time
import requests

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db, Artist, Show, SetlistSong

TARGET_USER_ID = 1
SETLISTFM_API_KEY = None

MB_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'ShareMyShows/1.0 (tim.h.orlando@gmail.com)'
}


def lookup_mbids(app):
    """Step 1: Look up MusicBrainz IDs for artists that don't have one."""
    with app.app_context():
        artists = Artist.query.filter(
            Artist.mbid.is_(None) | (Artist.mbid == '')
        ).all()

        # Only artists that have shows for our user
        show_artist_ids = set(
            r[0] for r in db.session.query(Show.artist_id)
            .filter_by(user_id=TARGET_USER_ID).distinct().all()
        )
        artists = [a for a in artists if a.id in show_artist_ids]

        print(f'\n=== Step 1: Looking up MBIDs for {len(artists)} artists ===\n')
        found = 0
        not_found = 0

        for i, artist in enumerate(artists):
            try:
                resp = requests.get(
                    'https://musicbrainz.org/ws/2/artist/',
                    headers=MB_HEADERS,
                    params={'query': artist.name, 'fmt': 'json', 'limit': 5},
                    timeout=10
                )
                if resp.status_code == 200:
                    results = resp.json().get('artists', [])
                    # Try exact name match first, then best match
                    match = None
                    for r in results:
                        if r.get('name', '').lower() == artist.name.lower():
                            match = r
                            break
                    if not match and results:
                        # Take top result if score is high enough
                        if results[0].get('score', 0) >= 90:
                            match = results[0]

                    if match:
                        artist.mbid = match['id']
                        db.session.commit()
                        found += 1
                        print(f'  [{i+1}/{len(artists)}] {artist.name} -> {match["id"]} ({match.get("disambiguation", "")})')
                    else:
                        not_found += 1
                        print(f'  [{i+1}/{len(artists)}] {artist.name} -> NOT FOUND')
                else:
                    not_found += 1
                    print(f'  [{i+1}/{len(artists)}] {artist.name} -> HTTP {resp.status_code}')
            except Exception as e:
                not_found += 1
                print(f'  [{i+1}/{len(artists)}] {artist.name} -> ERROR: {e}')

            time.sleep(1.1)  # MusicBrainz rate limit

        print(f'\nMBID results: {found} found, {not_found} not found')
        return found


def fetch_setlists(app):
    """Step 2: Fetch setlists from Setlist.fm for shows that don't have one."""
    global SETLISTFM_API_KEY
    SETLISTFM_API_KEY = os.getenv('SETLISTFM_API_KEY')
    if not SETLISTFM_API_KEY:
        # Try loading from .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('SETLISTFM_API_KEY='):
                        SETLISTFM_API_KEY = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break

    if not SETLISTFM_API_KEY:
        print('ERROR: SETLISTFM_API_KEY not found in environment or .env file')
        return

    with app.app_context():
        # Get all shows for the user that don't already have setlist songs
        shows_with_setlist = set(
            r[0] for r in db.session.query(SetlistSong.show_id).distinct().all()
        )
        all_shows = Show.query.filter_by(user_id=TARGET_USER_ID).order_by(Show.date).all()
        shows_to_process = [s for s in all_shows if s.id not in shows_with_setlist]

        print(f'\n=== Step 2: Fetching setlists for {len(shows_to_process)} shows ===\n')

        headers = {
            'Accept': 'application/json',
            'x-api-key': SETLISTFM_API_KEY
        }

        success = 0
        no_mbid = 0
        no_setlist = 0
        errors = 0

        for i, show in enumerate(shows_to_process):
            artist = show.artist
            if not artist or not artist.mbid:
                no_mbid += 1
                print(f'  [{i+1}/{len(shows_to_process)}] {show.date} {artist.name if artist else "?"} - SKIP (no MBID)')
                continue

            date_str = show.date.strftime('%d-%m-%Y')
            label = f'{show.date} {artist.name}'

            try:
                resp = requests.get(
                    'https://api.setlist.fm/rest/1.0/search/setlists',
                    headers=headers,
                    params={'artistMbid': artist.mbid, 'date': date_str},
                    timeout=10
                )

                if resp.status_code == 404 or resp.status_code != 200:
                    no_setlist += 1
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - no setlist found')
                    time.sleep(0.5)
                    continue

                result = resp.json()
                setlists = result.get('setlist', [])
                if not setlists:
                    no_setlist += 1
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - empty result')
                    time.sleep(0.5)
                    continue

                # Parse the first matching setlist
                setlist = setlists[0]
                sets_data = setlist.get('sets', {}).get('set', [])

                order = 1
                songs_added = 0
                for set_item in sets_data:
                    set_name = set_item.get('name', '')
                    for song in set_item.get('song', []):
                        song_name = song.get('name', '')
                        if not song_name:
                            continue

                        notes_parts = []
                        if set_name:
                            notes_parts.append(set_name)
                        if song.get('info'):
                            notes_parts.append(song['info'])

                        cover_data = song.get('cover')
                        is_cover = cover_data is not None
                        original_artist = cover_data.get('name') if cover_data else None

                        with_data = song.get('with')
                        with_artist = with_data.get('name') if with_data else None

                        setlist_song = SetlistSong(
                            show_id=show.id,
                            title=song_name,
                            order=order,
                            notes='; '.join(notes_parts) if notes_parts else None,
                            is_cover=is_cover,
                            original_artist=original_artist,
                            with_artist=with_artist,
                        )
                        db.session.add(setlist_song)
                        order += 1
                        songs_added += 1

                if songs_added > 0:
                    db.session.commit()
                    success += 1
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - {songs_added} songs added')
                else:
                    no_setlist += 1
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - setlist found but empty')

            except Exception as e:
                errors += 1
                print(f'  [{i+1}/{len(shows_to_process)}] {label} - ERROR: {e}')

            time.sleep(0.5)  # Be nice to Setlist.fm

        print(f'\nSetlist results: {success} populated, {no_setlist} not found, {no_mbid} skipped (no MBID), {errors} errors')
        print(f'Total shows with setlists now: {len(shows_with_setlist) + success}/{len(all_shows)}')


if __name__ == '__main__':
    app = create_app()
    lookup_mbids(app)
    fetch_setlists(app)
    print('\nDone!')
