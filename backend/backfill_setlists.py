"""
Backfill script: Look up MBIDs for artists, then fetch setlists from Setlist.fm for all shows.
Falls back to Concert Archives when Setlist.fm has no data.
Rate limits: MusicBrainz 1 req/sec, Setlist.fm ~2 req/sec, Concert Archives ~3 sec
"""
import os
import sys
import time
import requests

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db, Artist, Show, SetlistSong
from app.utils.concert_archives import fetch_setlist_from_concert_archives

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
    """Step 2: Fetch setlists from Setlist.fm (with Concert Archives fallback) for shows that don't have one."""
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
        print('WARNING: SETLISTFM_API_KEY not found, will only use Concert Archives')

    with app.app_context():
        # Get all shows for the user that don't already have setlist songs
        shows_with_setlist = set(
            r[0] for r in db.session.query(SetlistSong.show_id).distinct().all()
        )
        all_shows = Show.query.filter_by(user_id=TARGET_USER_ID).order_by(Show.date).all()
        shows_to_process = [s for s in all_shows if s.id not in shows_with_setlist]

        print(f'\n=== Step 2: Fetching setlists for {len(shows_to_process)} shows ===\n')

        sfm_headers = {
            'Accept': 'application/json',
            'x-api-key': SETLISTFM_API_KEY
        } if SETLISTFM_API_KEY else None

        success = 0
        success_ca = 0
        no_setlist = 0
        errors = 0

        for i, show in enumerate(shows_to_process):
            artist = show.artist
            label = f'{show.date} {artist.name if artist else "?"}'
            songs_data = []
            source = None

            # Try Setlist.fm first (requires MBID + API key)
            if sfm_headers and artist and artist.mbid:
                date_str = show.date.strftime('%d-%m-%Y')
                try:
                    resp = requests.get(
                        'https://api.setlist.fm/rest/1.0/search/setlists',
                        headers=sfm_headers,
                        params={'artistMbid': artist.mbid, 'date': date_str},
                        timeout=10
                    )

                    if resp.status_code == 200:
                        result = resp.json()
                        setlists = result.get('setlist', [])
                        if setlists:
                            sets_data = setlists[0].get('sets', {}).get('set', [])
                            order = 1
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

                                    songs_data.append({
                                        'title': song_name,
                                        'order': order,
                                        'notes': '; '.join(notes_parts) if notes_parts else None,
                                        'is_cover': is_cover,
                                        'original_artist': original_artist,
                                        'with_artist': with_artist,
                                    })
                                    order += 1

                            if songs_data:
                                source = 'Setlist.fm'

                    time.sleep(0.5)  # Be nice to Setlist.fm

                except Exception as e:
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - Setlist.fm error: {e}')

            # Fallback: Try Concert Archives
            if not songs_data and artist:
                try:
                    venue = show.venue
                    venue_name = venue.name if venue else None
                    ca_songs = fetch_setlist_from_concert_archives(
                        artist.name, venue_name, show.date, delay=3.0
                    )
                    if ca_songs:
                        songs_data = ca_songs
                        source = 'Concert Archives'
                except Exception as e:
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - Concert Archives error: {e}')

            # Store songs if we got any
            if songs_data:
                try:
                    for song_data in songs_data:
                        setlist_song = SetlistSong(
                            show_id=show.id,
                            title=song_data['title'],
                            order=song_data.get('order', 1),
                            notes=song_data.get('notes'),
                            is_cover=song_data.get('is_cover', False),
                            original_artist=song_data.get('original_artist'),
                            with_artist=song_data.get('with_artist'),
                        )
                        db.session.add(setlist_song)
                    db.session.commit()
                    if source == 'Concert Archives':
                        success_ca += 1
                    else:
                        success += 1
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - {len(songs_data)} songs added ({source})')
                except Exception as e:
                    db.session.rollback()
                    errors += 1
                    print(f'  [{i+1}/{len(shows_to_process)}] {label} - DB error: {e}')
            else:
                no_setlist += 1
                print(f'  [{i+1}/{len(shows_to_process)}] {label} - no setlist found')

        print(f'\nSetlist results: {success} from Setlist.fm, {success_ca} from Concert Archives, {no_setlist} not found, {errors} errors')
        print(f'Total shows with setlists now: {len(shows_with_setlist) + success + success_ca}/{len(all_shows)}')


def backfill_metadata(app):
    """Step 3: Backfill duration and songwriter from MusicBrainz for songs missing them."""
    with app.app_context():
        # Find all songs missing duration, grouped by show
        songs_missing = SetlistSong.query.filter(
            SetlistSong.duration.is_(None)
        ).join(Show, SetlistSong.show_id == Show.id).filter(
            Show.user_id == TARGET_USER_ID
        ).order_by(SetlistSong.show_id, SetlistSong.order).all()

        if not songs_missing:
            print('\n=== Step 3: All songs already have duration metadata ===\n')
            return

        # Group by show for caching
        from collections import defaultdict
        by_show = defaultdict(list)
        for s in songs_missing:
            by_show[s.show_id].append(s)

        print(f'\n=== Step 3: Backfilling metadata for {len(songs_missing)} songs across {len(by_show)} shows ===\n')

        total_updated = 0
        for show_id, songs in by_show.items():
            show = db.session.get(Show, show_id)
            artist = show.artist if show else None
            mbid = artist.mbid if artist else None
            artist_name = artist.name if artist else None
            label = f'{show.date} {artist_name or "?"}'

            # Build cache from existing songs by the same artist
            cached = {}
            if show.artist_id:
                existing = db.session.query(SetlistSong).join(
                    Show, SetlistSong.show_id == Show.id
                ).filter(
                    Show.artist_id == show.artist_id,
                    SetlistSong.show_id != show_id,
                    SetlistSong.duration.isnot(None)
                ).all()
                for s in existing:
                    cached[s.title.lower()] = s

            updated = 0
            for song in songs:
                cache_key = song.title.lower()
                if cache_key in cached:
                    hit = cached[cache_key]
                    song.duration = hit.duration
                    if hit.songwriter and not song.is_cover:
                        song.songwriter = hit.songwriter
                    updated += 1
                    continue

                try:
                    resp = requests.get(
                        'https://musicbrainz.org/ws/2/recording/',
                        headers=MB_HEADERS,
                        params={'query': song.title, 'fmt': 'json', 'limit': 20},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        recordings = resp.json().get('recordings', [])
                        best = None
                        # Prefer: same artist by MBID
                        if mbid:
                            for r in recordings:
                                if not r.get('length'):
                                    continue
                                r_ids = [a.get('artist', {}).get('id', '') for a in r.get('artist-credit', [])]
                                if mbid in r_ids:
                                    best = r
                                    break
                        # Fallback: same artist by name
                        if not best and artist_name:
                            for r in recordings:
                                if not r.get('length'):
                                    continue
                                r_names = [a.get('name', '').lower() for a in r.get('artist-credit', [])]
                                if artist_name.lower() in r_names:
                                    best = r
                                    break
                        # Last resort: exact title match
                        if not best:
                            for r in recordings:
                                if not r.get('length'):
                                    continue
                                if r.get('title', '').lower() == song.title.lower():
                                    best = r
                                    break
                        if best:
                            ms = best['length']
                            song.duration = f'{ms // 60000}:{(ms % 60000) // 1000:02d}'
                            updated += 1

                            # Songwriter lookup
                            if not song.is_cover and not song.songwriter:
                                time.sleep(1)
                                try:
                                    wr = requests.get(
                                        f'https://musicbrainz.org/ws/2/recording/{best["id"]}',
                                        headers=MB_HEADERS,
                                        params={'inc': 'work-rels+work-level-rels+artist-rels', 'fmt': 'json'},
                                        timeout=5
                                    )
                                    if wr.status_code == 200:
                                        composers, lyricists = [], []
                                        for rel in wr.json().get('relations', []):
                                            if rel.get('type') == 'performance':
                                                for wrel in rel.get('work', {}).get('relations', []):
                                                    name = wrel.get('artist', {}).get('name', '')
                                                    if wrel.get('type') == 'composer' and name not in composers:
                                                        composers.append(name)
                                                    elif wrel.get('type') == 'lyricist' and name not in lyricists:
                                                        lyricists.append(name)
                                        parts = []
                                        if composers:
                                            parts.append(', '.join(composers))
                                        if lyricists:
                                            parts.append(', '.join(lyricists))
                                        if parts:
                                            song.songwriter = ' / '.join(parts)
                                except Exception:
                                    pass
                    time.sleep(1)  # MusicBrainz rate limit
                except Exception:
                    continue

            if updated > 0:
                db.session.commit()
                total_updated += updated
            print(f'  {label} - {updated}/{len(songs)} songs enriched')

        print(f'\nMetadata backfill: {total_updated}/{len(songs_missing)} songs updated')


if __name__ == '__main__':
    app = create_app()
    lookup_mbids(app)
    fetch_setlists(app)
    backfill_metadata(app)
    print('\nDone!')
