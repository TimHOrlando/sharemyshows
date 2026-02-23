"""
Shows API Routes - Flask-RESTX Implementation
Handles show CRUD operations, setlist management, and check-ins
"""
import os
import requests as http_requests
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.models import db, Show, Artist, Venue, SetlistSong, ShowCheckin, User, Photo, AudioRecording, VideoRecording, Comment, get_friend_ids
from app.utils.concert_archives import fetch_setlist_from_concert_archives


def _batch_counts(show_ids):
    """Pre-compute media/comment/song counts for a list of shows in 5 queries instead of 5*N."""
    if not show_ids:
        return {}
    photo_counts = dict(db.session.query(Photo.show_id, func.count(Photo.id))
        .filter(Photo.show_id.in_(show_ids)).group_by(Photo.show_id).all())
    audio_counts = dict(db.session.query(AudioRecording.show_id, func.count(AudioRecording.id))
        .filter(AudioRecording.show_id.in_(show_ids)).group_by(AudioRecording.show_id).all())
    video_counts = dict(db.session.query(VideoRecording.show_id, func.count(VideoRecording.id))
        .filter(VideoRecording.show_id.in_(show_ids)).group_by(VideoRecording.show_id).all())
    comment_counts = dict(db.session.query(Comment.show_id, func.count(Comment.id))
        .filter(Comment.show_id.in_(show_ids)).group_by(Comment.show_id).all())
    song_counts = dict(db.session.query(SetlistSong.show_id, func.count(SetlistSong.id))
        .filter(SetlistSong.show_id.in_(show_ids)).group_by(SetlistSong.show_id).all())
    return {
        sid: (photo_counts.get(sid, 0), audio_counts.get(sid, 0),
              video_counts.get(sid, 0), comment_counts.get(sid, 0),
              song_counts.get(sid, 0))
        for sid in show_ids
    }

# Create namespace
api = Namespace('shows', description='Show management operations')

# Models
artist_model = api.model('Artist', {
    'id': fields.Integer(description='Artist ID'),
    'name': fields.String(description='Artist name'),
    'musicbrainz_id': fields.String(description='MusicBrainz ID')
})

venue_model = api.model('Venue', {
    'id': fields.Integer(description='Venue ID'),
    'name': fields.String(description='Venue name'),
    'city': fields.String(description='City'),
    'state': fields.String(description='State'),
    'country': fields.String(description='Country'),
    'latitude': fields.Float(description='Latitude'),
    'longitude': fields.Float(description='Longitude')
})

setlist_song_model = api.model('SetlistSong', {
    'id': fields.Integer(description='Song ID'),
    'show_id': fields.Integer(description='Show ID'),
    'title': fields.String(description='Song title'),
    'song_name': fields.String(description='Song name (legacy)'),
    'order': fields.Integer(description='Order in setlist'),
    'notes': fields.String(description='Song notes'),
    'is_cover': fields.Boolean(description='Whether this is a cover song'),
    'original_artist': fields.String(description='Original artist if cover'),
    'duration': fields.String(description='Song duration (e.g. "5:23")'),
    'songwriter': fields.String(description='Songwriter(s)'),
    'with_artist': fields.String(description='Guest/featured artist'),
})

owner_model = api.model('Owner', {
    'id': fields.Integer(description='Owner user ID'),
    'username': fields.String(description='Owner username'),
})

show_model = api.model('Show', {
    'id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'owner': fields.Nested(owner_model, description='Show owner info'),
    'is_owner': fields.Boolean(description='Whether the current user owns this show'),
    'artist_id': fields.Integer(description='Artist ID'),
    'venue_id': fields.Integer(description='Venue ID'),
    'date': fields.Date(description='Show date'),
    'notes': fields.String(description='Notes'),
    'rating': fields.Integer(description='Rating 1-5'),
    'created_at': fields.DateTime(description='Created at'),
    'artist': fields.Nested(artist_model),
    'venue': fields.Nested(venue_model),
    'song_count': fields.Integer(description='Number of songs in setlist'),
    'photo_count': fields.Integer(description='Number of photos'),
    'audio_count': fields.Integer(description='Number of audio recordings'),
    'video_count': fields.Integer(description='Number of video recordings'),
    'comment_count': fields.Integer(description='Number of comments'),
    'setlist': fields.List(fields.Nested(setlist_song_model), description='Setlist songs'),
    'photos': fields.Raw(description='Photos'),
    'audio': fields.Raw(description='Audio recordings'),
    'videos': fields.Raw(description='Video recordings'),
    'comments': fields.Raw(description='Comments'),
})

show_create_model = api.model('ShowCreate', {
    'artist_name': fields.String(required=True, description='Artist name'),
    'artist_mbid': fields.String(required=False, description='MusicBrainz ID for setlist lookup'),
    'venue_name': fields.String(required=True, description='Venue name'),
    'date': fields.String(required=True, description='Show date (YYYY-MM-DD)'),
    'city': fields.String(required=False, description='City'),
    'state': fields.String(required=False, description='State'),
    'country': fields.String(required=False, description='Country'),
    'notes': fields.String(required=False, description='Notes'),
    'rating': fields.Integer(required=False, description='Rating 1-5')
})

show_update_model = api.model('ShowUpdate', {
    'notes': fields.String(required=False, description='Notes'),
    'rating': fields.Integer(required=False, description='Rating 1-5')
})

song_create_model = api.model('SongCreate', {
    'song_name': fields.String(required=True, description='Song name'),
    'order': fields.Integer(required=False, description='Order in setlist'),
    'is_cover': fields.Boolean(required=False, description='Whether this is a cover song'),
    'original_artist': fields.String(required=False, description='Original artist if cover'),
    'duration': fields.String(required=False, description='Song duration (e.g. "5:23")'),
    'songwriter': fields.String(required=False, description='Songwriter(s)'),
    'with_artist': fields.String(required=False, description='Guest/featured artist'),
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})

# Query parsers
show_list_parser = api.parser()
show_list_parser.add_argument('artist', type=str, location='args', help='Filter by artist name')
show_list_parser.add_argument('venue', type=str, location='args', help='Filter by venue name')
show_list_parser.add_argument('year', type=int, location='args', help='Filter by year')
show_list_parser.add_argument('filter', type=str, location='args', help='Filter: upcoming, past, or all (default)')
show_list_parser.add_argument('limit', type=int, location='args', help='Limit number of results')


@api.route('')
class ShowList(Resource):
    @api.doc('list_shows', security='jwt')
    @api.expect(show_list_parser)
    @api.marshal_list_with(show_model)
    @jwt_required()
    def get(self):
        """Get list of user's shows with optional filters"""
        current_user_id = int(get_jwt_identity())

        # Eager-load user, artist, venue to eliminate N+1
        query = Show.query.options(
            joinedload(Show.user),
            joinedload(Show.artist),
            joinedload(Show.venue),
        ).filter_by(user_id=current_user_id)

        # Apply filters
        artist_filter = request.args.get('artist')
        artist_id_filter = request.args.get('artist_id', type=int)
        venue_filter = request.args.get('venue')
        venue_id_filter = request.args.get('venue_id', type=int)
        year_filter = request.args.get('year', type=int)

        if artist_id_filter:
            query = query.filter(Show.artist_id == artist_id_filter)
        elif artist_filter:
            query = query.join(Artist).filter(Artist.name.ilike(f'%{artist_filter}%'))
        if venue_id_filter:
            query = query.filter(Show.venue_id == venue_id_filter)
        elif venue_filter:
            query = query.join(Venue).filter(Venue.name.ilike(f'%{venue_filter}%'))
        if year_filter:
            query = query.filter(db.extract('year', Show.date) == year_filter)

        # Upcoming/past filter
        time_filter = request.args.get('filter')
        today = date.today()
        if time_filter == 'upcoming':
            query = query.filter(Show.date >= today).order_by(Show.date.asc())
        elif time_filter == 'past':
            query = query.filter(Show.date < today).order_by(Show.date.desc())
        else:
            query = query.order_by(Show.date.desc())

        limit = request.args.get('limit', type=int)
        if limit:
            shows = query.limit(limit).all()
        else:
            shows = query.all()

        # Batch-compute counts (5 queries total instead of 5 per show)
        show_ids = [s.id for s in shows]
        counts_map = _batch_counts(show_ids)

        return [show.to_dict(viewer_id=current_user_id, counts=counts_map.get(show.id)) for show in shows]
    
    @api.doc('create_show', security='jwt')
    @api.expect(show_create_model)
    @api.marshal_with(show_model, code=201)
    @jwt_required()
    def post(self):
        """Create a new show"""
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Get or create artist
        artist_name = data.get('artist_name')
        artist_mbid = data.get('artist_mbid')
        artist = Artist.query.filter_by(name=artist_name).first()
        if not artist:
            artist = Artist(name=artist_name, mbid=artist_mbid)
            db.session.add(artist)
            db.session.flush()
        elif artist_mbid and not artist.mbid:
            artist.mbid = artist_mbid
            db.session.flush()
        
        # Get or create venue
        venue_name = data.get('venue_name')
        city = data.get('city', '')
        state = data.get('state', '')
        country = data.get('country', '')
        
        venue = Venue.query.filter_by(name=venue_name, city=city).first()
        if not venue:
            venue = Venue(
                name=venue_name,
                city=city,
                state=state,
                country=country
            )
            db.session.add(venue)
            db.session.flush()
        
        # Create show
        show_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        
        show = Show(
            user_id=current_user_id,
            artist_id=artist.id,
            venue_id=venue.id,
            date=show_date,
            notes=data.get('notes', ''),
            rating=data.get('rating')
        )
        
        db.session.add(show)
        db.session.commit()

        return show.to_dict(viewer_id=current_user_id), 201


# Feed endpoint - MUST be before /<int:show_id> to avoid route conflict
feed_parser = api.parser()
feed_parser.add_argument('page', type=int, location='args', default=1, help='Page number')
feed_parser.add_argument('per_page', type=int, location='args', default=20, help='Items per page')


@api.route('/feed')
class ShowFeed(Resource):
    @api.doc('get_feed', security='jwt')
    @api.expect(feed_parser)
    @jwt_required()
    def get(self):
        """Get shows from accepted friends, ordered by date desc"""
        current_user_id = int(get_jwt_identity())
        friend_ids = get_friend_ids(current_user_id)

        if not friend_ids:
            return {'shows': [], 'total': 0, 'page': 1, 'pages': 0}

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Show.query.options(
            joinedload(Show.user),
            joinedload(Show.artist),
            joinedload(Show.venue),
        ).filter(Show.user_id.in_(friend_ids)).order_by(Show.date.desc())
        total = query.count()
        shows = query.offset((page - 1) * per_page).limit(per_page).all()

        show_ids = [s.id for s in shows]
        counts_map = _batch_counts(show_ids)

        return {
            'shows': [s.to_dict(viewer_id=current_user_id, counts=counts_map.get(s.id)) for s in shows],
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page
        }


@api.route('/<int:show_id>')
class ShowDetail(Resource):
    @api.doc('get_show', security='jwt')
    @jwt_required()
    def get(self, show_id):
        """Get show details with setlist and photos"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)

        # Access control: owner or accepted friend
        if show.user_id != current_user_id:
            friend_ids = get_friend_ids(show.user_id)
            if current_user_id not in friend_ids:
                return {'error': 'Not authorized to view this show'}, 403

        return show.to_dict(include_details=True, viewer_id=current_user_id)
    
    @api.doc('update_show', security='jwt')
    @api.expect(show_update_model)
    @api.marshal_with(show_model)
    @jwt_required()
    def put(self, show_id):
        """Update show"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        if 'notes' in data:
            show.notes = data['notes']
        if 'rating' in data:
            show.rating = data['rating']

        db.session.commit()
        return show.to_dict(viewer_id=current_user_id)
    
    @api.doc('delete_show', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def delete(self, show_id):
        """Delete show"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        db.session.delete(show)
        db.session.commit()
        
        return {'message': 'Show deleted'}


@api.route('/<int:show_id>/setlist')
class ShowSetlist(Resource):
    @api.doc('get_setlist', security='jwt')
    @api.marshal_list_with(setlist_song_model)
    @jwt_required()
    def get(self, show_id):
        """Get show setlist"""
        show = Show.query.get_or_404(show_id)
        songs = SetlistSong.query.filter_by(show_id=show_id).order_by(SetlistSong.order).all()
        return [song.to_dict() for song in songs]
    
    @api.doc('add_song_to_setlist', security='jwt')
    @api.expect(song_create_model)
    @api.marshal_with(setlist_song_model, code=201)
    @jwt_required()
    def post(self, show_id):
        """Add song to setlist"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        
        # Get next order number if not specified
        if 'order' not in data or data['order'] is None:
            max_order = db.session.query(db.func.max(SetlistSong.order))\
                .filter_by(show_id=show_id).scalar() or 0
            order = max_order + 1
        else:
            order = data['order']
        
        song = SetlistSong(
            show_id=show_id,
            title=data.get('song_name', data.get('title', 'Untitled')),
            order=order,
            is_cover=data.get('is_cover', False),
            original_artist=data.get('original_artist'),
            duration=data.get('duration'),
            songwriter=data.get('songwriter'),
            with_artist=data.get('with_artist'),
        )

        db.session.add(song)
        db.session.commit()

        return song.to_dict(), 201


@api.route('/<int:show_id>/setlist/<int:song_id>')
class SetlistSongDetail(Resource):
    @api.doc('update_setlist_song', security='jwt')
    @api.expect(song_create_model)
    @api.marshal_with(setlist_song_model)
    @jwt_required()
    def put(self, show_id, song_id):
        """Update song in setlist"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        song = SetlistSong.query.get_or_404(song_id)
        data = request.get_json()
        
        if 'song_name' in data:
            song.title = data.get('song_name', data.get('title', song.title))
        if 'order' in data:
            song.order = data['order']
        if 'is_cover' in data:
            song.is_cover = data['is_cover']
        if 'original_artist' in data:
            song.original_artist = data['original_artist']
        if 'duration' in data:
            song.duration = data['duration']
        if 'songwriter' in data:
            song.songwriter = data['songwriter']
        if 'with_artist' in data:
            song.with_artist = data['with_artist']

        db.session.commit()
        return song.to_dict()
    
    @api.doc('delete_setlist_song', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def delete(self, show_id, song_id):
        """Remove song from setlist"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        song = SetlistSong.query.get_or_404(song_id)
        db.session.delete(song)
        db.session.commit()
        
        return {'message': 'Song removed from setlist'}


auto_setlist_model = api.model('AutoSetlist', {
    'mbid': fields.String(required=False, description='MusicBrainz ID (falls back to stored artist mbid)')
})

auto_setlist_response = api.model('AutoSetlistResponse', {
    'message': fields.String(description='Result message'),
    'songs_added': fields.Integer(description='Number of songs added'),
    'source': fields.String(description='Setlist.fm URL for attribution')
})


@api.route('/<int:show_id>/auto-setlist')
class ShowAutoSetlist(Resource):
    @api.doc('auto_populate_setlist', security='jwt')
    @api.expect(auto_setlist_model)
    @jwt_required()
    def post(self, show_id):
        """Auto-populate setlist from Setlist.fm for a past show"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)

        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403

        # Skip if songs already exist
        existing_count = SetlistSong.query.filter_by(show_id=show_id).count()
        if existing_count > 0:
            print(f'[auto-setlist] Show {show_id}: already has {existing_count} songs, skipping')
            return {'message': 'Setlist already populated', 'songs_added': 0, 'source': ''}, 200

        # Determine mbid
        data = request.get_json() or {}
        mbid = data.get('mbid') or (show.artist.mbid if show.artist else None)
        artist_name = show.artist.name if show.artist else None
        venue_name = show.venue.name if show.venue else None

        # Phase 1: Try Setlist.fm (requires MBID)
        songs_from_source = []
        source_url = ''

        if mbid:
            show_date_str = show.date.strftime('%d-%m-%Y')
            print(f'[auto-setlist] Show {show_id}: looking up mbid={mbid} date={show_date_str}')

            SETLISTFM_API_KEY = os.getenv('SETLISTFM_API_KEY')
            if SETLISTFM_API_KEY:
                try:
                    headers = {
                        'Accept': 'application/json',
                        'x-api-key': SETLISTFM_API_KEY
                    }
                    response = http_requests.get(
                        'https://api.setlist.fm/rest/1.0/search/setlists',
                        headers=headers,
                        params={'artistMbid': mbid, 'date': show_date_str},
                        timeout=10
                    )

                    print(f'[auto-setlist] Show {show_id}: Setlist.fm status={response.status_code}')
                    if response.status_code == 200:
                        result = response.json()
                        setlists = result.get('setlist', [])
                        print(f'[auto-setlist] Show {show_id}: found {len(setlists)} setlist(s)')

                        if setlists:
                            setlist = setlists[0]
                            source_url = setlist.get('url', '')
                            sets_data = setlist.get('sets', {}).get('set', [])
                            print(f'[auto-setlist] Show {show_id}: setlist has {len(sets_data)} set(s), url={source_url}')

                            for set_item in sets_data:
                                set_name = set_item.get('name', '')
                                songs_in_set = set_item.get('song', [])
                                print(f'[auto-setlist] Show {show_id}: set "{set_name}" has {len(songs_in_set)} song(s)')
                                if songs_in_set:
                                    print(f'[auto-setlist] Show {show_id}: first song raw: {songs_in_set[0]}')
                                for song in songs_in_set:
                                    song_name = song.get('name', '')
                                    if not song_name:
                                        print(f'[auto-setlist] Show {show_id}: skipping song with empty name: {song}')
                                        continue

                                    notes_parts = []
                                    if set_name:
                                        notes_parts.append(set_name)
                                    if song.get('info'):
                                        notes_parts.append(song['info'])
                                    if song.get('tape'):
                                        notes_parts.append('(from tape)')

                                    cover_data = song.get('cover')
                                    is_cover = cover_data is not None
                                    original_artist = cover_data.get('name') if cover_data else None

                                    with_data = song.get('with')
                                    with_artist = with_data.get('name') if with_data else None

                                    songs_from_source.append({
                                        'title': song_name,
                                        'notes': '; '.join(notes_parts) if notes_parts else None,
                                        'is_cover': is_cover,
                                        'original_artist': original_artist,
                                        'with_artist': with_artist,
                                    })
                    else:
                        print(f'[auto-setlist] Show {show_id}: response body={response.text[:500]}')
                except Exception as e:
                    print(f'[auto-setlist] Show {show_id}: Setlist.fm error: {e}')
            else:
                print(f'[auto-setlist] Show {show_id}: SETLISTFM_API_KEY not configured')
        else:
            print(f'[auto-setlist] Show {show_id}: no MBID available, skipping Setlist.fm')

        # Phase 2: Fallback to Concert Archives if Setlist.fm returned nothing
        if not songs_from_source and artist_name:
            print(f'[auto-setlist] Show {show_id}: trying Concert Archives fallback...')
            try:
                ca_songs = fetch_setlist_from_concert_archives(artist_name, venue_name, show.date)
                if ca_songs:
                    songs_from_source = ca_songs
                    source_url = 'concertarchives.org'
                    print(f'[auto-setlist] Show {show_id}: Concert Archives returned {len(ca_songs)} songs')
                else:
                    print(f'[auto-setlist] Show {show_id}: Concert Archives returned no results')
            except Exception as e:
                print(f'[auto-setlist] Show {show_id}: Concert Archives error: {e}')

        if not songs_from_source:
            return {'message': 'No setlist found for this date', 'songs_added': 0, 'source': ''}, 200

        # Phase 3: Create SetlistSong records from collected data
        try:
            order = 1
            songs_added = 0
            for song_data in songs_from_source:
                setlist_song = SetlistSong(
                    show_id=show_id,
                    title=song_data['title'],
                    order=song_data.get('order', order),
                    notes=song_data.get('notes'),
                    is_cover=song_data.get('is_cover', False),
                    original_artist=song_data.get('original_artist'),
                    with_artist=song_data.get('with_artist'),
                )
                db.session.add(setlist_song)
                order += 1
                songs_added += 1

            print(f'[auto-setlist] Show {show_id}: committing {songs_added} songs')
            db.session.commit()
            print(f'[auto-setlist] Show {show_id}: committed successfully')

            # Backfill durations and songwriter from cache or MusicBrainz
            try:
                import time as _time
                artist_id = show.artist_id
                songs_to_update = SetlistSong.query.filter_by(show_id=show_id).all()

                # Build cache from existing songs by the same artist across all shows
                cached = {}
                if artist_id:
                    existing_songs = db.session.query(SetlistSong).join(
                        Show, SetlistSong.show_id == Show.id
                    ).filter(
                        Show.artist_id == artist_id,
                        SetlistSong.show_id != show_id,
                        SetlistSong.duration.isnot(None)
                    ).all()
                    for s in existing_songs:
                        cached[s.title.lower()] = s
                    if cached:
                        print(f'[auto-setlist] Show {show_id}: found {len(cached)} cached songs from previous shows')

                mb_headers = {'Accept': 'application/json', 'User-Agent': 'ShareMyShows/1.0'}
                updated = 0
                for song_record in songs_to_update:
                    # Check cache first
                    cache_key = song_record.title.lower()
                    if cache_key in cached:
                        hit = cached[cache_key]
                        song_record.duration = hit.duration
                        if hit.songwriter and not song_record.is_cover:
                            song_record.songwriter = hit.songwriter
                        updated += 1
                        print(f'[auto-setlist] Show {show_id}: cache hit for "{song_record.title}"')
                        continue

                    try:
                        # Broad search, then pick best match with duration
                        mb_resp = http_requests.get(
                            'https://musicbrainz.org/ws/2/recording/',
                            headers=mb_headers,
                            params={
                                'query': song_record.title,
                                'fmt': 'json',
                                'limit': 20
                            },
                            timeout=5
                        )
                        if mb_resp.status_code == 200:
                            recordings = mb_resp.json().get('recordings', [])
                            best = None
                            # Prefer: same artist (by MBID) with duration
                            if mbid:
                                for r in recordings:
                                    if not r.get('length'):
                                        continue
                                    r_artist_ids = [a.get('artist', {}).get('id', '') for a in r.get('artist-credit', [])]
                                    if mbid in r_artist_ids:
                                        best = r
                                        break
                            # Fallback: same artist by name with duration
                            if not best and artist_name:
                                for r in recordings:
                                    if not r.get('length'):
                                        continue
                                    r_names = [a.get('name', '').lower() for a in r.get('artist-credit', [])]
                                    if artist_name.lower() in r_names:
                                        best = r
                                        break
                            # Last resort: any exact title match with duration
                            if not best:
                                for r in recordings:
                                    if not r.get('length'):
                                        continue
                                    if r.get('title', '').lower() == song_record.title.lower():
                                        best = r
                                        break
                            if best:
                                ms = best['length']
                                minutes = ms // 60000
                                seconds = (ms % 60000) // 1000
                                song_record.duration = f'{minutes}:{seconds:02d}'
                                updated += 1

                                # Fetch songwriter from work relations
                                if not song_record.is_cover and not song_record.songwriter:
                                    _time.sleep(1)
                                    try:
                                        wr_resp = http_requests.get(
                                            f'https://musicbrainz.org/ws/2/recording/{best["id"]}',
                                            headers=mb_headers,
                                            params={'inc': 'work-rels+work-level-rels+artist-rels', 'fmt': 'json'},
                                            timeout=5
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
                                                song_record.songwriter = ' / '.join(parts)
                                    except Exception:
                                        pass
                        _time.sleep(1)  # MusicBrainz rate limit: 1 req/sec
                    except Exception:
                        continue
                if updated > 0:
                    db.session.commit()
                    print(f'[auto-setlist] Show {show_id}: backfilled {updated} song durations from MusicBrainz')
            except Exception as e:
                print(f'[auto-setlist] Show {show_id}: MusicBrainz duration lookup failed: {e}')

            source_label = 'Concert Archives' if source_url == 'concertarchives.org' else 'Setlist.fm'
            return {
                'message': f'Added {songs_added} songs from {source_label}',
                'songs_added': songs_added,
                'source': source_url
            }, 200

        except Exception as e:
            print(f'[auto-setlist] Show {show_id}: unexpected error: {e}')
            db.session.rollback()
            return {'message': 'Setlist auto-population failed', 'songs_added': 0, 'source': ''}, 200


@api.route('/<int:show_id>/checkin')
class ShowCheckinEndpoint(Resource):
    @api.doc('checkin_to_show', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def post(self, show_id):
        """Check in to a show"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        # Check if already checked in
        existing = ShowCheckin.query.filter_by(
            user_id=current_user_id,
            show_id=show_id
        ).first()
        
        if existing:
            return {'error': 'Already checked in'}, 400
        
        checkin = ShowCheckin(
            user_id=current_user_id,
            show_id=show_id,
            checked_in_at=datetime.utcnow()
        )
        
        db.session.add(checkin)
        db.session.commit()
        
        return {'message': 'Checked in successfully'}


@api.route('/<int:show_id>/checkout')
class ShowCheckoutEndpoint(Resource):
    @api.doc('checkout_from_show', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def post(self, show_id):
        """Check out from a show"""
        current_user_id = int(get_jwt_identity())
        
        checkin = ShowCheckin.query.filter_by(
            user_id=current_user_id,
            show_id=show_id
        ).first()
        
        if not checkin:
            return {'error': 'Not checked in'}, 400
        
        db.session.delete(checkin)
        db.session.commit()
        
        return {'message': 'Checked out successfully'}



@api.route('/<int:show_id>/presence')
class ShowPresence(Resource):
    @api.doc('get_show_presence', security='jwt')
    @jwt_required()
    def get(self, show_id):
        """Get users currently at this show"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        # Get active checkins with location
        checkins = ShowCheckin.query.filter_by(
            show_id=show_id,
            is_active=True
        ).all()
        
        # Get current user's friends for friend status
        from app.models import Friendship
        friends = Friendship.query.filter(
            db.or_(
                Friendship.user_id == current_user_id,
                Friendship.friend_id == current_user_id
            ),
            Friendship.status == 'accepted'
        ).all()
        
        friend_ids = set()
        for f in friends:
            friend_ids.add(f.user_id if f.friend_id == current_user_id else f.friend_id)
        
        users = []
        for checkin in checkins:
            if checkin.user_id != current_user_id:
                user_data = {
                    'id': checkin.user_id,
                    'username': checkin.user.username if checkin.user else 'Unknown',
                    'is_friend': checkin.user_id in friend_ids,
                    'last_seen': checkin.last_location_update.isoformat() if checkin.last_location_update else checkin.checked_in_at.isoformat()
                }
                # Include coordinates for friends
                if checkin.user_id in friend_ids and checkin.latitude is not None:
                    user_data['latitude'] = checkin.latitude
                    user_data['longitude'] = checkin.longitude
                users.append(user_data)
        
        return {'users': users}
    
    @api.doc('update_presence', security='jwt')
    @jwt_required()
    def post(self, show_id):
        """Update location for presence tracking"""
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        data = request.get_json()
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Find or create checkin
        checkin = ShowCheckin.query.filter_by(
            user_id=current_user_id,
            show_id=show_id
        ).first()
        
        if not checkin:
            checkin = ShowCheckin(
                user_id=current_user_id,
                show_id=show_id,
                is_active=True
            )
            db.session.add(checkin)
        
        checkin.latitude = latitude
        checkin.longitude = longitude
        checkin.last_location_update = datetime.utcnow()
        checkin.is_active = True
        
        db.session.commit()
        
        return {'message': 'Location updated'}
    
    @api.doc('stop_presence', security='jwt')
    @jwt_required()
    def delete(self, show_id):
        """Stop sharing location"""
        current_user_id = int(get_jwt_identity())
        
        checkin = ShowCheckin.query.filter_by(
            user_id=current_user_id,
            show_id=show_id
        ).first()
        
        if checkin:
            checkin.is_active = False
            checkin.latitude = None
            checkin.longitude = None
            db.session.commit()
        
        return {'message': 'Location sharing stopped'}


@api.route('/<int:show_id>/photos')
class ShowPhotos(Resource):
    @api.doc('get_show_photos', security='jwt')
    @jwt_required()
    def get(self, show_id):
        """Get all photos for a show"""
        show = Show.query.get_or_404(show_id)
        from app.models import Photo
        photos = Photo.query.filter_by(show_id=show_id).order_by(Photo.created_at.desc()).all()
        return {'photos': [p.to_dict() for p in photos]}
    
    @api.doc('upload_show_photo', security='jwt')
    @jwt_required()
    def post(self, show_id):
        """Upload a photo to a show"""
        import os
        from werkzeug.utils import secure_filename
        
        current_user_id = int(get_jwt_identity())
        show = Show.query.get_or_404(show_id)
        
        if 'photo' not in request.files:
            return {'error': 'No photo provided'}, 400
        
        file = request.files['photo']
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        # Generate unique filename
        import uuid
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return {'error': 'Invalid file type'}, 400
        
        filename = f"{uuid.uuid4()}{ext}"

        # Save file
        base_dir = os.path.dirname(os.path.dirname(__file__))
        upload_folder = os.path.join(base_dir, 'uploads', 'photos')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Generate thumbnail
        thumbnail_filename = None
        try:
            from PIL import Image as PILImage
            thumbnail_dir = os.path.join(base_dir, 'uploads', 'thumbnails')
            os.makedirs(thumbnail_dir, exist_ok=True)
            with PILImage.open(filepath) as img:
                img.thumbnail((300, 300), PILImage.Resampling.LANCZOS)
                thumbnail_filename = f"thumb_{filename}"
                img.save(os.path.join(thumbnail_dir, thumbnail_filename))
        except Exception as e:
            print(f'Thumbnail generation failed: {e}')
            thumbnail_filename = None

        # Create photo record
        from app.models import Photo
        photo = Photo(
            user_id=current_user_id,
            show_id=show_id,
            filename=filename,
            original_filename=secure_filename(file.filename),
            thumbnail_filename=thumbnail_filename,
            caption=request.form.get('caption', '')
        )
        
        db.session.add(photo)
        db.session.commit()
        
        return photo.to_dict(), 201

