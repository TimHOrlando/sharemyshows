"""
Show model for tracking concert events
"""
from datetime import datetime, date
from app import db


# Association table for many-to-many relationship between shows and artists
show_artists = db.Table('show_artists',
    db.Column('show_id', db.BigInteger, db.ForeignKey('shows.id', ondelete='CASCADE'), primary_key=True),
    db.Column('artist_id', db.BigInteger, db.ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


class Show(db.Model):
    """Show model"""
    
    __tablename__ = 'shows'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    venue_id = db.Column(db.BigInteger, db.ForeignKey('venues.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    # Show details
    show_date = db.Column(db.Date, nullable=False, index=True)
    show_time = db.Column(db.Time, nullable=True)
    title = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Privacy settings
    is_public = db.Column(db.Boolean, default=True)
    
    # Show status
    is_past = db.Column(db.Boolean, default=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    artists = db.relationship('Artist', secondary=show_artists, back_populates='shows', lazy='joined')
    
    # Phase 2: Photos, Audio, Setlist, Comments will be added
    # photos = db.relationship('Photo', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    # audio = db.relationship('Audio', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    # setlist = db.relationship('SetlistSong', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    # comments = db.relationship('Comment', backref='show', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Show {self.id} on {self.show_date}>'
    
    def check_if_past(self):
        """Check if the show date is in the past"""
        if self.show_date < date.today():
            self.is_past = True
        else:
            self.is_past = False
    
    def to_dict(self, include_user=False, include_venue=True, include_artists=True):
        """Convert show to dictionary"""
        self.check_if_past()
        
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'venue_id': self.venue_id,
            'show_date': self.show_date.isoformat() if self.show_date else None,
            'show_time': self.show_time.isoformat() if self.show_time else None,
            'title': self.title,
            'notes': self.notes,
            'is_public': self.is_public,
            'is_past': self.is_past,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Include user information if requested
        if include_user and self.user:
            data['user'] = self.user.to_dict()
        
        # Include venue information if requested
        if include_venue and self.venue:
            data['venue'] = self.venue.to_dict()
        
        # Include artists information if requested
        if include_artists:
            data['artists'] = [artist.to_dict() for artist in self.artists]
        
        return data
    
    def can_be_edited_by(self, user_id):
        """Check if the show can be edited by the given user"""
        return self.user_id == user_id
    
    def can_be_viewed_by(self, user_id=None):
        """Check if the show can be viewed by the given user"""
        # Public shows can be viewed by anyone
        if self.is_public:
            return True
        
        # Private shows can only be viewed by the owner
        if user_id:
            return self.user_id == user_id
        
        return False
