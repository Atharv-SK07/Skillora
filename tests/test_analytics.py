"""Tests for Milestone 5: Progress Tracking & Analytics."""

import pytest
from db import get_db
from seeds import seed_careers_and_skills
from analytics_service import get_user_analytics_data, generate_dated_progress_report
from roadmap_service import generate_roadmap_for_user, toggle_task_completion
from tests.conftest import register_user, login_user


@pytest.fixture
def seeded_app(app):
    """Fixture providing an app with seeded careers, skills, and test users."""
    with app.app_context():
        db = get_db()
        seed_careers_and_skills(db)
        db.execute("INSERT OR IGNORE INTO users (id, email, username, password_hash, full_name) VALUES (1, 'u1@test.com', 'user1', 'hash', 'User One')")
        db.execute("INSERT OR IGNORE INTO users (id, email, username, password_hash, full_name) VALUES (2, 'u2@test.com', 'user2', 'hash', 'User Two')")
        db.commit()
    return app


class TestAnalyticsServiceUnit:
    """Unit tests for analytics calculations and metrics derivation."""

    def test_user_without_career_returns_clean_empty_state(self, seeded_app):
        """User without active career returns has_active_career = False without errors."""
        with seeded_app.app_context():
            db = get_db()
            data = get_user_analytics_data(db, user_id=1)
            assert data['has_active_career'] is False
            assert data['career'] is None
            assert data['skills_data'] == []
            assert data['readiness'] is None

    def test_unassessed_skills_never_plotted_as_zero_proficiency(self, seeded_app):
        """CRITICAL: Unassessed skills have current_estimate None (not 0.0) in chart data."""
        with seeded_app.app_context():
            db = get_db()
            # Select Frontend Developer (id=1)
            db.execute("INSERT INTO career_selections (user_id, career_id, career_path, is_active) VALUES (1, 1, 'Frontend Developer', 1)")
            # Assess only skill_id 1 (html-css) with estimate 3.0
            db.execute("""
                INSERT INTO user_skill_estimates (user_id, skill_id, quiz_proficiency, self_assessed_level, current_estimate)
                VALUES (1, 1, 3, 3, 3.0)
            """)
            db.commit()

            data = get_user_analytics_data(db, user_id=1)
            assert data['has_active_career'] is True

            # In skills_data:
            assessed_item = next(s for s in data['skills_data'] if s['skill_id'] == 1)
            assert assessed_item['is_assessed'] is True
            assert assessed_item['current_estimate'] == 3.0

            unassessed_items = [s for s in data['skills_data'] if s['skill_id'] != 1]
            assert len(unassessed_items) > 0
            for u in unassessed_items:
                assert u['is_assessed'] is False
                assert u['current_estimate'] is None
                assert u['status'] == 'unassessed'

            # In chart_data, unassessed values are None (null in JSON), NOT 0
            chart_currents = data['chart_data']['skills']['currents']
            chart_assessed = data['chart_data']['skills']['assessed_flags']

            assert chart_currents[0] == 3.0
            assert chart_assessed[0] is True
            for val, is_ass in zip(chart_currents[1:], chart_assessed[1:]):
                assert is_ass is False
                assert val is None  # Never 0!

    def test_readiness_and_coverage_calculated_separately(self, seeded_app):
        """Readiness and coverage are separate; coverage < 70% flags provisional readiness."""
        with seeded_app.app_context():
            db = get_db()
            db.execute("INSERT INTO career_selections (user_id, career_id, career_path, is_active) VALUES (1, 1, 'Frontend Developer', 1)")
            # Assess 1 skill out of 7
            db.execute("""
                INSERT INTO user_skill_estimates (user_id, skill_id, quiz_proficiency, self_assessed_level, current_estimate)
                VALUES (1, 1, 4, 4, 4.0)
            """)
            db.commit()

            data = get_user_analytics_data(db, user_id=1)
            readiness = data['readiness']

            assert readiness is not None
            # Coverage is less than 70%
            assert readiness['coverage_percentage'] < 70.0
            assert readiness['is_provisional'] is True
            # Readiness score is computed across the assessed skill
            assert readiness['readiness_score'] > 0.0

    def test_assessment_history_uses_only_completed_attempts_no_fake_data(self, seeded_app):
        """Assessment history includes real completed attempts only; timeline requires >= 2 attempts."""
        with seeded_app.app_context():
            db = get_db()
            db.execute("INSERT INTO career_selections (user_id, career_id, career_path, is_active) VALUES (1, 1, 'Frontend Developer', 1)")

            # Check initially with 0 attempts
            data0 = get_user_analytics_data(db, user_id=1)
            assert len(data0['history']) == 0
            assert data0['has_timeline_trend'] is False

            # Add 1 completed attempt and 1 in_progress attempt
            db.execute("""
                INSERT INTO assessment_attempts (user_id, skill_id, total_questions, correct_count, score_percentage, quiz_proficiency, status, completed_at)
                VALUES (1, 1, 5, 4, 80.0, 4, 'completed', '2026-10-10 10:00:00')
            """)
            db.execute("""
                INSERT INTO assessment_attempts (user_id, skill_id, total_questions, correct_count, score_percentage, quiz_proficiency, status)
                VALUES (1, 2, 5, 0, 0.0, 1, 'in_progress')
            """)
            db.commit()

            data1 = get_user_analytics_data(db, user_id=1)
            assert len(data1['history']) == 1  # In_progress excluded!
            assert data1['has_timeline_trend'] is False  # 1 attempt is not enough for trend line

            # Add 2nd completed attempt
            db.execute("""
                INSERT INTO assessment_attempts (user_id, skill_id, total_questions, correct_count, score_percentage, quiz_proficiency, status, completed_at)
                VALUES (1, 2, 5, 5, 100.0, 5, 'completed', '2026-10-12 11:00:00')
            """)
            db.commit()

            data2 = get_user_analytics_data(db, user_id=1)
            assert len(data2['history']) == 2
            assert data2['has_timeline_trend'] is True
            assert len(data2['chart_data']['history_timeline']['scores']) == 2

    def test_task_completion_does_not_modify_proficiency_or_readiness(self, seeded_app):
        """CRITICAL: Completing roadmap tasks updates roadmap metrics only."""
        with seeded_app.app_context():
            db = get_db()
            db.execute("INSERT INTO career_selections (user_id, career_id, career_path, is_active) VALUES (1, 1, 'Frontend Developer', 1)")
            db.execute("""
                INSERT INTO user_skill_estimates (user_id, skill_id, quiz_proficiency, self_assessed_level, current_estimate)
                VALUES (1, 1, 3, 3, 3.0)
            """)
            db.commit()

            r_id = generate_roadmap_for_user(db, user_id=1, career_id=1)
            before = get_user_analytics_data(db, user_id=1)
            r_score_before = before['readiness']['readiness_score']
            est_before = before['skills_data'][0]['current_estimate']
            prog_before = before['roadmap']['overall_progress']

            # Mark all roadmap tasks completed
            tasks = db.execute("SELECT id FROM roadmap_tasks WHERE roadmap_id = ?", (r_id,)).fetchall()
            for t in tasks:
                toggle_task_completion(db, user_id=1, task_id=t['id'])

            after = get_user_analytics_data(db, user_id=1)
            r_score_after = after['readiness']['readiness_score']
            est_after = after['skills_data'][0]['current_estimate']
            prog_after = after['roadmap']['overall_progress']

            # Roadmap progress changed
            assert prog_before != prog_after
            assert prog_after == 100

            # Proficiency and readiness are completely untouched!
            assert r_score_before == r_score_after
            assert est_before == est_after


class TestAnalyticsRoutesAndSecurity:
    """Integration and security tests for /analytics endpoints."""

    def test_analytics_requires_login(self, client):
        """Unauthenticated requests to /analytics/ and /analytics/report redirect to login."""
        r1 = client.get('/analytics/', follow_redirects=False)
        assert r1.status_code == 302
        assert '/auth/login' in r1.headers['Location']

        r2 = client.get('/analytics/report', follow_redirects=False)
        assert r2.status_code == 302
        assert '/auth/login' in r2.headers['Location']

        r3 = client.get('/analytics/data', follow_redirects=False)
        assert r3.status_code == 302
        assert '/auth/login' in r3.headers['Location']

    def test_analytics_page_without_career_shows_empty_state(self, seeded_app, client):
        """User without target career sees helpful empty state."""
        register_user(client, email='no_career_ana@test.com', username='no_career_ana')
        login_user(client, email='no_career_ana@test.com')

        res = client.get('/analytics/')
        assert res.status_code == 200
        html = res.data.decode('utf-8')
        assert 'Select a Career to View Progress' in html
        assert 'Explore Careers' in html

    def test_analytics_page_with_active_career(self, seeded_app, client):
        """User with active career views full analytics dashboard with charts."""
        register_user(client, email='ana_user@test.com', username='ana_user')
        login_user(client, email='ana_user@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        res = client.get('/analytics/')
        assert res.status_code == 200
        html = res.data.decode('utf-8')
        assert 'Frontend Developer Progress &amp; Analytics' in html or 'Frontend Developer Progress & Analytics' in html
        assert 'Career Readiness' in html
        assert 'Assessment Coverage' in html
        assert 'Roadmap Completion' in html
        assert 'skillsChart' in html
        assert 'stagesChart' in html

    def test_analytics_data_json_endpoint(self, seeded_app, client):
        """GET /analytics/data returns serialized JSON metrics."""
        register_user(client, email='json_ana@test.com', username='json_ana')
        login_user(client, email='json_ana@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        res = client.get('/analytics/data')
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data['success'] is True
        assert json_data['has_active_career'] is True
        assert 'chart_data' in json_data
        assert 'skills' in json_data['chart_data']
        assert 'roadmap_stages' in json_data['chart_data']

    def test_user_isolation_on_analytics_data(self, seeded_app, client):
        """User B cannot see User A's assessments or estimates in analytics."""
        # Register and assess User A
        register_user(client, email='usera_ana@test.com', username='usera_ana')
        login_user(client, email='usera_ana@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        with seeded_app.app_context():
            db = get_db()
            ua = db.execute("SELECT id FROM users WHERE email = 'usera_ana@test.com'").fetchone()
            db.execute("""
                INSERT INTO assessment_attempts (user_id, skill_id, total_questions, correct_count, score_percentage, quiz_proficiency, status)
                VALUES (?, 1, 5, 5, 100.0, 5, 'completed')
            """, (ua['id'],))
            db.commit()

        # Register and check User B
        register_user(client, email='userb_ana@test.com', username='userb_ana')
        login_user(client, email='userb_ana@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        res_b = client.get('/analytics/data')
        data_b = res_b.get_json()
        assert len(data_b['chart_data']['history_timeline']['scores']) == 0

    def test_dated_progress_report_endpoint(self, seeded_app, client):
        """GET /analytics/report generates formatted printable report with user standing."""
        register_user(client, email='report_user@test.com', username='report_user', full_name='Report Candidate')
        login_user(client, email='report_user@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        res = client.get('/analytics/report')
        assert res.status_code == 200
        html = res.data.decode('utf-8')
        assert 'Student Career Readiness Progress Report' in html
        assert 'Report Candidate' in html
        assert 'Frontend Developer' in html
        assert 'Priority Development Gaps' in html or 'Skill Requirements' in html
        assert 'window.print()' in html

    def test_dashboard_progress_card_integration(self, seeded_app, client):
        """Dashboard displays live analytics summary card linking to /analytics/."""
        register_user(client, email='dash_ana@test.com', username='dash_ana')
        login_user(client, email='dash_ana@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        res = client.get('/dashboard')
        assert res.status_code == 200
        html = res.data.decode('utf-8')
        assert 'Progress &amp; Analytics' in html or 'Progress & Analytics' in html
        assert 'View Analytics' in html
        assert '/analytics/' in html

    def test_analytics_page_renders_with_assessment_history_and_resolves_view_attempt_link(self, seeded_app, client):
        """REGRESSION TEST: /analytics/ renders successfully with completed attempts and links resolve to assessment.view_attempt."""
        register_user(client, email='attempt_link@test.com', username='attempt_link')
        login_user(client, email='attempt_link@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        with seeded_app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'attempt_link@test.com'").fetchone()
            cur = db.execute("""
                INSERT INTO assessment_attempts (
                    user_id, skill_id, total_questions, correct_count, score_percentage,
                    quiz_proficiency, self_assessed_level, combined_estimate, status, completed_at
                )
                VALUES (?, 1, 5, 4, 80.0, 4, 3, 3.7, 'completed', '2026-10-15 12:00:00')
            """, (user['id'],))
            attempt_id = cur.lastrowid
            db.commit()

        # Request /analytics/ - must not raise BuildError
        res = client.get('/analytics/')
        assert res.status_code == 200
        html = res.data.decode('utf-8')

        # Verify that the link to assessment.view_attempt rendered correctly
        expected_url = f"/assessment/attempt/{attempt_id}"
        assert expected_url in html
        assert 'Completed Assessment History Log' in html
        assert '80.0%' in html

