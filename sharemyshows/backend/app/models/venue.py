"""
Venue model for tracking concert venues
"""
from datetime import datetime
from app import db


class Venue(db.Model):
    """Venue model"""
    
    __tablename__ = 'venues'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    location = db.Column(db.String(512), nullable=False)
    city = db.Column(db.String(100), nullable=True, index=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # GPS coordinates for location-based features
    latitude = db.Column(db.Numeric(precision=10, scale=8), nullable=True)
    longitude = db.Column(db.Numeric(precision=11, scale=8), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    shows = db.relationship('Show', backref='venue', lazy='dynamic')
    
    def __repr__(self):
        return f'<Venue {self.name}>'
    
    def to_dict(self):
        """Convert venue to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
