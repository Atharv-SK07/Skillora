"""Tests for Milestone 4: Personalized Learning Roadmap."""

import pytest
from db import get_db
from seeds import seed_careers_and_skills
from roadmap_service import (
    generate_roadmap_for_user,
    get_user_active_roadmap,
    toggle_task_completion,
)
from tests.conftest import register_user, login_user


@pytest.fixture
def seeded_app(app):
    """Fixture providing an app with seeded careers and skills and test users."""
    with app.app_context():
        db = get_db()
        seed_careers_and_skills(db)
        db.execute("INSERT OR IGNORE INTO users (id, email, username, password_hash, full_name) VALUES (1, 'u1@test.com', 'user1', 'hash', 'User One')")
        db.execute("INSERT OR IGNORE INTO users (id, email, username, password_hash, full_name) VALUES (2, 'u2@test.com', 'user2', 'hash', 'User Two')")
        db.commit()
    return app



class TestRoadmapGenerationService:
    """Unit and service tests for roadmap generation logic."""

    def test_roadmap_generation_all_six_careers(self, seeded_app):
        """Roadmap generation works for all six supported career tracks."""
        with seeded_app.app_context():
            db = get_db()
            careers = db.execute("SELECT id, code, title FROM careers ORDER BY id").fetchall()
            assert len(careers) == 6

            for career in careers:
                roadmap_id = generate_roadmap_for_user(db, user_id=1, career_id=career['id'])
                assert roadmap_id is not None

                tasks = db.execute(
                    "SELECT stage, is_project FROM roadmap_tasks WHERE roadmap_id = ?",
                    (roadmap_id,)
                ).fetchall()
                assert len(tasks) > 0

                stages = {t['stage'] for t in tasks}
                assert stages == {'learn', 'practice', 'build', 'review'}

                # Build stage has at least one project
                build_projects = [t for t in tasks if t['stage'] == 'build' and t['is_project'] == 1]
                assert len(build_projects) >= 1

    def test_correct_stage_ordering(self, seeded_app):
        """Tasks are strictly ordered: Learn -> Practice -> Build -> Review."""
        with seeded_app.app_context():
            db = get_db()
            roadmap_id = generate_roadmap_for_user(db, user_id=1, career_id=1)

            tasks = db.execute(
                "SELECT stage, recommended_order FROM roadmap_tasks WHERE roadmap_id = ? ORDER BY recommended_order ASC",
                (roadmap_id,)
            ).fetchall()

            stage_sequence = []
            for t in tasks:
                stage = t['stage']
                if not stage_sequence or stage_sequence[-1] != stage:
                    stage_sequence.append(stage)

            assert stage_sequence == ['learn', 'practice', 'build', 'review']

    def test_skill_gap_and_unassessed_reasoning(self, seeded_app):
        """Tasks provide personalized explanations for gaps vs unassessed skills."""
        with seeded_app.app_context():
            db = get_db()
            # Insert estimate for html-css (skill_id = 1) with gap
            # Frontend target is 4, user has 2.5
            db.execute("""
                INSERT INTO user_skill_estimates (user_id, skill_id, quiz_proficiency, self_assessed_level, current_estimate)
                VALUES (1, 1, 2, 3, 2.3)
            """)
            db.commit()

            roadmap_id = generate_roadmap_for_user(db, user_id=1, career_id=1)

            tasks = db.execute(
                "SELECT skill_id, reason, stage FROM roadmap_tasks WHERE roadmap_id = ? AND stage = 'learn'",
                (roadmap_id,)
            ).fetchall()

            # Task for skill_id 1 should mention gap
            task_gap = next((t for t in tasks if t['skill_id'] == 1), None)
            assert task_gap is not None
            assert "Skill gap" in task_gap['reason']
            assert "2.3" in task_gap['reason']

            # Other skills are unassessed, should not treat as zero proficiency
            task_unassessed = next((t for t in tasks if t['skill_id'] != 1 and t['skill_id'] is not None), None)
            assert task_unassessed is not None
            assert "Unassessed" in task_unassessed['reason']
            assert "0/5" not in task_unassessed['reason']
            assert "zero proficiency" not in task_unassessed['reason'].lower()

    def test_prerequisite_ordering_foundational_skills_first(self, seeded_app):
        """Foundational prerequisite skills appear before advanced dependent skills."""
        with seeded_app.app_context():
            db = get_db()
            roadmap_id = generate_roadmap_for_user(db, user_id=1, career_id=1)  # Frontend Dev

            tasks = db.execute(
                """
                SELECT s.code as skill_code, rt.recommended_order
                FROM roadmap_tasks rt
                JOIN skills s ON rt.skill_id = s.id
                WHERE rt.roadmap_id = ? AND rt.stage = 'learn'
                ORDER BY rt.recommended_order ASC
                """,
                (roadmap_id,)
            ).fetchall()

            orders = {t['skill_code']: t['recommended_order'] for t in tasks}
            # html-css is prerequisite to frontend-frameworks
            if 'html-css' in orders and 'frontend-frameworks' in orders:
                assert orders['html-css'] < orders['frontend-frameworks']

    def test_repeated_generation_avoids_duplicate_tasks(self, seeded_app):
        """Repeated generation calls do not duplicate tasks."""
        with seeded_app.app_context():
            db = get_db()
            id1 = generate_roadmap_for_user(db, user_id=1, career_id=1)
            count1 = db.execute("SELECT COUNT(*) FROM roadmap_tasks WHERE roadmap_id = ?", (id1,)).fetchone()[0]

            id2 = generate_roadmap_for_user(db, user_id=1, career_id=1)
            count2 = db.execute("SELECT COUNT(*) FROM roadmap_tasks WHERE roadmap_id = ?", (id2,)).fetchone()[0]

            assert id1 == id2
            assert count1 == count2


class TestTaskCompletionAndIntegrity:
    """Tests verifying task completion toggling and non-negotiable integrity rules."""

    def test_toggle_task_completion_and_reopen(self, seeded_app):
        """User can mark a task complete and reopen it."""
        with seeded_app.app_context():
            db = get_db()
            roadmap_id = generate_roadmap_for_user(db, user_id=1, career_id=1)
            task = db.execute("SELECT id, is_completed FROM roadmap_tasks WHERE roadmap_id = ? LIMIT 1", (roadmap_id,)).fetchone()
            assert task['is_completed'] == 0

            # Toggle to complete
            res1 = toggle_task_completion(db, user_id=1, task_id=task['id'])
            assert res1['is_completed'] == 1

            saved1 = db.execute("SELECT is_completed, completed_at FROM roadmap_tasks WHERE id = ?", (task['id'],)).fetchone()
            assert saved1['is_completed'] == 1
            assert saved1['completed_at'] is not None

            # Toggle to reopen
            res2 = toggle_task_completion(db, user_id=1, task_id=task['id'])
            assert res2['is_completed'] == 0

            saved2 = db.execute("SELECT is_completed, completed_at FROM roadmap_tasks WHERE id = ?", (task['id'],)).fetchone()
            assert saved2['is_completed'] == 0
            assert saved2['completed_at'] is None

    def test_task_completion_does_not_modify_proficiency_or_readiness(self, seeded_app):
        """CRITICAL: Task completion must NOT alter skill proficiency or assessment history."""
        with seeded_app.app_context():
            db = get_db()
            # Set initial estimate
            db.execute("""
                INSERT INTO user_skill_estimates (user_id, skill_id, quiz_proficiency, self_assessed_level, current_estimate)
                VALUES (1, 1, 3, 3, 3.0)
            """)
            db.commit()

            estimates_before = db.execute("SELECT * FROM user_skill_estimates WHERE user_id = 1").fetchall()
            attempts_before = db.execute("SELECT COUNT(*) FROM assessment_attempts WHERE user_id = 1").fetchone()[0]

            roadmap_id = generate_roadmap_for_user(db, user_id=1, career_id=1)
            tasks = db.execute("SELECT id FROM roadmap_tasks WHERE roadmap_id = ?", (roadmap_id,)).fetchall()

            # Mark all tasks completed
            for t in tasks:
                toggle_task_completion(db, user_id=1, task_id=t['id'])

            estimates_after = db.execute("SELECT * FROM user_skill_estimates WHERE user_id = 1").fetchall()
            attempts_after = db.execute("SELECT COUNT(*) FROM assessment_attempts WHERE user_id = 1").fetchone()[0]

            assert len(estimates_before) == len(estimates_after)
            assert estimates_before[0]['current_estimate'] == estimates_after[0]['current_estimate']
            assert attempts_before == attempts_after == 0

    def test_user_isolation_on_task_modification(self, seeded_app):
        """User A cannot modify User B's roadmap tasks."""
        with seeded_app.app_context():
            db = get_db()
            roadmap_user1 = generate_roadmap_for_user(db, user_id=1, career_id=1)
            task_user1 = db.execute("SELECT id FROM roadmap_tasks WHERE roadmap_id = ? LIMIT 1", (roadmap_user1,)).fetchone()

            with pytest.raises(PermissionError):
                toggle_task_completion(db, user_id=2, task_id=task_user1['id'])


class TestCareerSwitchingAndPersistence:
    """Tests career switching, history preservation, and regeneration."""

    def test_career_switch_preserves_historical_roadmaps(self, seeded_app):
        """Switching careers preserves prior roadmap and its completion status."""
        with seeded_app.app_context():
            db = get_db()
            # Create roadmap for Career 1 (Frontend)
            r1_id = generate_roadmap_for_user(db, user_id=1, career_id=1)
            task1 = db.execute("SELECT id FROM roadmap_tasks WHERE roadmap_id = ? LIMIT 1", (r1_id,)).fetchone()
            toggle_task_completion(db, user_id=1, task_id=task1['id'])

            # Switch to Career 2 (Backend)
            r2_id = generate_roadmap_for_user(db, user_id=1, career_id=2)
            assert r1_id != r2_id

            # Verify Career 1 roadmap is deactivated but intact
            r1_check = db.execute("SELECT is_active FROM roadmaps WHERE id = ?", (r1_id,)).fetchone()
            assert r1_check['is_active'] == 0

            # Verify completed task in Career 1 is preserved
            t1_check = db.execute("SELECT is_completed FROM roadmap_tasks WHERE id = ?", (task1['id'],)).fetchone()
            assert t1_check['is_completed'] == 1

            # Switch back to Career 1
            r1_reactivated = generate_roadmap_for_user(db, user_id=1, career_id=1)
            assert r1_reactivated == r1_id

            r1_active = db.execute("SELECT is_active FROM roadmaps WHERE id = ?", (r1_id,)).fetchone()
            assert r1_active['is_active'] == 1
            t1_preserved = db.execute("SELECT is_completed FROM roadmap_tasks WHERE id = ?", (task1['id'],)).fetchone()
            assert t1_preserved['is_completed'] == 1

    def test_roadmap_regeneration_preserves_completed_tasks(self, seeded_app):
        """Regenerating a roadmap updates task reasoning while preserving completed tasks."""
        with seeded_app.app_context():
            db = get_db()
            r_id = generate_roadmap_for_user(db, user_id=1, career_id=1)
            task = db.execute("SELECT id, title FROM roadmap_tasks WHERE roadmap_id = ? LIMIT 1", (r_id,)).fetchone()

            # Mark task complete
            toggle_task_completion(db, user_id=1, task_id=task['id'])

            # Simulate new assessment score
            db.execute("""
                INSERT INTO user_skill_estimates (user_id, skill_id, quiz_proficiency, self_assessed_level, current_estimate)
                VALUES (1, 1, 4, 4, 4.0)
            """)
            db.commit()

            # Regenerate with refresh=True
            generate_roadmap_for_user(db, user_id=1, career_id=1, refresh=True)

            # Assert task with matching title is still completed
            task_refreshed = db.execute(
                "SELECT is_completed FROM roadmap_tasks WHERE roadmap_id = ? AND title = ?",
                (r_id, task['title'])
            ).fetchone()
            assert task_refreshed['is_completed'] == 1


class TestRoadmapRoutesAndUI:
    """Integration tests for roadmap HTTP endpoints and dashboard integration."""

    def test_roadmap_page_requires_login(self, client):
        """Unauthenticated access to /roadmap/ redirects to login."""
        response = client.get('/roadmap/', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_roadmap_page_without_career_shows_helpful_empty_state(self, seeded_app, client):
        """User without a selected career sees clear guidance."""
        register_user(client, email='nocareer@test.com', username='nocareer')
        login_user(client, email='nocareer@test.com')

        response = client.get('/roadmap/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Select a Career to Generate Your Roadmap' in html
        assert 'Explore &amp; Select Career' in html or 'Explore & Select Career' in html

    def test_roadmap_page_with_active_career(self, seeded_app, client):
        """User with active career can view their 4-stage roadmap."""
        register_user(client, email='withcareer@test.com', username='withcareer')
        login_user(client, email='withcareer@test.com')

        # Select career 1 (Frontend Developer)
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        response = client.get('/roadmap/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Frontend Developer Roadmap' in html
        assert 'Stage 1: Learn' in html
        assert 'Stage 2: Practice' in html
        assert 'Stage 3: Build' in html
        assert 'Stage 4: Review' in html
        assert 'Milestone Project' in html

    def test_task_toggle_endpoint(self, seeded_app, client):
        """POST to toggle task marks it completed and redirects."""
        register_user(client, email='toggle@test.com', username='toggleuser')
        login_user(client, email='toggle@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        with seeded_app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'toggle@test.com'").fetchone()
            roadmap = db.execute("SELECT id FROM roadmaps WHERE user_id = ?", (user['id'],)).fetchone()
            task = db.execute("SELECT id FROM roadmap_tasks WHERE roadmap_id = ? LIMIT 1", (roadmap['id'],)).fetchone()
            task_id = task['id']

        # Toggle task
        res = client.post(f'/roadmap/task/{task_id}/toggle', follow_redirects=True)
        assert res.status_code == 200

        with seeded_app.app_context():
            db = get_db()
            updated_task = db.execute("SELECT is_completed FROM roadmap_tasks WHERE id = ?", (task_id,)).fetchone()
            assert updated_task['is_completed'] == 1

    def test_user_cannot_toggle_another_users_task_returns_403(self, seeded_app, client):
        """User B cannot toggle User A's task via HTTP endpoint."""
        register_user(client, email='usera@test.com', username='usera')
        register_user(client, email='userb@test.com', username='userb')

        # Login as User A and create roadmap
        login_user(client, email='usera@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        with seeded_app.app_context():
            db = get_db()
            user_a = db.execute("SELECT id FROM users WHERE email = 'usera@test.com'").fetchone()
            roadmap_a = db.execute("SELECT id FROM roadmaps WHERE user_id = ?", (user_a['id'],)).fetchone()
            task_a = db.execute("SELECT id FROM roadmap_tasks WHERE roadmap_id = ? LIMIT 1", (roadmap_a['id'],)).fetchone()
            task_a_id = task_a['id']

        # Login as User B and attempt to toggle User A's task
        login_user(client, email='userb@test.com')
        res = client.post(f'/roadmap/task/{task_a_id}/toggle')
        assert res.status_code == 403

    def test_dashboard_shows_live_roadmap_summary(self, seeded_app, client):
        """Dashboard displays live roadmap metrics and next recommended step."""
        register_user(client, email='dashroad@test.com', username='dashroad')
        login_user(client, email='dashroad@test.com')
        client.post('/careers/select', data={'career_id': 1}, follow_redirects=True)

        response = client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Learning Roadmap' in html
        assert 'tasks completed' in html
        assert 'Open Learning Roadmap' in html
        assert 'Recommended Next Step' in html
