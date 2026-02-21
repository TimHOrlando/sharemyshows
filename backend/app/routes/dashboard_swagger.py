"""
Dashboard API Routes - Flask-RESTX Implementation
Handles user statistics and recent activity feeds
"""
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
import requests
import time
import re

from app.models import (
    db, Show, Artist, Venue, Photo, AudioRecording,
    VideoRecording, Comment, User
)

MUSICBRAINZ_BASE_URL = 'https://musicbrainz.org/ws/2'
MUSICBRAINZ_HEADERS = {
    'User-Agent': 'ShareMyShows/1.0 (tim.h.orlando@gmail.com)',
    'Accept': 'application/json'
}


def fetch_artist_description(mbid):
    """Fetch artist description via MusicBrainz → Wikidata → Wikipedia pipeline.
    Returns description string or None."""
    try:
        # Step 1: Get Wikidata URL from MusicBrainz
        resp = requests.get(
            f'{MUSICBRAINZ_BASE_URL}/artist/{mbid}?inc=url-rels&fmt=json',
            headers=MUSICBRAINZ_HEADERS,
            timeout=5
        )
        if resp.status_code != 200:
            return None

        data = resp.json()

        # Look for wikidata link first, then direct wikipedia link
        wikidata_qid = None
        wiki_title = None
        for rel in data.get('relations', []):
            url = rel.get('url', {}).get('resource', '')
            if rel.get('type') == 'wikidata':
                match = re.search(r'/wiki/(Q\d+)$', url)
                if match:
                    wikidata_qid = match.group(1)
            elif rel.get('type') == 'wikipedia':
                match = re.search(r'en\.wikipedia\.org/wiki/(.+)$', url)
                if match:
                    wiki_title = match.group(1)

        # Step 2: Resolve Wikipedia title via Wikidata if needed
        if not wiki_title and wikidata_qid:
            time.sleep(1)  # MusicBrainz rate limit: 1 req/sec
            wd_resp = requests.get(
                f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={wikidata_qid}&sitefilter=enwiki&props=sitelinks&format=json',
                headers={'User-Agent': 'ShareMyShows/1.0'},
                timeout=5
            )
            if wd_resp.status_code == 200:
                wd_data = wd_resp.json()
                sitelinks = wd_data.get('entities', {}).get(wikidata_qid, {}).get('sitelinks', {})
                if 'enwiki' in sitelinks:
                    wiki_title = sitelinks['enwiki']['title']

        if not wiki_title:
            return None

        # Step 3: Fetch Wikipedia summary
        time.sleep(1)
        wiki_resp = requests.get(
            f'https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}',
            headers={'User-Agent': 'ShareMyShows/1.0'},
            timeout=5
        )
        if wiki_resp.status_code != 200:
            return None

        wiki_data = wiki_resp.json()
        return wiki_data.get('extract', '')

    except Exception:
        return None

# Create namespace
api = Namespace('dashboard', description='Dashboard statistics and recent activity')

# Models
stats_model = api.model('DashboardStats', {
    'total_shows': fields.Integer(description='Total shows attended'),
    'total_artists': fields.Integer(description='Unique artists seen'),
    'total_venues': fields.Integer(description='Unique venues visited'),
    'total_photos': fields.Integer(description='Total photos uploaded'),
    'total_audio': fields.Integer(description='Total audio recordings'),
    'total_videos': fields.Integer(description='Total video recordings'),
    'total_comments': fields.Integer(description='Total comments made')
})

artist_stats_model = api.model('ArtistStats', {
    'artist_name': fields.String(description='Artist name'),
    'show_count': fields.Integer(description='Number of shows'),
    'artist_id': fields.Integer(description='Artist ID'),
    'description': fields.String(description='Artist description from Wikipedia via MusicBrainz')
})

venue_stats_model = api.model('VenueStats', {
    'venue_name': fields.String(description='Venue name'),
    'show_count': fields.Integer(description='Number of shows'),
    'venue_id': fields.Integer(description='Venue ID')
})

photo_brief_model = api.model('PhotoBrief', {
    'id': fields.Integer(description='Photo ID'),
    'show_id': fields.Integer(description='Show ID'),
    'caption': fields.String(description='Caption'),
    'uploaded_at': fields.DateTime(description='Upload time'),
    'show_name': fields.String(description='Show name')
})

audio_brief_model = api.model('AudioBrief', {
    'id': fields.Integer(description='Audio ID'),
    'show_id': fields.Integer(description='Show ID'),
    'title': fields.String(description='Title'),
    'uploaded_at': fields.DateTime(description='Upload time'),
    'show_name': fields.String(description='Show name')
})

video_brief_model = api.model('VideoBrief', {
    'id': fields.Integer(description='Video ID'),
    'show_id': fields.Integer(description='Show ID'),
    'title': fields.String(description='Title'),
    'uploaded_at': fields.DateTime(description='Upload time'),
    'show_name': fields.String(description='Show name')
})

comment_brief_model = api.model('CommentBrief', {
    'id': fields.Integer(description='Comment ID'),
    'show_id': fields.Integer(description='Show ID'),
    'content': fields.String(description='Comment text'),
    'created_at': fields.DateTime(description='Creation time'),
    'show_name': fields.String(description='Show name')
})

artist_list_model = api.model('ArtistList', {
    'artists': fields.List(fields.Nested(artist_stats_model)),
    'total': fields.Integer(description='Total artists')
})

venue_list_model = api.model('VenueList', {
    'venues': fields.List(fields.Nested(venue_stats_model)),
    'total': fields.Integer(description='Total venues')
})

photo_list_model = api.model('PhotoList', {
    'photos': fields.List(fields.Nested(photo_brief_model)),
    'total': fields.Integer(description='Total photos')
})

audio_list_model = api.model('AudioList', {
    'recordings': fields.List(fields.Nested(audio_brief_model)),
    'total': fields.Integer(description='Total recordings')
})

video_list_model = api.model('VideoList', {
    'recordings': fields.List(fields.Nested(video_brief_model)),
    'total': fields.Integer(description='Total recordings')
})

comment_list_model = api.model('CommentList', {
    'comments': fields.List(fields.Nested(comment_brief_model)),
    'total': fields.Integer(description='Total comments')
})


@api.route('/stats')
class DashboardStats(Resource):
    @api.doc('get_dashboard_stats', security='jwt')
    @api.response(200, 'Success', stats_model)
    @jwt_required()
    def get(self):
        """Get user statistics overview"""
        current_user_id = int(get_jwt_identity())
        
        # Count user's shows
        total_shows = Show.query.filter_by(user_id=current_user_id).count()
        
        # Count unique artists
        total_artists = db.session.query(func.count(func.distinct(Show.artist_id)))\
            .filter(Show.user_id == current_user_id).scalar() or 0
        
        # Count unique venues
        total_venues = db.session.query(func.count(func.distinct(Show.venue_id)))\
            .filter(Show.user_id == current_user_id).scalar() or 0
        
        # Count media
        total_photos = Photo.query.filter_by(user_id=current_user_id).count()
        total_audio = AudioRecording.query.filter_by(user_id=current_user_id).count()
        total_videos = VideoRecording.query.filter_by(user_id=current_user_id).count()
        total_comments = Comment.query.filter_by(user_id=current_user_id).count()
        
        return {
            'total_shows': total_shows,
            'total_artists': total_artists,
            'total_venues': total_venues,
            'total_photos': total_photos,
            'total_audio': total_audio,
            'total_videos': total_videos,
            'total_comments': total_comments
        }


@api.route('/artists')
class DashboardArtists(Resource):
    @api.doc('get_top_artists', security='jwt')
    @api.response(200, 'Success', artist_list_model)
    @jwt_required()
    def get(self):
        """Get user's top artists by show count"""
        current_user_id = int(get_jwt_identity())

        # Get artists with show counts
        artist_stats = db.session.query(
            Artist.id,
            Artist.name,
            Artist.mbid,
            Artist.disambiguation,
            func.count(Show.id).label('show_count')
        ).join(Show, Show.artist_id == Artist.id)\
         .filter(Show.user_id == current_user_id)\
         .group_by(Artist.id, Artist.name, Artist.mbid, Artist.disambiguation)\
         .order_by(func.count(Show.id).desc())\
         .all()

        # Lazily backfill descriptions from MusicBrainz/Wikipedia (up to 3 per request)
        backfill_count = 0
        for artist_id, artist_name, mbid, description, show_count in artist_stats:
            if mbid and not description and backfill_count < 3:
                desc = fetch_artist_description(mbid)
                if desc:
                    artist = Artist.query.get(artist_id)
                    artist.disambiguation = desc
                    backfill_count += 1
        if backfill_count > 0:
            db.session.commit()
            # Re-query to get updated descriptions
            artist_stats = db.session.query(
                Artist.id,
                Artist.name,
                Artist.mbid,
                Artist.disambiguation,
                func.count(Show.id).label('show_count')
            ).join(Show, Show.artist_id == Artist.id)\
             .filter(Show.user_id == current_user_id)\
             .group_by(Artist.id, Artist.name, Artist.mbid, Artist.disambiguation)\
             .order_by(func.count(Show.id).desc())\
             .all()

        results = [{
            'artist_id': artist_id,
            'artist_name': artist_name,
            'show_count': show_count,
            'description': description or ''
        } for artist_id, artist_name, mbid, description, show_count in artist_stats]

        return {
            'artists': results,
            'total': len(results)
        }


@api.route('/venues')
class DashboardVenues(Resource):
    @api.doc('get_top_venues', security='jwt')
    @api.response(200, 'Success', venue_list_model)
    @jwt_required()
    def get(self):
        """Get user's top venues by show count"""
        current_user_id = int(get_jwt_identity())
        
        # Get venues with show counts
        venue_stats = db.session.query(
            Venue.id,
            Venue.name,
            func.count(Show.id).label('show_count')
        ).join(Show, Show.venue_id == Venue.id)\
         .filter(Show.user_id == current_user_id)\
         .group_by(Venue.id, Venue.name)\
         .order_by(func.count(Show.id).desc())\
         .limit(10)\
         .all()
        
        results = [{
            'venue_id': venue_id,
            'venue_name': venue_name,
            'show_count': show_count
        } for venue_id, venue_name, show_count in venue_stats]
        
        return {
            'venues': results,
            'total': len(results)
        }


@api.route('/photos/recent')
class DashboardRecentPhotos(Resource):
    @api.doc('get_recent_photos', security='jwt')
    @api.response(200, 'Success', photo_list_model)
    @jwt_required()
    def get(self):
        """Get user's recent photos"""
        current_user_id = int(get_jwt_identity())
        
        photos = db.session.query(Photo, Show)\
            .join(Show, Photo.show_id == Show.id)\
            .filter(Photo.user_id == current_user_id)\
            .order_by(Photo.created_at.desc())\
            .limit(10)\
            .all()
        
        results = [{
            'id': photo.id,
            'show_id': photo.show_id,
            'caption': photo.caption,
            'uploaded_at': photo.created_at.isoformat(),
            'show_name': f"{show.artist.name} at {show.venue.name}" if show.artist and show.venue else 'Unknown Show'
        } for photo, show in photos]
        
        return {
            'photos': results,
            'total': len(results)
        }


@api.route('/audio/recent')
class DashboardRecentAudio(Resource):
    @api.doc('get_recent_audio', security='jwt')
    @api.response(200, 'Success', audio_list_model)
    @jwt_required()
    def get(self):
        """Get user's recent audio recordings"""
        current_user_id = int(get_jwt_identity())
        
        recordings = db.session.query(AudioRecording, Show)\
            .join(Show, AudioRecording.show_id == Show.id)\
            .filter(AudioRecording.user_id == current_user_id)\
            .order_by(AudioRecording.created_at.desc())\
            .limit(10)\
            .all()
        
        results = [{
            'id': audio.id,
            'show_id': audio.show_id,
            'title': audio.title,
            'uploaded_at': audio.created_at.isoformat(),
            'show_name': f"{show.artist.name} at {show.venue.name}" if show.artist and show.venue else 'Unknown Show'
        } for audio, show in recordings]
        
        return {
            'recordings': results,
            'total': len(results)
        }


@api.route('/videos/recent')
class DashboardRecentVideos(Resource):
    @api.doc('get_recent_videos', security='jwt')
    @api.response(200, 'Success', video_list_model)
    @jwt_required()
    def get(self):
        """Get user's recent video recordings"""
        current_user_id = int(get_jwt_identity())
        
        recordings = db.session.query(VideoRecording, Show)\
            .join(Show, VideoRecording.show_id == Show.id)\
            .filter(VideoRecording.user_id == current_user_id)\
            .order_by(VideoRecording.created_at.desc())\
            .limit(10)\
            .all()
        
        results = [{
            'id': video.id,
            'show_id': video.show_id,
            'title': video.title,
            'uploaded_at': video.created_at.isoformat(),
            'show_name': f"{show.artist.name} at {show.venue.name}" if show.artist and show.venue else 'Unknown Show'
        } for video, show in recordings]
        
        return {
            'recordings': results,
            'total': len(results)
        }


@api.route('/comments/recent')
class DashboardRecentComments(Resource):
    @api.doc('get_recent_comments', security='jwt')
    @api.response(200, 'Success', comment_list_model)
    @jwt_required()
    def get(self):
        """Get user's recent comments"""
        current_user_id = int(get_jwt_identity())
        
        comments = db.session.query(Comment, Show)\
            .join(Show, Comment.show_id == Show.id)\
            .filter(Comment.user_id == current_user_id)\
            .order_by(Comment.created_at.desc())\
            .limit(10)\
            .all()
        
        results = [{
            'id': comment.id,
            'show_id': comment.show_id,
            'content': comment.text,
            'created_at': comment.created_at.isoformat(),
            'show_name': f"{show.artist.name} at {show.venue.name}" if show.artist and show.venue else 'Unknown Show'
        } for comment, show in comments]
        
        return {
            'comments': results,
            'total': len(results)
        }

