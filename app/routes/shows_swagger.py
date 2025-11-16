"""
Shows API Routes - Flask-RESTX Implementation
Handles show CRUD operations, setlist management, and check-ins
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models import db, Show, Artist, Venue, SetlistSong, ShowCheckin, User

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
    'song_name': fields.String(description='Song name'),
    'order': fields.Integer(description='Order in setlist')
})

show_model = api.model('Show', {
    'id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'artist_id': fields.Integer(description='Artist ID'),
    'venue_id': fields.Integer(description='Venue ID'),
    'date': fields.Date(description='Show date'),
    'notes': fields.String(description='Notes'),
    'rating': fields.Integer(description='Rating 1-5'),
    'created_at': fields.DateTime(description='Created at'),
    'artist': fields.Nested(artist_model),
    'venue': fields.Nested(venue_model)
})

show_create_model = api.model('ShowCreate', {
    'artist_name': fields.String(required=True, description='Artist name'),
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
    'order': fields.Integer(required=False, description='Order in setlist')
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


@api.route('')
class ShowList(Resource):
    @api.doc('list_shows', security='jwt')
    @api.expect(show_list_parser)
    @api.marshal_list_with(show_model)
    @jwt_required()
    def get(self):
        """Get list of user's shows with optional filters"""
        current_user_id = get_jwt_identity()
        
        query = Show.query.filter_by(user_id=current_user_id)
        
        # Apply filters
        artist_filter = request.args.get('artist')
        venue_filter = request.args.get('venue')
        year_filter = request.args.get('year', type=int)
        
        if artist_filter:
            query = query.join(Artist).filter(Artist.name.ilike(f'%{artist_filter}%'))
        if venue_filter:
            query = query.join(Venue).filter(Venue.name.ilike(f'%{venue_filter}%'))
        if year_filter:
            query = query.filter(db.extract('year', Show.date) == year_filter)
        
        shows = query.order_by(Show.date.desc()).all()
        return [show.to_dict() for show in shows]
    
    @api.doc('create_show', security='jwt')
    @api.expect(show_create_model)
    @api.marshal_with(show_model, code=201)
    @jwt_required()
    def post(self):
        """Create a new show"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get or create artist
        artist_name = data.get('artist_name')
        artist = Artist.query.filter_by(name=artist_name).first()
        if not artist:
            artist = Artist(name=artist_name)
            db.session.add(artist)
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
        
        return show.to_dict(), 201


@api.route('/<int:show_id>')
class ShowDetail(Resource):
    @api.doc('get_show', security='jwt')
    @api.marshal_with(show_model)
    @jwt_required()
    def get(self, show_id):
        """Get show details"""
        show = Show.query.get_or_404(show_id)
        return show.to_dict()
    
    @api.doc('update_show', security='jwt')
    @api.expect(show_update_model)
    @api.marshal_with(show_model)
    @jwt_required()
    def put(self, show_id):
        """Update show"""
        current_user_id = get_jwt_identity()
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        if 'notes' in data:
            show.notes = data['notes']
        if 'rating' in data:
            show.rating = data['rating']
        
        db.session.commit()
        return show.to_dict()
    
    @api.doc('delete_show', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def delete(self, show_id):
        """Delete show"""
        current_user_id = get_jwt_identity()
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
        current_user_id = get_jwt_identity()
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
            song_name=data['song_name'],
            order=order
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
        current_user_id = get_jwt_identity()
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        song = SetlistSong.query.get_or_404(song_id)
        data = request.get_json()
        
        if 'song_name' in data:
            song.song_name = data['song_name']
        if 'order' in data:
            song.order = data['order']
        
        db.session.commit()
        return song.to_dict()
    
    @api.doc('delete_setlist_song', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def delete(self, show_id, song_id):
        """Remove song from setlist"""
        current_user_id = get_jwt_identity()
        show = Show.query.get_or_404(show_id)
        
        if show.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        song = SetlistSong.query.get_or_404(song_id)
        db.session.delete(song)
        db.session.commit()
        
        return {'message': 'Song removed from setlist'}


@api.route('/<int:show_id>/checkin')
class ShowCheckinEndpoint(Resource):
    @api.doc('checkin_to_show', security='jwt')
    @api.marshal_with(message_response)
    @jwt_required()
    def post(self, show_id):
        """Check in to a show"""
        current_user_id = get_jwt_identity()
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
        current_user_id = get_jwt_identity()
        
        checkin = ShowCheckin.query.filter_by(
            user_id=current_user_id,
            show_id=show_id
        ).first()
        
        if not checkin:
            return {'error': 'Not checked in'}, 400
        
        db.session.delete(checkin)
        db.session.commit()
        
        return {'message': 'Checked out successfully'}
