"""Automated test suite for Milestone 3: Assessment Engine."""

import pytest
from db import get_db
from seeds import seed_careers_and_skills
from tests.conftest import register_user, login_user
from assessment_engine import (
    map_score_to_proficiency,
    calculate_combined_estimate,
    check_discrepancy,
    calculate_career_readiness,
)


class TestScoringEngineUnit:
    """Unit tests for the mathematical scoring engine and business rules."""

    def test_quiz_percentage_to_proficiency_boundaries(self):
        """Test the documented boundary mappings to 1-5 proficiency scale.
        
        0% <= score < 40%  -> Level 1 (Novice)
        40% <= score < 60% -> Level 2 (Advanced Beginner)
        60% <= score < 75% -> Level 3 (Competent)
        75% <= score < 90% -> Level 4 (Proficient)
        90% <= score <= 100% -> Level 5 (Expert)
        """
        # Level 1 boundaries
        assert map_score_to_proficiency(0.0) == 1
        assert map_score_to_proficiency(20.0) == 1
        assert map_score_to_proficiency(39.9) == 1

        # Level 2 boundaries
        assert map_score_to_proficiency(40.0) == 2
        assert map_score_to_proficiency(50.0) == 2
        assert map_score_to_proficiency(59.9) == 2

        # Level 3 boundaries
        assert map_score_to_proficiency(60.0) == 3
        assert map_score_to_proficiency(70.0) == 3
        assert map_score_to_proficiency(74.9) == 3

        # Level 4 boundaries
        assert map_score_to_proficiency(75.0) == 4
        assert map_score_to_proficiency(80.0) == 4
        assert map_score_to_proficiency(89.9) == 4

        # Level 5 boundaries
        assert map_score_to_proficiency(90.0) == 5
        assert map_score_to_proficiency(95.0) == 5
        assert map_score_to_proficiency(100.0) == 5

    def test_invalid_percentage_raises(self):
        """Invalid percentages outside [0, 100] raise ValueError."""
        with pytest.raises(ValueError):
            map_score_to_proficiency(-1.0)

        with pytest.raises(ValueError):
            map_score_to_proficiency(100.1)

        with pytest.raises(ValueError):
            map_score_to_proficiency(None)

    def test_combined_estimate_formula(self):
        """Test S = 0.7Q + 0.3A exact calculation."""
        # Q = 4, A = 2: 0.7*4 + 0.3*2 = 2.8 + 0.6 = 3.4
        assert calculate_combined_estimate(4, 2) == 3.4

        # Q = 5, A = 5: 0.7*5 + 0.3*5 = 3.5 + 1.5 = 5.0
        assert calculate_combined_estimate(5, 5) == 5.0

        # Q = 1, A = 1: 0.7*1 + 0.3*1 = 0.7 + 0.3 = 1.0
        assert calculate_combined_estimate(1, 1) == 1.0

        # Q = 3, A = 4: 0.7*3 + 0.3*4 = 2.1 + 1.2 = 3.3
        assert calculate_combined_estimate(3, 4) == 3.3

    def test_combined_estimate_missing_data_not_zero(self):
        """Missing data or Level 0 must return None and NOT silently substitute zero."""
        # None inputs
        assert calculate_combined_estimate(None, 3) is None
        assert calculate_combined_estimate(3, None) is None
        assert calculate_combined_estimate(None, None) is None

        # Level 0 (unassessed)
        assert calculate_combined_estimate(0, 3) is None
        assert calculate_combined_estimate(3, 0) is None
        assert calculate_combined_estimate(0, 0) is None

        # Out-of-bounds levels
        assert calculate_combined_estimate(6, 3) is None
        assert calculate_combined_estimate(3, 6) is None

    def test_discrepancy_detection_cases(self):
        """Test discrepancy detection at < 2, == 2, and > 2."""
        # Difference < 2: No discrepancy
        has_disc, msg = check_discrepancy(3, 3)
        assert has_disc is False

        has_disc, msg = check_discrepancy(3, 2)
        assert has_disc is False

        has_disc, msg = check_discrepancy(2, 3)
        assert has_disc is False

        # Difference == 2: Discrepancy flagged
        has_disc, msg = check_discrepancy(4, 2)
        assert has_disc is True
        assert "|Q - A| = 2" in msg
        assert "stronger than you thought" in msg.lower()

        has_disc, msg = check_discrepancy(2, 4)
        assert has_disc is True
        assert "|Q - A| = 2" in msg
        assert "foundational" in msg.lower()

        # Difference > 2: Discrepancy flagged
        has_disc, msg = check_discrepancy(5, 2)
        assert has_disc is True
        assert "|Q - A| = 3" in msg

        has_disc, msg = check_discrepancy(1, 5)
        assert has_disc is True
        assert "|Q - A| = 4" in msg

        # Incomplete data: No discrepancy
        has_disc, msg = check_discrepancy(None, 3)
        assert has_disc is False

    def test_career_readiness_and_coverage_logic(self):
        """Test importance-weighted readiness, capped target attainment, and provisional coverage."""
        requirements = [
            {'skill_id': 1, 'skill_name': 'HTML/CSS', 'target_level': 4, 'importance_weight': 3.0, 'is_core': 1},
            {'skill_id': 2, 'skill_name': 'JavaScript', 'target_level': 4, 'importance_weight': 3.0, 'is_core': 1},
            {'skill_id': 3, 'skill_name': 'Git', 'target_level': 3, 'importance_weight': 2.0, 'is_core': 0},
            {'skill_id': 4, 'skill_name': 'Performance', 'target_level': 3, 'importance_weight': 2.0, 'is_core': 0},
        ]
        # Total weight = 3.0 + 3.0 + 2.0 + 2.0 = 10.0

        # Scenario 1: No skills assessed -> coverage 0%, provisional, readiness 0%
        res0 = calculate_career_readiness(requirements, {})
        assert res0['coverage_percentage'] == 0.0
        assert res0['readiness_score'] == 0.0
        assert res0['is_provisional'] is True
        assert res0['assessed_skills_count'] == 0

        # Scenario 2: Assess skill 1 only (weight 3.0 out of 10.0 = 30% coverage)
        # Target = 4, Estimate = 4 -> Attainment = 4/4 = 1.0 (100%)
        # Coverage is 30% (< 70%), so is_provisional = True
        res1 = calculate_career_readiness(requirements, {1: 4.0})
        assert res1['coverage_percentage'] == 30.0
        assert res1['readiness_score'] == 100.0  # 100% attainment on assessed skill
        assert res1['is_provisional'] is True

        # Scenario 3: Capped attainment (Estimate exceeds target)
        # Target = 3, Estimate = 5 -> Attainment capped at min(1.0, 5/3) = 1.0
        res_capped = calculate_career_readiness(requirements, {3: 5.0})
        assert res_capped['breakdown'][2]['attainment_ratio'] == 1.0

        # Scenario 4: Partial attainment & reach >= 70% coverage (verified, definitive)
        # Assess skill 1 (weight 3.0, target 4, estimate 2 -> attainment 0.5)
        # Assess skill 2 (weight 3.0, target 4, estimate 4 -> attainment 1.0)
        # Assess skill 3 (weight 2.0, target 3, estimate 3 -> attainment 1.0)
        # Assessed weight = 3.0 + 3.0 + 2.0 = 8.0 out of 10.0 -> Coverage = 80.0% (>= 70%)
        # Weighted attainment = 3.0*0.5 + 3.0*1.0 + 2.0*1.0 = 1.5 + 3.0 + 2.0 = 6.5
        # Readiness = 6.5 / 8.0 * 100 = 81.25 -> rounded to 81.2% or 81.3%
        res4 = calculate_career_readiness(requirements, {1: 2.0, 2: 4.0, 3: 3.0})
        assert res4['coverage_percentage'] == 80.0
        assert res4['is_provisional'] is False  # Definitive!
        assert round(res4['readiness_score'], 1) == 81.2


class TestAssessmentRoutesAndFlow:
    """Integration tests for assessment routes and end-to-end flows."""

    def test_assessment_overview_requires_login(self, client):
        """Unauthenticated access to /assessment/ redirects to login."""
        response = client.get('/assessment/')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_assessment_overview_with_active_career(self, client, app):
        """Authenticated user sees skills and status for active career."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="ass_user@example.com", username="assuser")
        login_user(client, email="ass_user@example.com")

        # Select Frontend Developer
        client.post('/careers/select', data={'career_id': '1'}, follow_redirects=True)

        resp = client.get('/assessment/')
        assert resp.status_code == 200
        assert b'Skill Assessments' in resp.data
        assert b'Frontend Developer' in resp.data
        assert b'HTML5 &amp; Modern CSS' in resp.data
        assert b'JavaScript' in resp.data

    def test_take_assessment_page_loads_questions(self, client, app):
        """GET /assessment/<skill_code> displays questions without leaking correct answers."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="quiz_taker@example.com", username="quiztaker")
        login_user(client, email="quiz_taker@example.com")

        resp = client.get('/assessment/html-css')
        assert resp.status_code == 200
        assert b'HTML5 &amp; Modern CSS Assessment' in resp.data
        assert b'Step 1: Self-Assessment Rating' in resp.data
        assert b'Step 2: Technical Questions' in resp.data
        assert b'grid-based layout container' in resp.data

    def test_successful_quiz_submission_updates_estimate_and_saves_history(self, client, app):
        """Submitting valid quiz answers scores correctly, computes S, and updates current estimate."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="perfect_scorer@example.com", username="perfectscorer")
        login_user(client, email="perfect_scorer@example.com")

        # Frontend: html-css has 4 questions (Q1: B, Q2: B, Q3: B, Q4: B)
        with app.app_context():
            db = get_db()
            q_rows = db.execute(
                "SELECT q.id, q.correct_option FROM questions q JOIN skills s ON q.skill_id = s.id WHERE s.code = 'html-css' ORDER BY q.id"
            ).fetchall()

        form_data = {
            'self_assessed_level': '4',
        }
        # Answer all 4 correctly
        for q in q_rows:
            form_data[f'question_{q["id"]}'] = q['correct_option']

        resp = client.post('/assessment/html-css', data=form_data, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Assessment for HTML5 &amp; Modern CSS completed successfully!' in resp.data
        assert b'100.0%' in resp.data or b'100%' in resp.data
        # 100% -> Level 5. Self-assessed = 4.
        # Combined S = 0.7 * 5 + 0.3 * 4 = 3.5 + 1.2 = 4.7
        assert b'Level 5' in resp.data
        assert b'4.7' in resp.data

        # Verify database persistence
        with app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'perfect_scorer@example.com'").fetchone()
            skill = db.execute("SELECT id FROM skills WHERE code = 'html-css'").fetchone()

            # Verify attempt record
            attempt = db.execute(
                "SELECT * FROM assessment_attempts WHERE user_id = ? AND skill_id = ?",
                (user['id'], skill['id'])
            ).fetchone()
            assert attempt is not None
            assert attempt['score_percentage'] == 100.0
            assert attempt['quiz_proficiency'] == 5
            assert attempt['self_assessed_level'] == 4
            assert attempt['combined_estimate'] == 4.7
            assert attempt['has_discrepancy'] == 0

            # Verify current estimate record
            curr = db.execute(
                "SELECT * FROM user_skill_estimates WHERE user_id = ? AND skill_id = ?",
                (user['id'], skill['id'])
            ).fetchone()
            assert curr is not None
            assert curr['quiz_proficiency'] == 5
            assert curr['current_estimate'] == 4.7

    def test_reassessment_updates_current_estimate_preserving_history(self, client, app):
        """Reassessing a skill updates current_estimate and keeps both attempt records in history."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="reassessor@example.com", username="reassessor")
        login_user(client, email="reassessor@example.com")

        with app.app_context():
            db = get_db()
            q_rows = db.execute(
                "SELECT q.id, q.correct_option FROM questions q JOIN skills s ON q.skill_id = s.id WHERE s.code = 'html-css' ORDER BY q.id"
            ).fetchall()

        # Attempt 1: Score 0% (choose wrong answer 'D' for all)
        data1 = {'self_assessed_level': '2'}
        for q in q_rows:
            data1[f'question_{q["id"]}'] = 'D' if q['correct_option'] != 'D' else 'A'
        client.post('/assessment/html-css', data=data1, follow_redirects=True)

        with app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'reassessor@example.com'").fetchone()
            skill = db.execute("SELECT id FROM skills WHERE code = 'html-css'").fetchone()

            # Attempt 1 should map 0% to Level 1. S = 0.7*1 + 0.3*2 = 1.3
            curr1 = db.execute(
                "SELECT * FROM user_skill_estimates WHERE user_id = ? AND skill_id = ?",
                (user['id'], skill['id'])
            ).fetchone()
            assert curr1['quiz_proficiency'] == 1
            assert curr1['current_estimate'] == 1.3

        # Attempt 2: Reassess with 100% correct answers
        data2 = {'self_assessed_level': '4'}
        for q in q_rows:
            data2[f'question_{q["id"]}'] = q['correct_option']
        client.post('/assessment/html-css', data=data2, follow_redirects=True)

        with app.app_context():
            db = get_db()
            # Verify both attempts exist in history
            attempts = db.execute(
                "SELECT id, score_percentage, quiz_proficiency FROM assessment_attempts WHERE user_id = ? AND skill_id = ? ORDER BY id ASC",
                (user['id'], skill['id'])
            ).fetchall()
            assert len(attempts) == 2
            assert attempts[0]['score_percentage'] == 0.0
            assert attempts[1]['score_percentage'] == 100.0

            # Current estimate updated to latest attempt (Level 5, S = 4.7)
            curr2 = db.execute(
                "SELECT * FROM user_skill_estimates WHERE user_id = ? AND skill_id = ?",
                (user['id'], skill['id'])
            ).fetchone()
            assert curr2['quiz_proficiency'] == 5
            assert curr2['current_estimate'] == 4.7

    def test_incomplete_assessment_rejected_without_updating_estimate(self, client, app):
        """Unanswered questions reject submission and must NOT update user estimates."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="incompleter@example.com", username="incompleter")
        login_user(client, email="incompleter@example.com")

        # Submit with missing questions
        resp = client.post('/assessment/html-css', data={'self_assessed_level': '3'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b'unanswered' in resp.data.lower()

        # Verify no attempt or estimate was stored
        with app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'incompleter@example.com'").fetchone()
            skill = db.execute("SELECT id FROM skills WHERE code = 'html-css'").fetchone()

            attempts_count = db.execute(
                "SELECT COUNT(*) as cnt FROM assessment_attempts WHERE user_id = ?",
                (user['id'],)
            ).fetchone()['cnt']
            assert attempts_count == 0

            estimate = db.execute(
                "SELECT * FROM user_skill_estimates WHERE user_id = ?",
                (user['id'],)
            ).fetchone()
            assert estimate is None

    def test_assessment_one_skill_does_not_modify_another(self, client, app):
        """Assessing Skill A leaves Skill B completely unassessed."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="isolation_skill@example.com", username="isolationskill")
        login_user(client, email="isolation_skill@example.com")

        with app.app_context():
            db = get_db()
            q_rows = db.execute(
                "SELECT q.id, q.correct_option FROM questions q JOIN skills s ON q.skill_id = s.id WHERE s.code = 'html-css'"
            ).fetchall()

        form_data = {'self_assessed_level': '3'}
        for q in q_rows:
            form_data[f'question_{q["id"]}'] = q['correct_option']

        client.post('/assessment/html-css', data=form_data, follow_redirects=True)

        with app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'isolation_skill@example.com'").fetchone()
            js_skill = db.execute("SELECT id FROM skills WHERE code = 'javascript'").fetchone()

            js_estimate = db.execute(
                "SELECT * FROM user_skill_estimates WHERE user_id = ? AND skill_id = ?",
                (user['id'], js_skill['id'])
            ).fetchone()
            assert js_estimate is None

    def test_user_isolation_on_assessment_attempts(self, client, app):
        """User A cannot access or view User B's assessment attempt results."""
        with app.app_context():
            seed_careers_and_skills()

        # User A registers and completes an assessment
        register_user(client, email="user_alice@example.com", username="useralice")
        login_user(client, email="user_alice@example.com")

        with app.app_context():
            db = get_db()
            q_rows = db.execute(
                "SELECT q.id, q.correct_option FROM questions q JOIN skills s ON q.skill_id = s.id WHERE s.code = 'git'"
            ).fetchall()

        data_a = {'self_assessed_level': '3'}
        for q in q_rows:
            data_a[f'question_{q["id"]}'] = q['correct_option']
        client.post('/assessment/git', data=data_a, follow_redirects=True)

        with app.app_context():
            db = get_db()
            alice = db.execute("SELECT id FROM users WHERE email = 'user_alice@example.com'").fetchone()
            alice_attempt = db.execute(
                "SELECT id FROM assessment_attempts WHERE user_id = ?",
                (alice['id'],)
            ).fetchone()
            alice_attempt_id = alice_attempt['id']

        client.get('/auth/logout')

        # User B logs in and tries to view Alice's attempt
        register_user(client, email="user_bob@example.com", username="userbob")
        login_user(client, email="user_bob@example.com")

        bob_resp = client.get(f'/assessment/attempt/{alice_attempt_id}')
        # Must return 403 Forbidden
        assert bob_resp.status_code == 403
