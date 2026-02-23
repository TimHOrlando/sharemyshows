"""
Concert Archives (concertarchives.org) scraper for setlist data.
Used as a fallback when Setlist.fm returns no results.

Flow:
1. Search concert-search-engine with artist name + date
2. Extract concert page URL from results
3. Fetch concert page, extract numeric concert ID from script tag
4. Hit /concert_setlists/{id}?data[ajax_request]=true for setlist HTML
5. Parse <ol>/<li> structure into song dicts
"""
import re
import time
from datetime import date

import cloudscraper
from bs4 import BeautifulSoup


_scraper = None


def _get_scraper():
    """Lazily create a cloudscraper instance (reuses session across calls)."""
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True}
        )
    return _scraper


def _search_concert(artist_name, show_date):
    """
    Search Concert Archives for a concert matching artist + date.
    Returns the concert page path (e.g. '/concerts/phish--4681289') or None.
    """
    scraper = _get_scraper()

    # Format: "Artist Month Day Year" e.g. "Phish December 31 2023"
    date_query = show_date.strftime('%B %d %Y')
    search_query = f'{artist_name} {date_query}'

    print(f'[concert-archives] Searching: {search_query}')
    try:
        resp = scraper.get(
            'https://www.concertarchives.org/concert-search-engine',
            params={'search': search_query},
            timeout=20
        )
        if resp.status_code != 200:
            print(f'[concert-archives] Search returned status {resp.status_code}')
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.find_all('div', class_='new_concert_search_result')
        if not results:
            print('[concert-archives] No search results found')
            return None

        print(f'[concert-archives] Found {len(results)} search result(s)')

        # Format the target date for matching
        # Concert Archives shows dates like "Dec 31, 2023"
        target_date_str = show_date.strftime('%b %-d, %Y')
        artist_lower = artist_name.lower()

        for result in results:
            result_text = result.get_text(strip=True)

            # Check if date matches
            if target_date_str not in result_text:
                continue

            # Check if artist name appears in the result
            if artist_lower not in result_text.lower():
                continue

            # Extract the concert link
            link = result.find('a', href=re.compile(r'^/concerts/'))
            if link:
                href = link['href']
                print(f'[concert-archives] Matched: {href}')
                return href

        # If exact date match failed, take first result if it has the artist name
        for result in results:
            result_text = result.get_text(strip=True)
            if artist_lower not in result_text.lower():
                continue
            link = result.find('a', href=re.compile(r'^/concerts/'))
            if link:
                href = link['href']
                print(f'[concert-archives] Fuzzy match (first artist result): {href}')
                return href

        print('[concert-archives] No matching result found')
        return None

    except Exception as e:
        print(f'[concert-archives] Search error: {e}')
        return None


def _get_concert_setlist_id(concert_path):
    """
    Given a concert page path, extract the numeric concert ID for the setlist AJAX call.
    For --{id} URLs, extracts directly. Otherwise fetches the page and parses the script.
    """
    # Try extracting numeric ID from URL pattern like /concerts/phish--4681289
    m = re.search(r'--(\d+)$', concert_path)
    if m:
        return m.group(1)

    # For UUID or slug-only URLs, fetch the page and extract from the script tag
    scraper = _get_scraper()
    try:
        url = f'https://www.concertarchives.org{concert_path}'
        print(f'[concert-archives] Fetching concert page to extract setlist ID: {url}')
        resp = scraper.get(url, timeout=20)
        if resp.status_code != 200:
            print(f'[concert-archives] Concert page returned status {resp.status_code}')
            return None

        m = re.search(r'concert_setlists/(\d+)', resp.text)
        if m:
            return m.group(1)

        print('[concert-archives] Could not find setlist ID in concert page')
        return None
    except Exception as e:
        print(f'[concert-archives] Error fetching concert page: {e}')
        return None


def _fetch_and_parse_setlist(concert_id, artist_name=None):
    """
    Fetch the setlist AJAX endpoint and parse songs from HTML.
    When artist_name is provided, filters to only that artist's setlist
    (multi-band concerts have separate wrappers per band).
    Returns list of song dicts or None.
    """
    scraper = _get_scraper()
    url = f'https://www.concertarchives.org/concert_setlists/{concert_id}'

    try:
        resp = scraper.get(url, params={'data[ajax_request]': 'true'}, timeout=20)
        if resp.status_code != 200:
            print(f'[concert-archives] Setlist endpoint returned status {resp.status_code}')
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Structure: <dl class="setlists-container">
        #   <div class="setlists-wrapper">
        #     <dt><strong>Artist setlist:</strong>...</dt>
        #     <dd><ol><li>Song 1</li>...</ol></dd>
        #   </div>
        # </dl>

        wrappers = soup.find_all('div', class_='setlists-wrapper')
        if not wrappers:
            # Fallback: just find all <ol> lists
            wrappers = [soup]

        # Parse all wrappers, grouping by band label
        all_band_songs = []
        for wrapper in wrappers:
            dt = wrapper.find('dt')
            set_label = ''
            if dt:
                strong = dt.find('strong')
                if strong:
                    set_label = strong.get_text(strip=True).rstrip(':')

            ol = wrapper.find('ol')
            if not ol:
                continue

            band_songs = []
            for li in ol.find_all('li', recursive=False):
                song_name = li.get_text(strip=True)
                if not song_name or len(song_name) > 200:
                    continue
                band_songs.append((song_name, set_label))

            if band_songs:
                all_band_songs.append((set_label, band_songs))

        if not all_band_songs:
            return None

        # Filter to the requested artist's setlist when band labels are present
        if artist_name:
            artist_lower = artist_name.lower()
            # Check if any wrapper labels contain band names
            labeled = [(label, songs) for label, songs in all_band_songs if label]
            if labeled:
                matched = [(label, songs) for label, songs in all_band_songs
                           if artist_lower in label.lower()]
                if matched:
                    all_band_songs = matched
                    print(f'[concert-archives] Filtered to {len(matched)} matching setlist(s) for "{artist_name}"')
                else:
                    # All wrappers have labels but none match our artist — wrong band's setlist
                    print(f'[concert-archives] No setlist matched artist "{artist_name}", skipping')
                    return None

        # Flatten into song dicts
        songs = []
        order = 1
        for set_label, band_songs in all_band_songs:
            for song_name, label in band_songs:
                songs.append({
                    'title': song_name,
                    'order': order,
                    'notes': label if label else None,
                    'is_cover': False,
                    'original_artist': None,
                    'with_artist': None,
                })
                order += 1

        return songs if songs else None

    except Exception as e:
        print(f'[concert-archives] Error parsing setlist: {e}')
        return None


def fetch_setlist_from_concert_archives(artist_name, venue_name, show_date, delay=2.0):
    """
    Attempt to find and parse a setlist from Concert Archives.
    This is a fallback source, called only when Setlist.fm returns nothing.

    Args:
        artist_name: Name of the artist/band
        venue_name: Name of the venue (used for logging, not search)
        show_date: Python date object
        delay: Seconds between requests (rate limiting)

    Returns:
        List of song dicts compatible with SetlistSong fields, or None on failure.
        Each dict: {'title', 'order', 'notes', 'is_cover', 'original_artist', 'with_artist'}
    """
    try:
        # Step 1: Search for the concert
        concert_path = _search_concert(artist_name, show_date)
        if not concert_path:
            return None

        time.sleep(delay)

        # Step 2: Get the numeric concert ID for the setlist AJAX call
        concert_id = _get_concert_setlist_id(concert_path)
        if not concert_id:
            return None

        # If we had to fetch the concert page, add another delay
        if not re.search(r'--(\d+)$', concert_path):
            time.sleep(delay)

        # Step 3: Fetch and parse the setlist
        songs = _fetch_and_parse_setlist(concert_id, artist_name=artist_name)

        if songs:
            print(f'[concert-archives] Parsed {len(songs)} songs for {artist_name} on {show_date}')
        else:
            print(f'[concert-archives] No setlist data found for {artist_name} on {show_date}')

        return songs

    except Exception as e:
        print(f'[concert-archives] Unexpected error: {e}')
        return None
