"""Skillora Assessment Blueprint.

Routes and controllers for:
- Viewing available skill assessments for the user's active career.
- Taking skill-specific quizzes with self-assessment rating.
- Server-side answer validation, scoring, and proficiency mapping.
- Combined skill estimation: S = 0.7Q + 0.3A.
- Discrepancy flagging (|Q - A| >= 2) with constructive guidance.
- Updating current user estimates while preserving full attempt history.
- Reviewing past assessment attempts with question-by-question feedback.
"""

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, abort

from auth import login_required
from db import get_db
from assessment_engine import (
    map_score_to_proficiency,
    calculate_combined_estimate,
    check_discrepancy,
    calculate_career_readiness,
    PROFICIENCY_LEVELS,
)

bp = Blueprint('assessment', __name__, url_prefix='/assessment')


@bp.route('/')
@login_required
def index():
    """Overview of skill assessments for the user's active career."""
    db = get_db()

    # Get active career
    active_career = db.execute(
        '''
        SELECT cs.career_id, cs.career_path, c.id as cid, c.code, c.icon, c.description
        FROM career_selections cs
        LEFT JOIN careers c ON cs.career_id = c.id OR cs.career_path = c.title
        WHERE cs.user_id = ? AND cs.is_active = 1
        ORDER BY cs.selected_at DESC, cs.id DESC LIMIT 1
        ''',
        (g.user['id'],)
    ).fetchone()

    skills_data = []
    readiness_summary = None

    if active_career and active_career['cid']:
        career_id = active_career['cid']

        # Fetch required skills with question counts and user estimates
        reqs = db.execute(
            '''
            SELECT s.id as skill_id, s.code as skill_code, s.name as skill_name,
                   s.category, s.description as skill_description,
                   csr.target_level, csr.importance_weight, csr.is_core,
                   COUNT(DISTINCT q.id) as question_count,
                   use.quiz_proficiency, use.self_assessed_level,
                   use.current_estimate, use.last_attempt_id, use.updated_at as last_assessed_at,
                   COUNT(DISTINCT aa.id) as attempt_count
            FROM career_skill_requirements csr
            JOIN skills s ON csr.skill_id = s.id
            LEFT JOIN questions q ON s.id = q.skill_id
            LEFT JOIN user_skill_estimates use ON (s.id = use.skill_id AND use.user_id = ?)
            LEFT JOIN assessment_attempts aa ON (s.id = aa.skill_id AND aa.user_id = ? AND aa.status = 'completed')
            WHERE csr.career_id = ?
            GROUP BY s.id
            ORDER BY csr.is_core DESC, csr.importance_weight DESC, s.name ASC
            ''',
            (g.user['id'], g.user['id'], career_id)
        ).fetchall()

        # Build user estimates map for readiness calculation
        user_estimates = {}
        requirements_for_readiness = []

        for r in reqs:
            s_dict = dict(r)
            s_dict['proficiency_title'] = PROFICIENCY_LEVELS.get(r['quiz_proficiency'], 'Unassessed')
            skills_data.append(s_dict)

            requirements_for_readiness.append({
                'skill_id': r['skill_id'],
                'skill_name': r['skill_name'],
                'target_level': r['target_level'],
                'importance_weight': r['importance_weight'],
                'is_core': r['is_core']
            })

            if r['current_estimate'] is not None and r['current_estimate'] > 0:
                user_estimates[r['skill_id']] = r['current_estimate']

        # Calculate readiness & coverage
        readiness_summary = calculate_career_readiness(requirements_for_readiness, user_estimates)

    # Fetch recent attempts for the user
    recent_attempts = db.execute(
        '''
        SELECT aa.*, s.name as skill_name, s.code as skill_code
        FROM assessment_attempts aa
        JOIN skills s ON aa.skill_id = s.id
        WHERE aa.user_id = ?
        ORDER BY aa.completed_at DESC, aa.id DESC LIMIT 10
        ''',
        (g.user['id'],)
    ).fetchall()

    return render_template(
        'assessment/index.html',
        active_career=active_career,
        skills=skills_data,
        readiness=readiness_summary,
        recent_attempts=recent_attempts,
        proficiency_levels=PROFICIENCY_LEVELS
    )


@bp.route('/<skill_code>', methods=['GET', 'POST'])
@login_required
def take_assessment(skill_code):
    """Take a skill assessment quiz with self-assessment rating."""
    db = get_db()

    skill = db.execute(
        'SELECT * FROM skills WHERE code = ?',
        (skill_code,)
    ).fetchone()

    if skill is None:
        flash(f'Skill "{skill_code}" not found.', 'error')
        return redirect(url_for('assessment.index'))

    # Fetch questions for this skill
    questions = db.execute(
        'SELECT id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, difficulty_level '
        'FROM questions WHERE skill_id = ? ORDER BY id ASC',
        (skill['id'],)
    ).fetchall()

    # Get user's existing estimate if any
    current_estimate = db.execute(
        'SELECT * FROM user_skill_estimates WHERE user_id = ? AND skill_id = ?',
        (g.user['id'], skill['id'])
    ).fetchone()

    if request.method == 'POST':
        if not questions or len(questions) == 0:
            flash('No questions are available for this skill yet.', 'error')
            return redirect(url_for('assessment.index'))

        # 1. Parse and validate self-assessed level
        self_assessed_raw = request.form.get('self_assessed_level')
        self_assessed_level = None
        if self_assessed_raw:
            try:
                val = int(self_assessed_raw)
                if 1 <= val <= 5:
                    self_assessed_level = val
                else:
                    flash('Self-assessed level must be between 1 and 5.', 'error')
                    return redirect(url_for('assessment.take_assessment', skill_code=skill_code))
            except ValueError:
                flash('Invalid self-assessed level format.', 'error')
                return redirect(url_for('assessment.take_assessment', skill_code=skill_code))

        # 2. Check submitted answers
        submitted_answers = {}
        unanswered_count = 0

        for q in questions:
            q_id = q['id']
            ans = request.form.get(f'question_{q_id}')
            if not ans or ans not in ('A', 'B', 'C', 'D'):
                unanswered_count += 1
            else:
                submitted_answers[q_id] = ans

        # Business Rule: Incomplete or invalid assessment must NOT update proficiency
        if unanswered_count > 0:
            flash(f'Please answer all {len(questions)} questions to complete the assessment ({unanswered_count} unanswered).', 'error')
            return render_template(
                'assessment/take.html',
                skill=skill,
                questions=questions,
                current_estimate=current_estimate,
                selected_answers=submitted_answers,
                selected_self_assessed=self_assessed_level
            )

        # 3. Score the quiz
        total_questions = len(questions)
        correct_count = 0
        answer_records = []

        for q in questions:
            q_id = q['id']
            chosen = submitted_answers[q_id]
            is_correct = 1 if chosen == q['correct_option'] else 0
            if is_correct:
                correct_count += 1
            answer_records.append({
                'question_id': q_id,
                'selected_option': chosen,
                'is_correct': is_correct
            })

        score_percentage = round((correct_count / total_questions) * 100.0, 2)
        quiz_proficiency = map_score_to_proficiency(score_percentage)

        # 4. Calculate combined estimate: S = 0.7Q + 0.3A
        combined_estimate = calculate_combined_estimate(quiz_proficiency, self_assessed_level)

        # 5. Check discrepancy: |Q - A| >= 2
        has_disc, disc_msg = check_discrepancy(quiz_proficiency, self_assessed_level)
        has_disc_int = 1 if has_disc else 0

        # Effective estimate for current skill proficiency
        effective_estimate = combined_estimate if combined_estimate is not None else float(quiz_proficiency)

        # 6. Persist attempt
        cursor = db.execute(
            '''
            INSERT INTO assessment_attempts (
                user_id, skill_id, total_questions, correct_count, score_percentage,
                quiz_proficiency, self_assessed_level, combined_estimate,
                has_discrepancy, discrepancy_message, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')
            ''',
            (g.user['id'], skill['id'], total_questions, correct_count, score_percentage,
             quiz_proficiency, self_assessed_level, combined_estimate,
             has_disc_int, disc_msg)
        )
        attempt_id = cursor.lastrowid

        # 7. Persist individual question answers
        for ans_rec in answer_records:
            db.execute(
                '''
                INSERT INTO assessment_answers (attempt_id, question_id, selected_option, is_correct)
                VALUES (?, ?, ?, ?)
                ''',
                (attempt_id, ans_rec['question_id'], ans_rec['selected_option'], ans_rec['is_correct'])
            )

        # 8. Update current user skill estimate (upsert preserving history)
        db.execute(
            '''
            INSERT INTO user_skill_estimates (
                user_id, skill_id, quiz_proficiency, self_assessed_level,
                current_estimate, last_attempt_id, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, skill_id) DO UPDATE SET
                quiz_proficiency = excluded.quiz_proficiency,
                self_assessed_level = excluded.self_assessed_level,
                current_estimate = excluded.current_estimate,
                last_attempt_id = excluded.last_attempt_id,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (g.user['id'], skill['id'], quiz_proficiency, self_assessed_level,
             effective_estimate, attempt_id)
        )
        db.commit()

        flash(f'Assessment for {skill["name"]} completed successfully!', 'success')
        return redirect(url_for('assessment.view_attempt', attempt_id=attempt_id))

    return render_template(
        'assessment/take.html',
        skill=skill,
        questions=questions,
        current_estimate=current_estimate,
        selected_answers={},
        selected_self_assessed=None
    )


@bp.route('/attempt/<int:attempt_id>')
@login_required
def view_attempt(attempt_id):
    """View details, score, proficiency mapping, and answer breakdown of an assessment attempt."""
    db = get_db()

    attempt = db.execute(
        '''
        SELECT aa.*, s.name as skill_name, s.code as skill_code, s.category
        FROM assessment_attempts aa
        JOIN skills s ON aa.skill_id = s.id
        WHERE aa.id = ?
        ''',
        (attempt_id,)
    ).fetchone()

    if attempt is None:
        flash('Assessment attempt not found.', 'error')
        return redirect(url_for('assessment.index'))

    # User isolation: reject unauthorized access to other users' records
    if attempt['user_id'] != g.user['id']:
        abort(403)

    # Fetch answers with full question context
    answers = db.execute(
        '''
        SELECT an.selected_option, an.is_correct,
               q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
               q.correct_option, q.explanation
        FROM assessment_answers an
        JOIN questions q ON an.question_id = q.id
        WHERE an.attempt_id = ?
        ORDER BY an.id ASC
        ''',
        (attempt_id,)
    ).fetchall()

    return render_template(
        'assessment/result.html',
        attempt=attempt,
        answers=answers,
        proficiency_levels=PROFICIENCY_LEVELS
    )
