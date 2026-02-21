"""
Import shows from the old share_my_shows MySQL dump into the current SQLite database.
Maps old schema (artists_id, venues_id, shows_id) to new schema (id-based).
Deduplicates artists and venues by name.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import db, Artist, Venue, Show

# Target user for all imported shows
TARGET_USER_ID = 1

# --- Old data extracted from the SQL dump ---

OLD_ARTISTS = {
    1: 'Lover Boy', 2: 'The Black Crowes', 3: 'Ozzy Osbourne', 4: 'The Beach Boys',
    5: 'Van Halen', 6: 'Iron Maiden', 7: 'REO Speedwagon', 8: 'Grateful Dead',
    9: 'Rossington Collins Band', 10: 'Blue Oyster Cult', 11: 'Foghat',
    12: 'U2', 13: 'Billy Squire', 14: 'Nazareth', 15: 'Tom Petty and the Heartbreakers',
    16: 'Def Leppard', 17: 'Bon Jovi', 18: 'Alice Cooper', 19: 'Duran Duran',
    20: 'Bob Seger', 21: 'Sammy Hagar', 22: 'Judas Priest', 23: 'Motley Crue',
    24: 'Bryan Adams', 25: 'Yes', 26: 'Ted Nugent', 27: 'Whitesnake',
    28: 'Skid Row', 29: 'Aerosmith', 30: 'AC/DC', 31: 'Alice In Chains',
    32: 'Kiss', 33: 'ZZ Top', 34: 'Rush', 35: 'Robert Plant & Jimmy Page',
    36: 'Furthur', 37: 'Ratdog', 38: 'The Dead', 39: 'Galactic',
    40: 'Metallica', 41: 'Smashing Pumpkins', 42: 'Pearl Jam',
    43: 'The Smashing Pumpkins', 44: 'Red Hot Chili Peppers',
    46: 'Soul Asylum', 47: 'Screaming Trees', 48: 'Spin Doctors',
    49: 'Dokken', 50: 'Kingdom Come', 51: 'Scorpions', 52: 'Pink Floyd',
    53: 'Kid Rock', 54: 'Buddy Guy', 55: 'Allman Brothers Band',
    56: 'Wide Spread Panic', 57: "Les Claypool's Duo de Twang",
    58: 'Megadeth', 59: 'Tool', 60: 'Nine Inch Nails', 61: 'Chris Cornell',
    62: 'Incubus', 63: 'Sting and the Royal Philharmonic Concert Orchestra',
    64: 'J. Geils Band', 65: 'Queens of the Stoneage', 66: 'Audioslave',
    67: 'Seether', 68: 'Erykah Badu', 69: 'Anthony Hamilton',
    70: 'Bela Fleck and the Flecktones', 71: 'Radiohead', 72: 'Sade',
    73: 'Marilyn Manson',
}

OLD_VENUES = {
    0:  ('Freedom Hall, Kentucky State Fair & Expo Center', 'Louisville', 'KY'),
    3:  ('Louisville Gardens', 'Louisville', 'KY'),
    4:  ('Cardinal Stadium', 'Louisville', 'KY'),
    6:  ('Deer Creek Music Center', 'Noblesville', 'IN'),
    7:  ('Buckeye Lake Music Center', 'Thornville', 'OH'),
    8:  ('Rupp Arena', 'Lexington', 'KY'),
    9:  ('Pyramid Arena', 'Memphis', 'TN'),
    10: ('Hard Rock Live Orlando', 'Lake Buena Vista', 'FL'),
    11: ('UCF Arena', 'Orlando', 'FL'),
    12: ('St. Augustine Amphitheatre', 'St. Augustine', 'FL'),
    14: ('Red Rocks Amphitheatre', 'Morrison', 'CO'),
    15: ('House of Blues Orlando', 'Lake Buena Vista', 'FL'),
    16: ('Greensboro Coliseum', 'Greensboro', 'NC'),
    17: ('St. Pete Times Forum', 'Tampa', 'FL'),
    18: ('Hoosier Dome', 'Indianapolis', 'IN'),
    19: ('Tewligans Bar', 'Louisville', 'KY'),
    20: ('Silver Spurs Arena', 'Kissimmee', 'FL'),
    21: ('Amway Center', 'Orlando', 'FL'),
    22: ('World Music Theater', 'Tinley Park', 'IL'),
    24: ('Citrus Bowl', 'Orlando', 'FL'),
    25: ('Spirit of the Suwannee Music Park', 'Live Oak', 'FL'),
    26: ('The Palace Theatre', 'Louisville', 'KY'),
    27: ('TD Waterhouse Centre', 'Orlando', 'FL'),
    28: ('Midflorida Credit Union Amphitheatre, Florida State Fairgrounds', 'Tampa', 'FL'),
}

# (users_id, artists_id, shows_id, venues_id, shows_date)
OLD_SHOWS = [
    (1, 1, 18, 0, '1986-08-11'), (1, 2, 19, 3, '1993-04-07'),
    (1, 3, 20, 4, '1984-05-25'), (1, 4, 21, 4, '1980-08-10'),
    (1, 5, 22, 0, '1982-07-30'), (1, 6, 23, 0, '1983-08-02'),
    (1, 7, 24, 0, '1984-12-28'), (1, 8, 25, 6, '1990-07-19'),
    (1, 8, 26, 6, '1990-07-18'), (1, 8, 27, 6, '1989-07-15'),
    (1, 8, 28, 7, '1993-06-11'), (1, 8, 29, 7, '1992-07-01'),
    (1, 8, 31, 7, '1991-06-09'), (1, 8, 32, 0, '1989-04-09'),
    (1, 8, 33, 0, '1993-06-15'), (1, 9, 34, 3, '1988-08-23'),
    (1, 10, 35, 3, '1981-10-25'), (1, 11, 36, 3, '1981-10-25'),
    (1, 12, 37, 3, '1982-03-13'), (1, 13, 38, 3, '1982-11-10'),
    (1, 14, 39, 3, '1982-10-10'), (1, 15, 40, 3, '1983-02-15'),
    (1, 16, 41, 3, '1988-01-29'), (1, 17, 42, 3, '1987-05-22'),
    (1, 18, 43, 3, '1987-12-12'), (1, 19, 44, 3, '1987-07-10'),
    (1, 20, 45, 0, '1980-07-13'), (1, 21, 46, 0, '1983-06-05'),
    (1, 22, 48, 0, '1984-04-14'), (1, 23, 49, 0, '1987-08-21'),
    (1, 23, 50, 0, '1985-08-25'), (1, 24, 52, 0, '1987-07-14'),
    (1, 25, 53, 0, '1987-11-22'), (1, 26, 54, 0, '1987-12-29'),
    (1, 27, 55, 0, '1988-02-14'), (1, 28, 56, 0, '1990-01-27'),
    (1, 29, 57, 0, '1990-03-27'), (1, 30, 59, 0, '1988-05-24'),
    (1, 31, 60, 0, '1996-06-30'), (1, 32, 61, 0, '1996-06-30'),
    (1, 33, 63, 8, '1982-01-26'), (1, 34, 64, 8, '1984-10-21'),
    (1, 35, 65, 9, '1995-03-04'), (1, 36, 66, 10, '2010-02-06'),
    (1, 36, 67, 11, '2011-04-05'), (1, 36, 68, 12, '2011-07-30'),
    (1, 36, 69, 25, '2012-04-20'), (1, 36, 70, 25, '2012-04-21'),
    (1, 36, 71, 14, '2011-09-30'), (1, 36, 72, 14, '2011-10-01'),
    (1, 36, 73, 14, '2011-10-02'), (1, 37, 74, 15, '2007-11-16'),
    (1, 37, 75, 10, '2008-11-19'), (1, 38, 76, 16, '2009-04-12'),
    (1, 38, 77, 17, '2003-07-30'), (1, 39, 78, 15, '2011-01-21'),
    (1, 40, 79, 18, '1988-07-06'), (1, 41, 82, 19, '1991-10-08'),
    (1, 42, 83, 20, '2004-10-08'), (1, 43, 84, 15, '2010-07-19'),
    (1, 44, 85, 21, '2012-03-31'), (1, 72, 87, 21, '2011-07-17'),
    (1, 73, 88, 10, '2008-07-19'), (1, 46, 89, 22, '1993-07-25'),
    (1, 47, 90, 22, '1993-07-25'), (1, 48, 91, 22, '1993-07-25'),
    (1, 49, 92, 0, '1988-07-06'), (1, 50, 93, 18, '1988-07-06'),
    (1, 51, 94, 18, '1988-07-06'), (1, 5, 95, 18, '1988-07-06'),
    (1, 52, 96, 8, '1987-11-08'), (1, 52, 97, 18, '1994-06-14'),
    (1, 53, 98, 24, '2011-11-13'), (1, 54, 99, 24, '2011-11-13'),
    (1, 55, 100, 25, '2013-04-19'), (1, 55, 101, 25, '2013-04-20'),
    (1, 56, 102, 25, '2013-04-19'), (1, 56, 103, 25, '2013-04-20'),
    (1, 39, 104, 25, '2013-04-20'), (1, 57, 105, 25, '2013-04-19'),
    (1, 55, 106, 25, '2012-04-20'), (1, 55, 107, 25, '2012-04-21'),
    (1, 36, 108, 25, '2012-04-21'), (1, 36, 109, 25, '2012-04-20'),
    (1, 58, 110, 26, '1995-07-26'), (1, 8, 113, 0, '1993-06-16'),
    (1, 59, 114, 21, '2007-05-31'), (1, 2, 115, 15, '2010-08-22'),
    (1, 60, 116, 27, '2005-10-25'), (1, 61, 117, 10, '2012-05-13'),
    (1, 56, 118, 15, '1997-08-23'), (1, 62, 119, 12, '2011-08-18'),
    (1, 63, 120, 28, '2010-07-02'), (1, 64, 121, 3, '1982-03-13'),
    (1, 23, 122, 4, '1984-03-25'), (1, 5, 123, 0, '1984-02-09'),
    (1, 65, 124, 27, '2005-10-25'), (1, 66, 125, 10, '2005-10-19'),
    (1, 67, 126, 10, '2005-10-19'), (1, 68, 127, 15, '2007-08-19'),
    (1, 69, 128, 15, '2009-03-26'), (1, 8, 130, 6, '1992-06-29'),
    (1, 70, 131, 15, '2011-10-21'), (1, 71, 138, 0, '2008-05-06'),
]


def parse_date(s):
    y, m, d = s.split('-')
    return date(int(y), int(m), int(d))


def import_data():
    app = create_app()
    with app.app_context():
        # Build lookup of existing artists/venues by normalized name
        existing_artists = {}
        for a in Artist.query.all():
            existing_artists[a.name.lower().strip()] = a

        existing_venues = {}
        for v in Venue.query.all():
            existing_venues[v.name.lower().strip()] = v

        # Map old_artist_id -> new Artist object
        old_to_new_artist = {}
        artists_created = 0
        artists_reused = 0

        for old_id, name in OLD_ARTISTS.items():
            key = name.lower().strip()
            if key in existing_artists:
                old_to_new_artist[old_id] = existing_artists[key]
                artists_reused += 1
            else:
                artist = Artist(name=name)
                db.session.add(artist)
                db.session.flush()  # get the new ID
                existing_artists[key] = artist
                old_to_new_artist[old_id] = artist
                artists_created += 1

        print(f"Artists: {artists_created} created, {artists_reused} reused (already existed)")

        # Map old_venue_id -> new Venue object
        old_to_new_venue = {}
        venues_created = 0
        venues_reused = 0

        for old_id, (name, city, state) in OLD_VENUES.items():
            key = name.lower().strip()
            if key in existing_venues:
                venue = existing_venues[key]
                # Backfill city/state if missing
                if not venue.city and city:
                    venue.city = city
                if not venue.state and state:
                    venue.state = state
                old_to_new_venue[old_id] = venue
                venues_reused += 1
            else:
                venue = Venue(name=name, city=city, state=state, country='US')
                db.session.add(venue)
                db.session.flush()
                existing_venues[key] = venue
                old_to_new_venue[old_id] = venue
                venues_created += 1

        print(f"Venues: {venues_created} created, {venues_reused} reused (already existed)")

        # Build set of existing shows for dedup (user_id, artist_id, venue_id, date)
        existing_shows = set()
        for s in Show.query.filter_by(user_id=TARGET_USER_ID).all():
            existing_shows.add((s.artist_id, s.venue_id, s.date))

        # Import shows
        shows_created = 0
        shows_skipped = 0

        for _, old_artist_id, _, old_venue_id, date_str in OLD_SHOWS:
            artist = old_to_new_artist.get(old_artist_id)
            venue = old_to_new_venue.get(old_venue_id)

            if not artist:
                print(f"  WARNING: No artist mapping for old_id={old_artist_id}, skipping")
                shows_skipped += 1
                continue
            if not venue:
                print(f"  WARNING: No venue mapping for old_id={old_venue_id}, skipping")
                shows_skipped += 1
                continue

            show_date = parse_date(date_str)
            dedup_key = (artist.id, venue.id, show_date)

            if dedup_key in existing_shows:
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

        db.session.commit()
        print(f"Shows: {shows_created} created, {shows_skipped} skipped (duplicate or missing ref)")
        print(f"\nImport complete!")


if __name__ == '__main__':
    import_data()
