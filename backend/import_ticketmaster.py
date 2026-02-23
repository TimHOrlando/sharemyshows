"""
Import Ticketmaster shows that aren't already in the database.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db, Artist, Venue, Show

TARGET_USER_ID = 1

# Parsed from Ticketmaster list. Co-headliners split into separate entries.
# Duplicate Joe Walsh/Bad Company order removed (same show, two orders).
# (artist_name, date, venue_name, city, state)
TICKETMASTER_SHOWS = [
    ('Dead & Company', '2025-03-27', 'Sphere', 'Las Vegas', 'NV'),
    ('Billy Strings', '2024-04-19', 'St. Augustine Amphitheatre', 'St. Augustine', 'FL'),
    ('Billy Strings', '2022-11-16', 'Virginia Credit Union LIVE!', 'Richmond', 'VA'),
    ('Billy Strings', '2022-07-23', 'Iroquois Amphitheater', 'Louisville', 'KY'),
    ('Dead & Company', '2021-10-07', 'MIDFLORIDA Credit Union Amphitheatre', 'Tampa', 'FL'),
    ('Dark Star Orchestra', '2019-04-01', 'House of Blues Orlando', 'Lake Buena Vista', 'FL'),
    ('Bob Weir and Wolf Bros', '2018-11-16', 'Boch Center Wang Theatre', 'Boston', 'MA'),
    ('Bob Weir and Wolf Bros', '2018-11-15', 'Boch Center Wang Theatre', 'Boston', 'MA'),
    ('Dead & Company', '2018-05-30', 'Xfinity Center', 'Mansfield', 'MA'),
    ('Dead & Company', '2018-03-27', 'Kia Center', 'Orlando', 'FL'),
    ('Dead & Company', '2018-02-26', 'Amerant Bank Arena', 'Sunrise', 'FL'),
    ('Prophets of Rage', '2016-10-01', 'MIDFLORIDA Credit Union Amphitheatre', 'Tampa', 'FL'),
    ('Joe Walsh', '2016-05-28', 'MIDFLORIDA Credit Union Amphitheatre', 'Tampa', 'FL'),
    ('Bad Company', '2016-05-28', 'MIDFLORIDA Credit Union Amphitheatre', 'Tampa', 'FL'),
    ('Ratdog', '2014-08-24', 'St. Augustine Amphitheatre', 'St. Augustine', 'FL'),
    ('Nine Inch Nails', '2014-08-11', 'MIDFLORIDA Credit Union Amphitheatre', 'Tampa', 'FL'),
    ('Soundgarden', '2014-08-11', 'MIDFLORIDA Credit Union Amphitheatre', 'Tampa', 'FL'),
    ('The Who', '2012-11-03', 'Kia Center', 'Orlando', 'FL'),
    ('George Clinton & Parliament Funkadelic', '2012-10-27', 'House of Blues Orlando', 'Lake Buena Vista', 'FL'),
    ("Jane's Addiction", '2012-05-15', 'House of Blues Orlando', 'Lake Buena Vista', 'FL'),
    ('Radiohead', '2012-02-29', 'Benchmark International Arena', 'Tampa', 'FL'),
]


def parse_date(s):
    y, m, d = s.split('-')
    return date(int(y), int(m), int(d))


def import_data():
    app = create_app()
    with app.app_context():
        # Build lookups by normalized name
        existing_artists = {}
        for a in Artist.query.all():
            existing_artists[a.name.lower().strip()] = a

        existing_venues = {}
        for v in Venue.query.all():
            existing_venues[v.name.lower().strip()] = v

        # Also match partial venue names for known aliases
        venue_aliases = {
            'midflorida credit union amphitheatre': [
                'midflorida credit union amphitheatre, florida state fairgrounds',
                'midflorida credit union amphitheatre',
            ],
            'st. augustine amphitheatre': [
                'st. augustine amphitheatre',
            ],
        }

        # Build existing shows set for dedup
        existing_shows = set()
        for s in Show.query.filter_by(user_id=TARGET_USER_ID).all():
            existing_shows.add((s.artist_id, s.venue_id, s.date))

        shows_created = 0
        shows_skipped = 0

        for artist_name, date_str, venue_name, city, state in TICKETMASTER_SHOWS:
            show_date = parse_date(date_str)

            # Find or create artist
            artist_key = artist_name.lower().strip()
            artist = existing_artists.get(artist_key)
            if not artist:
                artist = Artist(name=artist_name)
                db.session.add(artist)
                db.session.flush()
                existing_artists[artist_key] = artist
                print(f'  Created artist: {artist_name}')

            # Find or create venue (check aliases)
            venue_key = venue_name.lower().strip()
            venue = existing_venues.get(venue_key)
            if not venue:
                # Check aliases
                for alias_key, alias_list in venue_aliases.items():
                    if venue_key == alias_key:
                        for alias in alias_list:
                            venue = existing_venues.get(alias)
                            if venue:
                                break
                        break
            if not venue:
                venue = Venue(name=venue_name, city=city, state=state, country='US')
                db.session.add(venue)
                db.session.flush()
                existing_venues[venue_key] = venue
                print(f'  Created venue: {venue_name} ({city}, {state})')

            # Check for duplicate
            dedup_key = (artist.id, venue.id, show_date)
            if dedup_key in existing_shows:
                print(f'  SKIP (exists): {show_date} {artist_name} @ {venue.name}')
                shows_skipped += 1
                continue

            show = Show(
                user_id=TARGET_USER_ID,
                artist_id=artist.id,
                venue_id=venue.id,
                date=show_date,
            )
            db.session.add(show)
            existing_shows.add(dedup_key)
            shows_created += 1
            print(f'  ADDED: {show_date} {artist_name} @ {venue.name}')

        db.session.commit()
        print(f'\nResults: {shows_created} added, {shows_skipped} skipped')
        print(f'Total shows now: {Show.query.filter_by(user_id=TARGET_USER_ID).count()}')


if __name__ == '__main__':
    import_data()
