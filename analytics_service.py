"""Skillora Analytics Service.

Provides calculations and aggregation for progress tracking, skill gap analysis,
career readiness metrics, roadmap completion, and assessment history.

Strict rules:
- All metrics are computed from real, persisted application data.
- Never invent historical records, fake progress trends, or sample achievements.
- Unassessed skills are NEVER plotted or interpreted as zero proficiency.
- Task completion updates roadmap progress ONLY; never alters proficiency or readiness.
- Separate calculation of career readiness and assessment coverage.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import sqlite3

from assessment_engine import calculate_career_readiness, PROFICIENCY_LEVELS


def get_user_analytics_data(db: sqlite3.Connection, user_id: int) -> Dict[str, Any]:
    """Compile comprehensive analytics, chart datasets, and progress metrics for a user.

    Args:
        db: SQLite database connection.
        user_id: Authenticated user ID.

    Returns:
        dict: Full analytics structure or empty-state descriptor.
    """
    # 1. Fetch active career selection
    active_career = db.execute(
        """
        SELECT cs.career_id, cs.career_path, c.id as cid, c.code, c.title, c.icon, c.description
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ? AND cs.is_active = 1
        ORDER BY cs.selected_at DESC, cs.id DESC LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    if not active_career or not active_career['cid']:
        return {
            'has_active_career': False,
            'career': None,
            'skills_data': [],
            'readiness': None,
            'roadmap': None,
            'history': [],
            'chart_data': {
                'skills': {'labels': [], 'targets': [], 'currents': [], 'assessed_flags': []},
                'roadmap_stages': {'labels': [], 'completed': [], 'total': []},
                'history_timeline': {'labels': [], 'scores': [], 'proficiencies': []}
            }
        }

    career_id = active_career['cid']

    # 2. Skill requirements, target levels, and user estimates
    skill_rows = db.execute(
        """
        SELECT s.id as skill_id, s.code as skill_code, s.name as skill_name, s.category,
               csr.target_level, csr.importance_weight, csr.is_core,
               use.current_estimate, use.quiz_proficiency, use.self_assessed_level,
               use.updated_at as last_assessed_at
        FROM career_skill_requirements csr
        JOIN skills s ON csr.skill_id = s.id
        LEFT JOIN user_skill_estimates use ON (csr.skill_id = use.skill_id AND use.user_id = ?)
        WHERE csr.career_id = ?
        ORDER BY csr.is_core DESC, csr.importance_weight DESC, s.name ASC
        """,
        (user_id, career_id)
    ).fetchall()

    skills_data = []
    reqs_for_readiness = []
    user_estimates_dict = {}

    for row in skill_rows:
        sid = row['skill_id']
        target = row['target_level']
        weight = row['importance_weight']
        is_core = bool(row['is_core'])
        est = row['current_estimate']

        reqs_for_readiness.append({
            'skill_id': sid,
            'target_level': target,
            'importance_weight': weight,
            'is_core': 1 if is_core else 0,
            'skill_name': row['skill_name']
        })

        is_assessed = est is not None and est > 0
        if is_assessed:
            user_estimates_dict[sid] = est
            gap = max(0.0, round(target - est, 1))
            if est >= target:
                status = 'target_met'
            else:
                status = 'gap_exists'
        else:
            gap = None
            status = 'unassessed'

        skills_data.append({
            'skill_id': sid,
            'skill_code': row['skill_code'],
            'skill_name': row['skill_name'],
            'category': row['category'],
            'target_level': target,
            'importance_weight': weight,
            'is_core': is_core,
            'is_assessed': is_assessed,
            'current_estimate': est,
            'quiz_proficiency': row['quiz_proficiency'],
            'self_assessed_level': row['self_assessed_level'],
            'last_assessed_at': row['last_assessed_at'],
            'gap': gap,
            'status': status
        })

    # 3. Career readiness & assessment coverage calculation
    readiness = calculate_career_readiness(reqs_for_readiness, user_estimates_dict)

    # 4. Roadmap metrics & stage breakdown
    roadmap_row = db.execute(
        "SELECT id, title FROM roadmaps WHERE user_id = ? AND career_id = ? AND is_active = 1",
        (user_id, career_id)
    ).fetchone()

    roadmap_data = None
    if roadmap_row:
        roadmap_id = roadmap_row['id']
        tasks = db.execute(
            """
            SELECT stage, is_project, is_completed, title, completed_at
            FROM roadmap_tasks
            WHERE roadmap_id = ?
            ORDER BY recommended_order ASC
            """,
            (roadmap_id,)
        ).fetchall()

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t['is_completed'])
        overall_progress = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        stages = {
            'learn': {'title': 'Learn', 'total': 0, 'completed': 0, 'progress': 0},
            'practice': {'title': 'Practice', 'total': 0, 'completed': 0, 'progress': 0},
            'build': {'title': 'Build', 'total': 0, 'completed': 0, 'progress': 0},
            'review': {'title': 'Review', 'total': 0, 'completed': 0, 'progress': 0},
        }

        completed_projects = []
        for t in tasks:
            st = t['stage']
            if st in stages:
                stages[st]['total'] += 1
                if t['is_completed']:
                    stages[st]['completed'] += 1
            if t['is_project'] and t['is_completed']:
                completed_projects.append({
                    'title': t['title'],
                    'completed_at': t['completed_at']
                })

        for st in stages:
            tot = stages[st]['total']
            cmp = stages[st]['completed']
            stages[st]['progress'] = round((cmp / tot * 100)) if tot > 0 else 0

        roadmap_data = {
            'roadmap_id': roadmap_id,
            'title': roadmap_row['title'],
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overall_progress': overall_progress,
            'stages': stages,
            'completed_projects': completed_projects
        }

    # 5. Completed assessment history (Strictly real completed attempts, ordered chronologically)
    history_rows = db.execute(
        """
        SELECT aa.id, aa.skill_id, s.name as skill_name, s.code as skill_code,
               aa.total_questions, aa.correct_count, aa.score_percentage,
               aa.quiz_proficiency, aa.self_assessed_level, aa.combined_estimate,
               aa.has_discrepancy, aa.discrepancy_message, aa.completed_at
        FROM assessment_attempts aa
        JOIN skills s ON aa.skill_id = s.id
        WHERE aa.user_id = ? AND aa.status = 'completed'
        ORDER BY aa.completed_at ASC, aa.id ASC
        """,
        (user_id,)
    ).fetchall()

    history = []
    for h in history_rows:
        history.append({
            'attempt_id': h['id'],
            'skill_id': h['skill_id'],
            'skill_name': h['skill_name'],
            'skill_code': h['skill_code'],
            'total_questions': h['total_questions'],
            'correct_count': h['correct_count'],
            'score_percentage': round(h['score_percentage'], 1),
            'quiz_proficiency': h['quiz_proficiency'],
            'self_assessed_level': h['self_assessed_level'],
            'combined_estimate': round(h['combined_estimate'], 2) if h['combined_estimate'] is not None else None,
            'has_discrepancy': bool(h['has_discrepancy']),
            'discrepancy_message': h['discrepancy_message'],
            'completed_at': h['completed_at']
        })

    # 6. Prepare Chart-ready data structures
    # A. Skill proficiency comparison (Target vs Current)
    # Assessed skills have float values; unassessed skills have None (null in JSON) so they are NOT plotted as 0!
    skill_chart_labels = []
    skill_chart_targets = []
    skill_chart_currents = []
    skill_chart_assessed = []

    for item in skills_data:
        skill_chart_labels.append(item['skill_name'])
        skill_chart_targets.append(item['target_level'])
        if item['is_assessed']:
            skill_chart_currents.append(round(item['current_estimate'], 1))
            skill_chart_assessed.append(True)
        else:
            skill_chart_currents.append(None)  # None renders as null in JSON; skips plotting zero
            skill_chart_assessed.append(False)

    # B. Roadmap stage chart data
    stage_labels = []
    stage_completed = []
    stage_total = []
    if roadmap_data:
        for sk in ['learn', 'practice', 'build', 'review']:
            s_info = roadmap_data['stages'][sk]
            stage_labels.append(s_info['title'])
            stage_completed.append(s_info['completed'])
            stage_total.append(s_info['total'])

    # C. Assessment score timeline (only if real history exists)
    history_dates = []
    history_scores = []
    history_proficiencies = []
    history_labels = []

    for h in history:
        # Format date for readability
        dt_str = h['completed_at'][:10] if h['completed_at'] else 'N/A'
        history_labels.append(f"{h['skill_name']} ({dt_str})")
        history_dates.append(dt_str)
        history_scores.append(h['score_percentage'])
        history_proficiencies.append(h['quiz_proficiency'])

    has_timeline_trend = len(history) >= 2

    return {
        'has_active_career': True,
        'career': active_career,
        'skills_data': skills_data,
        'readiness': readiness,
        'roadmap': roadmap_data,
        'history': history,
        'has_timeline_trend': has_timeline_trend,
        'total_assessments_count': len(history),
        'chart_data': {
            'skills': {
                'labels': skill_chart_labels,
                'targets': skill_chart_targets,
                'currents': skill_chart_currents,
                'assessed_flags': skill_chart_assessed
            },
            'roadmap_stages': {
                'labels': stage_labels,
                'completed': stage_completed,
                'total': stage_total
            },
            'history_timeline': {
                'labels': history_labels,
                'dates': history_dates,
                'scores': history_scores,
                'proficiencies': history_proficiencies
            }
        }
    }


def generate_dated_progress_report(db: sqlite3.Connection, user_id: int) -> Dict[str, Any]:
    """Generate a clean, structured progress report snapshot as of the current timestamp.

    Args:
        db: SQLite database connection.
        user_id: Authenticated user ID.

    Returns:
        dict: Dated report summary.
    """
    analytics = get_user_analytics_data(db, user_id)
    user_row = db.execute("SELECT id, username, full_name, email FROM users WHERE id = ?", (user_id,)).fetchone()

    report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Priority focus gaps
    priority_gaps = []
    if analytics['has_active_career']:
        for s in analytics['skills_data']:
            if s['status'] == 'gap_exists':
                priority_gaps.append(s)
            elif s['status'] == 'unassessed' and s['is_core']:
                priority_gaps.append(s)

    return {
        'generated_at': report_date,
        'user': user_row,
        'analytics': analytics,
        'priority_gaps': priority_gaps
    }
