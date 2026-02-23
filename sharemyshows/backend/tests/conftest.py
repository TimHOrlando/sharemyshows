"""
Pytest configuration and fixtures
"""
import pytest
from app import create_app, db
from app.models import User, Artist, Venue, Show
from config.config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for each test"""
    with app.app_context():
        # Clear all tables
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        yield db.session
        
        # Cleanup
        db.session.remove()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        email='test@example.com',
        username='testuser'
    )
    user.set_password('SecurePass123!')
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def sample_artist(db_session):
    """Create a sample artist for testing"""
    artist = Artist(name='Test Artist')
    db_session.add(artist)
    db_session.commit()
    
    return artist


@pytest.fixture
def sample_venue(db_session):
    """Create a sample venue for testing"""
    venue = Venue(
        name='Test Venue',
        location='123 Test St, Test City, TS',
        city='Test City',
        state='Test State',
        country='Test Country',
        latitude=40.7128,
        longitude=-74.0060
    )
    db_session.add(venue)
    db_session.commit()
    
    return venue


@pytest.fixture
def auth_headers(client, sample_user):
    """Get authentication headers with JWT token"""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'SecurePass123!'
    })
    
    token = response.json['access_token']
    
    return {
        'Authorization': f'Bearer {token}'
    }
