"""Main routes blueprint for Skillora."""

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from auth import login_required
from db import get_db

bp = Blueprint('main', __name__)

# Demo account credentials — predictable and safe for judge access
DEMO_EMAIL = 'demo@skillora.app'
DEMO_USERNAME = 'demo_user'
DEMO_FULL_NAME = 'Demo User'
DEMO_PASSWORD = 'demo_password_2024'


# ---------------------------------------------------------------------------
# Route: Landing page
# ---------------------------------------------------------------------------

@bp.route('/')
def landing():
    """Landing page — redirects authenticated users to dashboard."""
    if g.user:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')


# ---------------------------------------------------------------------------
# Route: Dashboard (protected)
# ---------------------------------------------------------------------------

@bp.route('/dashboard')
@login_required
def dashboard():
    """Authenticated user dashboard with honest states and readiness calculations."""
    db = get_db()
    career = db.execute(
        '''
        SELECT cs.career_path, cs.career_id, c.id as cid, c.code, c.icon, c.description
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ? AND cs.is_active = 1
        ORDER BY cs.selected_at DESC, cs.id DESC LIMIT 1
        ''',
        (g.user['id'],)
    ).fetchone()

    readiness = None
    if career and career['cid']:
        from assessment_engine import calculate_career_readiness
        reqs = db.execute(
            '''
            SELECT csr.skill_id, csr.target_level, csr.importance_weight, csr.is_core,
                   use.current_estimate
            FROM career_skill_requirements csr
            LEFT JOIN user_skill_estimates use ON (csr.skill_id = use.skill_id AND use.user_id = ?)
            WHERE csr.career_id = ?
            ''',
            (g.user['id'], career['cid'])
        ).fetchall()

        requirements_list = []
        user_estimates = {}
        for r in reqs:
            requirements_list.append({
                'skill_id': r['skill_id'],
                'target_level': r['target_level'],
                'importance_weight': r['importance_weight'],
                'is_core': r['is_core']
            })
            if r['current_estimate'] is not None and r['current_estimate'] > 0:
                user_estimates[r['skill_id']] = r['current_estimate']

        readiness = calculate_career_readiness(requirements_list, user_estimates)

    roadmap_data = None
    if career and career['cid']:
        from roadmap_service import get_user_active_roadmap
        roadmap_data = get_user_active_roadmap(db, g.user['id'])

    return render_template('dashboard.html', active_career=career, readiness=readiness, roadmap=roadmap_data)



# ---------------------------------------------------------------------------
# Route: Careers List & Overview (protected)
# ---------------------------------------------------------------------------

@bp.route('/careers')
@login_required
def careers():
    """Display the six supported career paths, skill counts, and user's current selection."""
    db = get_db()
    careers_list = db.execute(
        '''
        SELECT c.*,
               COUNT(csr.id) as skill_count,
               SUM(CASE WHEN csr.is_core = 1 THEN 1 ELSE 0 END) as core_skill_count
        FROM careers c
        LEFT JOIN career_skill_requirements csr ON c.id = csr.career_id
        GROUP BY c.id
        ORDER BY c.id ASC
        '''
    ).fetchall()

    current_selection = db.execute(
        '''
        SELECT cs.career_id, cs.career_path, c.code
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ? AND cs.is_active = 1
        ORDER BY cs.selected_at DESC, cs.id DESC LIMIT 1
        ''',
        (g.user['id'],)
    ).fetchone()

    # Get career history for the user
    history = db.execute(
        '''
        SELECT cs.id, cs.career_path, cs.selected_at, cs.is_active, c.icon
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ?
        ORDER BY cs.selected_at DESC, cs.id DESC
        ''',
        (g.user['id'],)
    ).fetchall()

    return render_template(
        'careers/index.html',
        careers=careers_list,
        current_selection=current_selection,
        history=history
    )


# ---------------------------------------------------------------------------
# Route: Career Detail / Skill Requirements (protected)
# ---------------------------------------------------------------------------

@bp.route('/careers/<career_code>')
@login_required
def career_detail(career_code):
    """View details of a specific career profile and its skill requirements."""
    db = get_db()
    career = db.execute(
        'SELECT * FROM careers WHERE code = ?',
        (career_code,)
    ).fetchone()

    if career is None:
        flash(f'Career "{career_code}" not found.', 'error')
        return redirect(url_for('main.careers'))

    requirements = db.execute(
        '''
        SELECT s.code as skill_code, s.name as skill_name, s.category, s.description,
               csr.target_level, csr.importance_weight, csr.is_core
        FROM career_skill_requirements csr
        JOIN skills s ON csr.skill_id = s.id
        WHERE csr.career_id = ?
        ORDER BY csr.is_core DESC, csr.importance_weight DESC, s.name ASC
        ''',
        (career['id'],)
    ).fetchall()

    is_current = db.execute(
        '''
        SELECT id FROM career_selections
        WHERE user_id = ? AND (career_id = ? OR career_path = ?) AND is_active = 1
        ''',
        (g.user['id'], career['id'], career['title'])
    ).fetchone() is not None

    return render_template(
        'careers/detail.html',
        career=career,
        requirements=requirements,
        is_current=is_current
    )


# ---------------------------------------------------------------------------
# Route: Select / Switch Career (protected, POST only)
# ---------------------------------------------------------------------------

@bp.route('/careers/select', methods=['POST'])
@login_required
def select_career():
    """Select or change the target career.
    
    Preserves historical selections by deactivating earlier entries (is_active = 0)
    rather than overwriting or deleting them.
    """
    career_id_raw = request.form.get('career_id')
    if not career_id_raw:
        flash('Please select a valid career path.', 'error')
        return redirect(url_for('main.careers'))

    try:
        career_id = int(career_id_raw)
    except ValueError:
        flash('Invalid career ID format.', 'error')
        return redirect(url_for('main.careers'))

    db = get_db()
    career = db.execute(
        'SELECT * FROM careers WHERE id = ?',
        (career_id,)
    ).fetchone()

    if career is None:
        flash('The selected career does not exist.', 'error')
        return redirect(url_for('main.careers'))

    # Check if already active
    active = db.execute(
        '''
        SELECT id FROM career_selections
        WHERE user_id = ? AND (career_id = ? OR career_path = ?) AND is_active = 1
        ''',
        (g.user['id'], career['id'], career['title'])
    ).fetchone()

    if active:
        flash(f'"{career["title"]}" is already your active career path.', 'info')
        return redirect(url_for('main.careers'))

    # Deactivate previous active selections to preserve history
    db.execute(
        'UPDATE career_selections SET is_active = 0 WHERE user_id = ? AND is_active = 1',
        (g.user['id'],)
    )

    # Insert new selection record with both foreign key and text title
    db.execute(
        '''
        INSERT INTO career_selections (user_id, career_id, career_path, is_active)
        VALUES (?, ?, ?, 1)
        ''',
        (g.user['id'], career['id'], career['title'])
    )
    db.commit()

    # Automatically activate or generate roadmap for newly selected career
    from roadmap_service import generate_roadmap_for_user
    generate_roadmap_for_user(db, g.user['id'], career['id'])

    flash(f'Target career set to "{career["title"]}"!', 'success')
    return redirect(url_for('main.careers'))



# ---------------------------------------------------------------------------
# Route: Demo / Judge access
# ---------------------------------------------------------------------------

@bp.route('/demo')
def demo_login():
    """Create or retrieve the demo account and log in automatically.

    Provides a predictable, safe entry point for hackathon judges.
    This route is idempotent — visiting it multiple times will not
    create duplicate accounts.
    """
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE email = ?', (DEMO_EMAIL,)
    ).fetchone()

    if user is None:
        db.execute(
            'INSERT INTO users (email, username, password_hash, full_name, is_demo_account) '
            'VALUES (?, ?, ?, ?, 1)',
            (DEMO_EMAIL, DEMO_USERNAME,
             generate_password_hash(DEMO_PASSWORD), DEMO_FULL_NAME),
        )
        db.commit()
        user = db.execute(
            'SELECT * FROM users WHERE email = ?', (DEMO_EMAIL,)
        ).fetchone()

    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    flash(f'Welcome to Skillora, {user["full_name"]}! This is a demo account.', 'info')
    return redirect(url_for('main.dashboard'))
