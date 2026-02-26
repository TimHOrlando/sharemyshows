"""
Dashboard API Routes - Flask-RESTX Implementation
Handles user statistics and recent activity feeds
"""
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, text
import requests
import time
import re
import threading

from app.models import (
    db, Show, Artist, Venue, Photo, AudioRecording,
    VideoRecording, Comment, User
)
from app import cache

MUSICBRAINZ_BASE_URL = 'https://musicbrainz.org/ws/2'
MUSICBRAINZ_HEADERS = {
    'User-Agent': 'ShareMyShows/1.0 (tim.h.orlando@gmail.com)',
    'Accept': 'application/json'
}


def fetch_artist_metadata(mbid):
    """Fetch artist description and image via MusicBrainz → Wikidata → Wikipedia pipeline.
    Returns dict with 'description' and 'image_url' keys (values may be None)."""
    result = {'description': None, 'image_url': None}
    try:
        # Step 1: Get Wikidata URL and image relations from MusicBrainz
        resp = requests.get(
            f'{MUSICBRAINZ_BASE_URL}/artist/{mbid}?inc=url-rels&fmt=json',
            headers=MUSICBRAINZ_HEADERS,
            timeout=5
        )
        if resp.status_code != 200:
            return result

        data = resp.json()
        artist_name = data.get('name', '')

        # Look for wikidata link, direct wikipedia link, and image relations
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
            elif rel.get('type') == 'image':
                # Wikimedia Commons image relation
                # URL like: https://commons.wikimedia.org/wiki/File:Band.jpg
                commons_match = re.search(r'commons\.wikimedia\.org/wiki/File:(.+)$', url)
                if commons_match and not result['image_url']:
                    filename = commons_match.group(1)
                    result['image_url'] = f'https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=300'

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

        # Step 3: Fetch Wikipedia summary (also provides thumbnail as fallback)
        if wiki_title:
            time.sleep(1)
            wiki_resp = requests.get(
                f'https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}',
                headers={'User-Agent': 'ShareMyShows/1.0'},
                timeout=5
            )
            if wiki_resp.status_code == 200:
                wiki_data = wiki_resp.json()
                result['description'] = wiki_data.get('extract', '')

                # Use Wikipedia thumbnail as fallback if no MusicBrainz image
                if not result['image_url']:
                    thumbnail = wiki_data.get('thumbnail', {})
                    if thumbnail.get('source'):
                        result['image_url'] = thumbnail['source']

        # Step 4: Deezer fallback if still no image
        if not result['image_url'] and artist_name:
            try:
                deezer_resp = requests.get(
                    'https://api.deezer.com/search/artist',
                    params={'q': artist_name, 'limit': 5},
                    timeout=5
                )
                if deezer_resp.status_code == 200:
                    deezer_data = deezer_resp.json()
                    # Find best match by comparing names case-insensitively
                    for hit in deezer_data.get('data', []):
                        if hit.get('name', '').lower() == artist_name.lower():
                            result['image_url'] = hit.get('picture_medium') or hit.get('picture')
                            break
                    # If no exact match, use first result
                    if not result['image_url'] and deezer_data.get('data'):
                        result['image_url'] = deezer_data['data'][0].get('picture_medium') or deezer_data['data'][0].get('picture')
            except Exception:
                pass

        return result

    except Exception:
        return result

def _backfill_artist_metadata(artist_ids_with_mbids, app):
    """Background thread: fetch and save artist descriptions and images without blocking requests."""
    with app.app_context():
        for artist_id, mbid in artist_ids_with_mbids:
            metadata = fetch_artist_metadata(mbid)
            artist = Artist.query.get(artist_id)
            if artist:
                if metadata['description'] and not artist.disambiguation:
                    artist.disambiguation = metadata['description']
                if metadata['image_url'] and not artist.image_url:
                    artist.image_url = metadata['image_url']
        db.session.commit()


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
    'description': fields.String(description='Artist description from Wikipedia via MusicBrainz'),
    'image_url': fields.String(description='Artist thumbnail image URL')
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

        cache_key = f'dashboard_stats_{current_user_id}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Single query instead of 7 separate COUNT queries
        row = db.session.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM shows WHERE user_id = :uid) as total_shows,
                (SELECT COUNT(DISTINCT artist_id) FROM shows WHERE user_id = :uid) as total_artists,
                (SELECT COUNT(DISTINCT venue_id) FROM shows WHERE user_id = :uid) as total_venues,
                (SELECT COUNT(*) FROM photos WHERE user_id = :uid) as total_photos,
                (SELECT COUNT(*) FROM audio_recordings WHERE user_id = :uid) as total_audio,
                (SELECT COUNT(*) FROM video_recordings WHERE user_id = :uid) as total_videos,
                (SELECT COUNT(*) FROM comments WHERE user_id = :uid) as total_comments
        """), {'uid': current_user_id}).fetchone()

        result = {
            'total_shows': row[0],
            'total_artists': row[1],
            'total_venues': row[2],
            'total_photos': row[3],
            'total_audio': row[4],
            'total_videos': row[5],
            'total_comments': row[6]
        }
        cache.set(cache_key, result, timeout=120)
        return result


@api.route('/artists')
class DashboardArtists(Resource):
    @api.doc('get_top_artists', security='jwt')
    @api.response(200, 'Success', artist_list_model)
    @jwt_required()
    def get(self):
        """Get user's top artists by show count"""
        current_user_id = int(get_jwt_identity())

        cache_key = f'dashboard_artists_{current_user_id}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get artists with show counts
        artist_stats = db.session.query(
            Artist.id,
            Artist.name,
            Artist.mbid,
            Artist.disambiguation,
            Artist.image_url,
            func.count(Show.id).label('show_count')
        ).join(Show, Show.artist_id == Artist.id)\
         .filter(Show.user_id == current_user_id)\
         .group_by(Artist.id, Artist.name, Artist.mbid, Artist.disambiguation, Artist.image_url)\
         .order_by(func.count(Show.id).desc())\
         .all()

        # Fire-and-forget backfill for artists missing description OR image_url
        to_backfill = [(aid, mbid) for aid, name, mbid, desc, img, count in artist_stats if mbid and (not desc or not img)]
        if to_backfill[:3]:
            from flask import current_app
            app = current_app._get_current_object()
            threading.Thread(
                target=_backfill_artist_metadata,
                args=(to_backfill[:3], app),
                daemon=True
            ).start()

        results = [{
            'artist_id': artist_id,
            'artist_name': artist_name,
            'show_count': show_count,
            'description': description or '',
            'image_url': image_url or ''
        } for artist_id, artist_name, mbid, description, image_url, show_count in artist_stats]

        result = {
            'artists': results,
            'total': len(results)
        }
        cache.set(cache_key, result, timeout=120)
        return result


@api.route('/venues')
class DashboardVenues(Resource):
    @api.doc('get_top_venues', security='jwt')
    @api.response(200, 'Success', venue_list_model)
    @jwt_required()
    def get(self):
        """Get user's top venues by show count"""
        current_user_id = int(get_jwt_identity())

        cache_key = f'dashboard_venues_{current_user_id}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get venues with show counts
        venue_stats = db.session.query(
            Venue.id,
            Venue.name,
            func.count(Show.id).label('show_count')
        ).join(Show, Show.venue_id == Venue.id)\
         .filter(Show.user_id == current_user_id)\
         .group_by(Venue.id, Venue.name)\
         .order_by(func.count(Show.id).desc())\
         .all()

        results = [{
            'venue_id': venue_id,
            'venue_name': venue_name,
            'show_count': show_count
        } for venue_id, venue_name, show_count in venue_stats]

        result = {
            'venues': results,
            'total': len(results)
        }
        cache.set(cache_key, result, timeout=120)
        return result


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

