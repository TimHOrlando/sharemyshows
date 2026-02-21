"""
Backfill song durations and songwriters from MusicBrainz for all SetlistSongs.
Uses in-memory cache + DB cache to minimize API calls.
Rate limit: 1 req/sec for MusicBrainz.
"""
import os
import sys
import time
import requests

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db, Show, Artist, SetlistSong

MB_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'ShareMyShows/1.0 (tim.h.orlando@gmail.com)'
}

# Cache: (artist_mbid, song_title_lower) -> {duration, songwriter}
cache = {}


def lookup_recording(title, artist_mbid, artist_name):
    """Search MusicBrainz for a recording and return duration + songwriter."""
    try:
        resp = requests.get(
            'https://musicbrainz.org/ws/2/recording/',
            headers=MB_HEADERS,
            params={'query': title, 'fmt': 'json', 'limit': 20},
            timeout=10
        )
        if resp.status_code != 200:
            return None, None

        recordings = resp.json().get('recordings', [])
        best = None

        # Tier 1: match by artist MBID
        if artist_mbid:
            for r in recordings:
                if not r.get('length'):
                    continue
                r_artist_ids = [a.get('artist', {}).get('id', '') for a in r.get('artist-credit', [])]
                if artist_mbid in r_artist_ids:
                    best = r
                    break

        # Tier 2: match by artist name
        if not best and artist_name:
            for r in recordings:
                if not r.get('length'):
                    continue
                r_names = [a.get('name', '').lower() for a in r.get('artist-credit', [])]
                if artist_name.lower() in r_names:
                    best = r
                    break

        # Tier 3: exact title match with any duration
        if not best:
            for r in recordings:
                if not r.get('length'):
                    continue
                if r.get('title', '').lower() == title.lower():
                    best = r
                    break

        if not best:
            return None, None

        # Format duration
        ms = best['length']
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        duration = f'{minutes}:{seconds:02d}'

        # Look up songwriter
        songwriter = None
        time.sleep(1)
        try:
            wr_resp = requests.get(
                f'https://musicbrainz.org/ws/2/recording/{best["id"]}',
                headers=MB_HEADERS,
                params={'inc': 'work-rels+work-level-rels+artist-rels', 'fmt': 'json'},
                timeout=10
            )
            if wr_resp.status_code == 200:
                composers = []
                lyricists = []
                for rel in wr_resp.json().get('relations', []):
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
                    songwriter = ' / '.join(parts)
        except Exception:
            pass

        return duration, songwriter

    except Exception as e:
        print(f'    ERROR looking up "{title}": {e}')
        return None, None


def backfill():
    app = create_app()
    with app.app_context():
        # Get all songs that need duration
        songs = SetlistSong.query.filter(
            (SetlistSong.duration.is_(None)) | (SetlistSong.duration == '')
        ).all()

        if not songs:
            print('All songs already have durations!')
            return

        # Pre-populate cache from songs that already have durations
        cached_songs = SetlistSong.query.filter(SetlistSong.duration.isnot(None), SetlistSong.duration != '').all()
        for s in cached_songs:
            show = Show.query.get(s.show_id)
            if show and show.artist:
                key = (show.artist.mbid or '', s.title.lower())
                cache[key] = {'duration': s.duration, 'songwriter': s.songwriter}
        print(f'Pre-loaded {len(cache)} songs from DB cache')

        # Group songs by show for logging
        show_ids = set(s.show_id for s in songs)
        print(f'Songs needing duration: {len(songs)} across {len(show_ids)} shows\n')

        updated = 0
        cache_hits = 0
        api_calls = 0
        not_found = 0

        for i, song in enumerate(songs):
            show = Show.query.get(song.show_id)
            artist = show.artist if show else None
            artist_mbid = artist.mbid if artist else None
            artist_name = artist.name if artist else None

            key = (artist_mbid or '', song.title.lower())

            # Check cache
            if key in cache:
                hit = cache[key]
                song.duration = hit['duration']
                if hit.get('songwriter') and not song.is_cover and not song.songwriter:
                    song.songwriter = hit['songwriter']
                cache_hits += 1
                updated += 1
                if (i + 1) % 50 == 0:
                    print(f'  [{i+1}/{len(songs)}] Progress... ({cache_hits} cache hits, {api_calls} API calls, {not_found} not found)')
                continue

            # API lookup
            duration, songwriter = lookup_recording(song.title, artist_mbid, artist_name)
            api_calls += 1

            if duration:
                song.duration = duration
                if songwriter and not song.is_cover and not song.songwriter:
                    song.songwriter = songwriter
                cache[key] = {'duration': duration, 'songwriter': songwriter}
                updated += 1
                print(f'  [{i+1}/{len(songs)}] "{song.title}" ({artist_name}) -> {duration}')
            else:
                cache[key] = {'duration': None, 'songwriter': None}
                not_found += 1
                print(f'  [{i+1}/{len(songs)}] "{song.title}" ({artist_name}) -> not found')

            # Commit every 25 songs
            if (i + 1) % 25 == 0:
                db.session.commit()
                print(f'  --- Committed {i+1}/{len(songs)} ({updated} updated, {cache_hits} cache, {api_calls} API, {not_found} not found) ---')

            time.sleep(1)  # MusicBrainz rate limit

        db.session.commit()
        print(f'\nDone! {updated} songs updated, {cache_hits} from cache, {api_calls} API calls, {not_found} not found')
        print(f'Total songs with duration: {SetlistSong.query.filter(SetlistSong.duration.isnot(None), SetlistSong.duration != "").count()}/{SetlistSong.query.count()}')


if __name__ == '__main__':
    backfill()
