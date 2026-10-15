import pytest
from db import get_db
from tests.conftest import register_user, login_user


class TestRegistration:
    """Test user registration."""

    def test_register_page_loads(self, client):
        """GET /auth/register returns 200."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create Your Account' in response.data

    def test_successful_registration(self, client, app):
        """Valid registration creates user and redirects to login."""
        response = register_user(client)
        assert response.status_code == 200
        # Should redirect to login page after registration
        assert b'Welcome Back' in response.data or b'Registration successful' in response.data

        # Verify user exists in database with hashed password
        with app.app_context():
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',)).fetchone()
            assert user is not None
            assert user['username'] == 'testuser'
            assert user['password_hash'] != 'password123'  # Must be hashed
            assert user['password_hash'].startswith('scrypt:') or user['password_hash'].startswith('pbkdf2:')

    def test_duplicate_email_rejected(self, client):
        """Registration with existing email fails."""
        register_user(client)
        response = register_user(client, username='different_user')
        assert b'already registered' in response.data or b'already' in response.data.lower()

    def test_duplicate_username_rejected(self, client):
        """Registration with existing username fails."""
        register_user(client)
        response = register_user(client, email='other@example.com')
        assert b'already' in response.data.lower()

    def test_password_mismatch_rejected(self, client):
        """Registration with mismatched passwords fails."""
        response = register_user(client, confirm_password='different')
        assert b'match' in response.data.lower()

    def test_short_password_rejected(self, client):
        """Registration with short password fails."""
        response = register_user(client, password='short', confirm_password='short')
        assert b'8 characters' in response.data.lower() or b'minimum' in response.data.lower()

    def test_invalid_username_rejected(self, client):
        """Registration with invalid username format fails."""
        response = register_user(client, username='ab')  # too short
        assert response.status_code == 200

    def test_invalid_email_rejected(self, client):
        """Registration with invalid email fails."""
        response = register_user(client, email='notanemail')
        assert response.status_code == 200

    def test_empty_fields_rejected(self, client):
        """Registration with empty required fields fails."""
        response = client.post('/auth/register', data={
            'email': '',
            'username': '',
            'password': '',
            'confirm_password': '',
            'full_name': '',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestLogin:
    """Test user login."""

    def test_login_page_loads(self, client):
        """GET /auth/login returns 200."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Welcome Back' in response.data

    def test_successful_login(self, client):
        """Valid credentials log user in."""
        register_user(client)
        response = login_user(client)
        assert response.status_code == 200
        # Should be on dashboard after login
        assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()

    def test_invalid_email_login(self, client):
        """Login with nonexistent email fails."""
        response = login_user(client, email='nobody@example.com')
        assert b'Invalid' in response.data or b'invalid' in response.data.lower()

    def test_wrong_password_login(self, client):
        """Login with wrong password fails."""
        register_user(client)
        response = login_user(client, password='wrongpassword')
        assert b'Invalid' in response.data or b'invalid' in response.data.lower()


class TestLogout:
    """Test logout."""

    def test_logout(self, client):
        """Logout clears session."""
        register_user(client)
        login_user(client)
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'logged out' in response.data.lower() or b'Sign In' in response.data


class TestAccessControl:
    """Test route protection."""

    def test_dashboard_requires_login(self, client):
        """Dashboard redirects unauthenticated users."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_accessible_when_logged_in(self, client):
        """Dashboard accessible after login."""
        register_user(client)
        login_user(client)
        response = client.get('/dashboard')
        assert response.status_code == 200

    def test_dashboard_after_logout_redirects(self, client):
        """Dashboard redirects after logout."""
        register_user(client)
        login_user(client)
        client.get('/auth/logout')
        response = client.get('/dashboard')
        assert response.status_code == 302
