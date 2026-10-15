"""Skillora Roadmap Blueprint.

Routes and controllers for:
- Viewing the user's personalized 4-stage learning roadmap (Learn -> Practice -> Build -> Review).
- Tracking task completion and reopening completed tasks.
- Refreshing/regenerating roadmap recommendations based on updated assessment scores.
- Informative empty states when no career is selected.
"""

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for, abort

from auth import login_required
from db import get_db
from roadmap_service import (
    get_user_active_roadmap,
    toggle_task_completion,
    generate_roadmap_for_user
)

bp = Blueprint('roadmap', __name__, url_prefix='/roadmap')


@bp.route('/')
@login_required
def index():
    """View the personalized learning roadmap for the authenticated user's active career."""
    db = get_db()
    roadmap_data = get_user_active_roadmap(db, g.user['id'])

    # If user has an active career selection but no career id mapped
    active_career = db.execute(
        """
        SELECT cs.career_id, cs.career_path, c.id as cid, c.title
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ? AND cs.is_active = 1
        ORDER BY cs.selected_at DESC, cs.id DESC LIMIT 1
        """,
        (g.user['id'],)
    ).fetchone()

    return render_template(
        'roadmap/index.html',
        roadmap=roadmap_data,
        active_career=active_career
    )


@bp.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle a task between completed and incomplete.

    Strict rule: Task completion updates roadmap progress ONLY.
    Never alters skill proficiency or career readiness.
    """
    db = get_db()
    try:
        updated = toggle_task_completion(db, g.user['id'], task_id)
    except PermissionError:
        abort(403)
    except ValueError:
        abort(404)

    # Check if request is JSON / AJAX
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'task': updated
        })

    status_str = "completed" if updated['is_completed'] else "reopened"
    flash(f"Task marked as {status_str}: {updated['title']}", "success")
    return redirect(request.referrer or url_for('roadmap.index'))


@bp.route('/regenerate', methods=['POST'])
@login_required
def regenerate():
    """Regenerate the active roadmap to reflect updated assessment estimates.

    Preserves completed task records while re-evaluating remaining skill gaps.
    """
    db = get_db()
    active_career = db.execute(
        """
        SELECT cs.career_id, c.id as cid, c.title
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ? AND cs.is_active = 1
        ORDER BY cs.selected_at DESC, cs.id DESC LIMIT 1
        """,
        (g.user['id'],)
    ).fetchone()

    if not active_career or not active_career['cid']:
        flash("Please select a target career before generating a roadmap.", "error")
        return redirect(url_for('main.careers'))

    career_id = active_career['cid']
    generate_roadmap_for_user(db, g.user['id'], career_id, refresh=True)
    flash("Roadmap refreshed with your latest skill assessment insights! Your completed tasks were preserved.", "success")
    return redirect(url_for('roadmap.index'))
