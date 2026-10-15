"""Skillora Progress & Analytics Blueprint.

Routes and controllers for:
- Viewing the Progress Tracking & Analytics dashboard with interactive Chart.js visualizations.
- Inspecting skill proficiency vs target levels (unassessed clearly distinguished).
- Viewing roadmap completion breakdown by stage (Learn, Practice, Build, Review).
- Reviewing chronological assessment attempt history without fake data.
- Generating a dated, printable career readiness progress report.
"""

from flask import Blueprint, render_template, jsonify, g, request, abort

from auth import login_required
from db import get_db
from analytics_service import get_user_analytics_data, generate_dated_progress_report

bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@bp.route('/')
@login_required
def index():
    """Main Progress & Analytics dashboard view."""
    db = get_db()
    analytics_data = get_user_analytics_data(db, g.user['id'])

    return render_template(
        'analytics/index.html',
        data=analytics_data
    )


@bp.route('/report')
@login_required
def report():
    """Printable / formatted dated career-readiness progress report."""
    db = get_db()
    report_data = generate_dated_progress_report(db, g.user['id'])

    return render_template(
        'analytics/report.html',
        report=report_data
    )


@bp.route('/data')
@login_required
def chart_data():
    """API endpoint providing serialized chart data for client-side rendering."""
    db = get_db()
    analytics_data = get_user_analytics_data(db, g.user['id'])

    return jsonify({
        'success': True,
        'has_active_career': analytics_data['has_active_career'],
        'chart_data': analytics_data['chart_data'],
        'readiness': analytics_data['readiness'],
        'roadmap': analytics_data['roadmap'],
    })
