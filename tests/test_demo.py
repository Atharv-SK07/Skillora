from db import get_db


class TestDemoAccess:
    """Test demo/judge access."""

    def test_demo_creates_user_and_logs_in(self, client, app):
        """Demo route creates demo user and logs in."""
        response = client.get('/demo')
        assert response.status_code == 302  # Redirect to dashboard

        # Verify demo user was created
        with app.app_context():
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE email = ?', ('demo@skillora.app',)).fetchone()
            assert user is not None
            assert user['is_demo_account'] == 1
            assert user['username'] == 'demo_user'

    def test_demo_is_idempotent(self, client, app):
        """Multiple demo accesses don't create duplicate users."""
        client.get('/demo')
        client.get('/auth/logout')
        client.get('/demo')

        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(*) as cnt FROM users WHERE email = ?', ('demo@skillora.app',)).fetchone()
            assert count['cnt'] == 1

    def test_demo_accesses_dashboard(self, client):
        """After demo login, dashboard is accessible."""
        client.get('/demo')  # Login via demo
        response = client.get('/dashboard')
        assert response.status_code == 200
