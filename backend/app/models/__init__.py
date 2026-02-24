from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import pyotp

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and profile"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # MFA
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_method = db.Column(db.String(20))
    mfa_secret = db.Column(db.String(32))
    phone_number = db.Column(db.String(20))
    mfa_code = db.Column(db.String(6))  # Add this
    mfa_code_expires = db.Column(db.DateTime)  # Add this
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    
    # Password reset
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    
    # Preferences
    theme_preference = db.Column(db.String(20), default='forest')
    appear_offline = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shows = db.relationship('Show', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    photos = db.relationship('Photo', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    audio_recordings = db.relationship('AudioRecording', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    video_recordings = db.relationship('VideoRecording', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    checkins = db.relationship('ShowCheckin', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sent_messages = db.relationship('ChatMessage', backref='sender', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_mfa_secret(self):
        self.mfa_secret = pyotp.random_base32()
        return self.mfa_secret
    
    def get_totp_uri(self):
        if self.mfa_secret:
            return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
                name=self.email,
                issuer_name='ShareMyShows'
            )
        return None
    
    def verify_totp(self, token):
        if self.mfa_secret:
            totp = pyotp.TOTP(self.mfa_secret)
            return totp.verify(token, valid_window=1)
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'mfa_enabled': self.mfa_enabled,
            'mfa_method': self.mfa_method,
            'email_verified': self.email_verified,
            'appear_offline': self.appear_offline or False,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Artist(db.Model):
    """Artist model"""
    __tablename__ = 'artists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    mbid = db.Column(db.String(36))
    spotify_id = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    disambiguation = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shows = db.relationship('Show', backref='artist', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mbid': self.mbid,
            'spotify_id': self.spotify_id,
            'image_url': self.image_url,
            'disambiguation': self.disambiguation
        }

class Venue(db.Model):
    """Venue model"""
    __tablename__ = 'venues'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    location = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    place_id = db.Column(db.String(100))
    address = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shows = db.relationship('Show', backref='venue', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'place_id': self.place_id,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

class Show(db.Model):
    """Show/Concert model"""
    __tablename__ = 'shows'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    photos = db.relationship('Photo', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    audio_recordings = db.relationship('AudioRecording', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    video_recordings = db.relationship('VideoRecording', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    setlist_songs = db.relationship('SetlistSong', backref='show', lazy='dynamic', cascade='all, delete-orphan', order_by='SetlistSong.order')
    checkins = db.relationship('ShowCheckin', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_details=False, viewer_id=None, counts=None):
        if counts:
            photo_count, audio_count, video_count, comment_count, song_count = counts
        else:
            photo_count = self.photos.count()
            audio_count = self.audio_recordings.count()
            video_count = self.video_recordings.count()
            comment_count = self.comments.count()
            song_count = self.setlist_songs.count()

        data = {
            'id': self.id,
            'user_id': self.user_id,
            'owner': {'id': self.user.id, 'username': self.user.username} if self.user else None,
            'is_owner': viewer_id == self.user_id if viewer_id else None,
            'artist': self.artist.to_dict() if self.artist else None,
            'venue': self.venue.to_dict() if self.venue else None,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.strftime('%H:%M') if self.time else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'photo_count': photo_count,
            'audio_count': audio_count,
            'video_count': video_count,
            'comment_count': comment_count,
            'song_count': song_count
        }

        if include_details:
            data['setlist'] = [song.to_dict() for song in self.setlist_songs]
            data['photos'] = [photo.to_dict() for photo in self.photos]
            data['audio'] = [audio.to_dict() for audio in self.audio_recordings]
            data['videos'] = [video.to_dict() for video in self.video_recordings]
            data['comments'] = [comment.to_dict() for comment in self.comments.filter(Comment.photo_id.is_(None))]

        return data

class Photo(db.Model):
    """Photo model"""
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    thumbnail_filename = db.Column(db.String(255))
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship('Comment', backref='photo', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'show_id': self.show_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'thumbnail_filename': self.thumbnail_filename,
            'caption': self.caption,
            'comment_count': self.comments.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'url': f'/api/photos/{self.id}',
            'thumbnail_url': f'/api/photos/{self.id}/thumbnail' if self.thumbnail_filename else None
        }

class AudioRecording(db.Model):
    """Audio recording model"""
    __tablename__ = 'audio_recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    title = db.Column(db.String(200))
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'show_id': self.show_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'title': self.title,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'url': f'/api/audio/{self.id}'
        }

class VideoRecording(db.Model):
    """Video recording model"""
    __tablename__ = 'video_recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    thumbnail_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'show_id': self.show_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'url': f'/api/videos/{self.id}',
            'thumbnail_url': f'/api/videos/{self.id}/thumbnail' if self.thumbnail_filename else None
        }

class Comment(db.Model):
    """Comment model"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'show_id': self.show_id,
            'photo_id': self.photo_id,
            'user': self.user.to_dict() if self.user else None,
            'text': self.text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SetlistSong(db.Model):
    """Setlist song model"""
    __tablename__ = 'setlist_songs'

    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)
    is_cover = db.Column(db.Boolean, default=False)
    original_artist = db.Column(db.String(200))
    duration = db.Column(db.String(20))
    songwriter = db.Column(db.String(200))
    with_artist = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'show_id': self.show_id,
            'title': self.title,
            'order': self.order,
            'notes': self.notes,
            'is_cover': self.is_cover or False,
            'original_artist': self.original_artist,
            'duration': self.duration,
            'songwriter': self.songwriter,
            'with_artist': self.with_artist,
        }

class Friendship(db.Model):
    """Friendship model"""
    __tablename__ = 'friendships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='friendships_sent')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friendships_received')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ShowCheckin(db.Model):
    """Show check-in model"""
    __tablename__ = 'show_checkins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    checked_in_at = db.Column(db.DateTime, default=datetime.utcnow)
    checked_out_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    share_with = db.Column(db.Text, nullable=True)  # JSON array of friend IDs, null = all friends

    __table_args__ = (
        db.UniqueConstraint('user_id', 'show_id', name='unique_user_show_checkin'),
    )

    def get_share_with_ids(self):
        """Return set of friend IDs to share with, or None (= all friends)."""
        if self.share_with is None:
            return None
        try:
            return set(json.loads(self.share_with))
        except (json.JSONDecodeError, TypeError):
            return None

    def set_share_with(self, friend_ids):
        """Set selective sharing list. None = share with all friends."""
        if friend_ids is None:
            self.share_with = None
        else:
            self.share_with = json.dumps([int(fid) for fid in friend_ids])

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict() if self.user else None,
            'show_id': self.show_id,
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
            'checked_out_at': self.checked_out_at.isoformat() if self.checked_out_at else None,
            'is_active': self.is_active,
            'share_with': self.get_share_with_ids(),
        }

class Conversation(db.Model):
    """Direct message conversation between two users"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    messages = db.relationship('DirectMessage', backref='conversation', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='DirectMessage.created_at')

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_conversation'),
        db.CheckConstraint('user1_id < user2_id', name='ordered_user_ids'),
    )

    def other_user(self, current_user_id):
        """Return the other user in the conversation"""
        if self.user1_id == current_user_id:
            return self.user2
        return self.user1

    def to_dict(self, current_user_id=None):
        other = self.other_user(current_user_id) if current_user_id else None
        return {
            'id': self.id,
            'other_user': {'id': other.id, 'username': other.username} if other else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DirectMessage(db.Model):
    """Direct message between two users"""
    __tablename__ = 'direct_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender': {'id': self.sender.id, 'username': self.sender.username} if self.sender else None,
            'body': self.body,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ChatMessage(db.Model):
    """Chat message model"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'show_id': self.show_id,
            'user': self.sender.to_dict() if self.sender else None,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def get_friend_ids(user_id):
    """Get set of user IDs that are accepted friends of the given user."""
    friendships = Friendship.query.filter(
        db.or_(
            Friendship.user_id == user_id,
            Friendship.friend_id == user_id
        ),
        Friendship.status == 'accepted'
    ).all()
    ids = set()
    for f in friendships:
        ids.add(f.friend_id if f.user_id == user_id else f.user_id)
    return ids

