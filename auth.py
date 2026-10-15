"""Authentication blueprint for Skillora."""

import functools
import re

from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


# ---------------------------------------------------------------------------
# Before-request: load the logged-in user into g
# ---------------------------------------------------------------------------

@bp.before_app_request
def load_logged_in_user():
    """Load the current user from the session into g.user."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()


# ---------------------------------------------------------------------------
# Decorator: login_required
# ---------------------------------------------------------------------------

def login_required(view):
    """View decorator that redirects unauthenticated users to login."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


# ---------------------------------------------------------------------------
# Route: Register
# ---------------------------------------------------------------------------

@bp.route('/register', methods=('GET', 'POST'))
def register():
    """User registration."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()

        error = _validate_registration(email, username, password,
                                       confirm_password, full_name)

        if error is None:
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO users (email, username, password_hash, full_name) '
                    'VALUES (?, ?, ?, ?)',
                    (email, username, generate_password_hash(password), full_name),
                )
                db.commit()
            except db.IntegrityError:
                error = 'Email or username is already registered.'
            else:
                flash('Registration successful! Please sign in.', 'success')
                return redirect(url_for('auth.login'))

        flash(error, 'error')

    return render_template('auth/register.html')


def _validate_registration(email, username, password, confirm_password, full_name):
    """Validate registration form fields. Returns an error string or None."""
    if not full_name:
        return 'Full name is required.'
    if not email:
        return 'Email is required.'
    if '@' not in email or '.' not in email:
        return 'Please enter a valid email address.'
    if not username:
        return 'Username is required.'
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return ('Username must be 3–20 characters and contain only '
                'letters, numbers, and underscores.')
    if not password:
        return 'Password is required.'
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    if password != confirm_password:
        return 'Passwords do not match.'

    # Check uniqueness
    db = get_db()
    if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return 'This email is already registered.'
    if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return 'This username is already taken.'

    return None


# ---------------------------------------------------------------------------
# Route: Login
# ---------------------------------------------------------------------------

@bp.route('/login', methods=('GET', 'POST'))
def login():
    """User login."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html')

        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash(f'Welcome back, {user["full_name"]}!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


# ---------------------------------------------------------------------------
# Route: Logout
# ---------------------------------------------------------------------------

@bp.route('/logout')
def logout():
    """Log the user out."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
