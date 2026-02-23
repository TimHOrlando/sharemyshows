"""
Authentication tests
"""
import pytest


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration"""
    
    def test_register_success(self, client, db_session):
        """Test successful user registration"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 201
        assert 'user' in response.json
        assert response.json['user']['email'] == 'newuser@example.com'
        assert response.json['user']['username'] == 'newuser'
    
    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email"""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'username': 'differentuser',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 409
        assert 'already registered' in response.json['message'].lower()
    
    def test_register_duplicate_username(self, client, sample_user):
        """Test registration with duplicate username"""
        response = client.post('/api/auth/register', json={
            'email': 'different@example.com',
            'username': 'testuser',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 409
        assert 'already taken' in response.json['message'].lower()
    
    def test_register_weak_password(self, client, db_session):
        """Test registration with weak password"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'weak'
        })
        
        assert response.status_code == 400
        assert 'password' in response.json['message'].lower()
    
    def test_register_invalid_email(self, client, db_session):
        """Test registration with invalid email"""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'username': 'newuser',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 400
        assert 'email' in response.json['message'].lower()


@pytest.mark.auth
class TestUserLogin:
    """Test user login"""
    
    def test_login_success(self, client, sample_user):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 200
        assert 'access_token' in response.json
        assert 'refresh_token' in response.json
        assert 'user' in response.json
    
    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password"""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client, db_session):
        """Test login with nonexistent user"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 401


@pytest.mark.auth
class TestProtectedRoutes:
    """Test protected routes"""
    
    def test_get_me_success(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'user' in response.json
        assert response.json['user']['email'] == 'test@example.com'
    
    def test_get_me_without_token(self, client):
        """Test getting current user without token"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_logout_success(self, client, auth_headers):
        """Test logout"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
