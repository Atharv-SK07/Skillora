import os
import tempfile
import pytest
from app import create_app
from db import get_db, init_db


@pytest.fixture
def app():
    """Create application for testing."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })

    with app.app_context():
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


def register_user(client, email='test@example.com', username='testuser',
                  password='password123', confirm_password='password123',
                  full_name='Test User'):
    """Helper to register a user."""
    return client.post('/auth/register', data={
        'email': email,
        'username': username,
        'password': password,
        'confirm_password': confirm_password,
        'full_name': full_name,
    }, follow_redirects=True)


def login_user(client, email='test@example.com', password='password123'):
    """Helper to login a user."""
    return client.post('/auth/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=True)
