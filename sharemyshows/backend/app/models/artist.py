"""
Artist model for tracking performing artists
"""
from datetime import datetime
from app import db


class Artist(db.Model):
    """Artist model"""
    
    __tablename__ = 'artists'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    shows = db.relationship('Show', secondary='show_artists', back_populates='artists', lazy='dynamic')
    
    def __repr__(self):
        return f'<Artist {self.name}>'
    
    def to_dict(self):
        """Convert artist to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
