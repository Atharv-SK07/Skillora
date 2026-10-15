"""Tests for Milestone 2: Career Profiles & Skill Requirements."""

import pytest
from db import get_db
from seeds import seed_careers_and_skills, CAREERS_DATA
from tests.conftest import register_user, login_user


class TestCareerProfilesAndSkills:
    """Test career profiles and skill requirements seeding and integrity."""

    def test_all_six_careers_seeded(self, app):
        """Verify exactly the 6 required careers exist after seeding."""
        with app.app_context():
            db = get_db()
            seed_careers_and_skills(db)

            rows = db.execute("SELECT code, title FROM careers ORDER BY id").fetchall()
            assert len(rows) == 6

            expected_titles = [
                "Frontend Developer",
                "Backend Developer",
                "Full-Stack Developer",
                "Data Analyst",
                "UI/UX Designer",
                "Software QA Engineer"
            ]
            titles = [r["title"] for r in rows]
            assert titles == expected_titles

    def test_repeated_seeding_is_idempotent(self, app):
        """Repeated seeding must not duplicate careers, skills, or requirements."""
        with app.app_context():
            db = get_db()
            seed_careers_and_skills(db)
            first_careers_count = db.execute("SELECT COUNT(*) as cnt FROM careers").fetchone()["cnt"]
            first_skills_count = db.execute("SELECT COUNT(*) as cnt FROM skills").fetchone()["cnt"]
            first_reqs_count = db.execute("SELECT COUNT(*) as cnt FROM career_skill_requirements").fetchone()["cnt"]

            # Run seeding again
            seed_careers_and_skills(db)
            second_careers_count = db.execute("SELECT COUNT(*) as cnt FROM careers").fetchone()["cnt"]
            second_skills_count = db.execute("SELECT COUNT(*) as cnt FROM skills").fetchone()["cnt"]
            second_reqs_count = db.execute("SELECT COUNT(*) as cnt FROM career_skill_requirements").fetchone()["cnt"]

            assert first_careers_count == second_careers_count == 6
            assert first_skills_count == second_skills_count
            assert first_reqs_count == second_reqs_count

    def test_skill_requirements_targets_and_weights(self, app):
        """Verify skill requirements have target levels 1-5 and strictly positive weights."""
        with app.app_context():
            db = get_db()
            seed_careers_and_skills(db)

            reqs = db.execute(
                "SELECT career_id, skill_id, target_level, importance_weight, is_core FROM career_skill_requirements"
            ).fetchall()
            assert len(reqs) > 0

            for req in reqs:
                # Target levels must be on the 1-5 scale (0 is reserved for not assessed)
                assert 1 <= req["target_level"] <= 5
                # Importance weights must be strictly positive
                assert req["importance_weight"] > 0
                # Core flag must be 0 or 1
                assert req["is_core"] in (0, 1)

    def test_duplicate_career_skill_mapping_rejected(self, app):
        """Database constraint must prevent duplicate (career_id, skill_id) mappings."""
        with app.app_context():
            db = get_db()
            seed_careers_and_skills(db)

            first_req = db.execute("SELECT career_id, skill_id FROM career_skill_requirements LIMIT 1").fetchone()
            import sqlite3
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO career_skill_requirements (career_id, skill_id, target_level, importance_weight, is_core) "
                    "VALUES (?, ?, 3, 2.0, 1)",
                    (first_req["career_id"], first_req["skill_id"])
                )

    def test_seed_db_cli_command(self, runner, app):
        """Test seed-db CLI command runs cleanly."""
        result = runner.invoke(args=['seed-db'])
        assert 'Seeded careers and skills successfully.' in result.output or 'seeded' in result.output.lower()


class TestCareerSelectionRoutes:
    """Test viewing and selecting career profiles."""

    def test_careers_page_requires_login(self, client):
        """Unauthenticated access to /careers redirects to login."""
        response = client.get('/careers')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_authenticated_user_can_view_careers(self, client, app):
        """Authenticated user can view all 6 careers and skill counts."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="career_viewer@example.com", username="careerviewer")
        login_user(client, email="career_viewer@example.com")

        response = client.get('/careers')
        assert response.status_code == 200
        assert b'Explore Career Paths' in response.data
        assert b'Frontend Developer' in response.data
        assert b'Backend Developer' in response.data
        assert b'Full-Stack Developer' in response.data
        assert b'Data Analyst' in response.data
        assert b'UI/UX Designer' in response.data
        assert b'Software QA Engineer' in response.data

    def test_user_can_view_career_details_and_requirements(self, client, app):
        """Authenticated user can view a career's specific skill requirements table."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="detail_viewer@example.com", username="detailviewer")
        login_user(client, email="detail_viewer@example.com")

        response = client.get('/careers/frontend-dev')
        assert response.status_code == 200
        assert b'Frontend Developer' in response.data
        assert b'Required Skills &amp; Proficiency Targets' in response.data
        assert b'HTML5 &amp; Modern CSS' in response.data or b'HTML5' in response.data
        assert b'Core' in response.data

    def test_nonexistent_career_detail_redirects(self, client):
        """Accessing nonexistent career code redirects to careers list with flash error."""
        register_user(client, email="bad_career@example.com", username="badcareer")
        login_user(client, email="bad_career@example.com")

        response = client.get('/careers/non-existent-career', follow_redirects=True)
        assert response.status_code == 200
        assert b'not found' in response.data.lower()

    def test_user_can_select_career(self, client, app):
        """User can select a target career and see it active on the dashboard and careers page."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="selector@example.com", username="selector")
        login_user(client, email="selector@example.com")

        # Select Frontend Developer (id = 1)
        response = client.post('/careers/select', data={'career_id': '1'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'Target career set to' in response.data
        assert b'Frontend Developer' in response.data

        # Verify on dashboard
        dash_response = client.get('/dashboard')
        assert dash_response.status_code == 200
        assert b'Frontend Developer' in dash_response.data

    def test_user_can_change_career_and_history_is_preserved(self, client, app):
        """Changing careers deactivates the old selection while retaining complete history."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="switcher@example.com", username="switcher")
        login_user(client, email="switcher@example.com")

        # Select Frontend Developer
        client.post('/careers/select', data={'career_id': '1'}, follow_redirects=True)
        # Switch to Data Analyst (id = 4)
        client.post('/careers/select', data={'career_id': '4'}, follow_redirects=True)

        with app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'switcher@example.com'").fetchone()

            # Verify historical selections
            history = db.execute(
                "SELECT career_path, is_active FROM career_selections WHERE user_id = ? ORDER BY id ASC",
                (user["id"],)
            ).fetchall()

            assert len(history) == 2
            assert history[0]["career_path"] == "Frontend Developer"
            assert history[0]["is_active"] == 0  # Preserved as archived
            assert history[1]["career_path"] == "Data Analyst"
            assert history[1]["is_active"] == 1  # Active target

        # Check careers page history display
        careers_resp = client.get('/careers')
        assert b'Career Selection History' in careers_resp.data
        assert b'Frontend Developer' in careers_resp.data
        assert b'Data Analyst' in careers_resp.data
        assert b'Archived' in careers_resp.data

    def test_selecting_already_active_career_shows_info(self, client, app):
        """Attempting to select the currently active career path produces an informative notice."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="same_career@example.com", username="samecareer")
        login_user(client, email="same_career@example.com")

        client.post('/careers/select', data={'career_id': '2'}, follow_redirects=True)
        response = client.post('/careers/select', data={'career_id': '2'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'already your active career path' in response.data

    def test_invalid_career_id_rejected(self, client, app):
        """Submitting non-numeric or nonexistent career ID returns clear error message."""
        with app.app_context():
            seed_careers_and_skills()

        register_user(client, email="invalid_tester@example.com", username="invalidtester")
        login_user(client, email="invalid_tester@example.com")

        # Non-numeric ID
        resp1 = client.post('/careers/select', data={'career_id': 'abc'}, follow_redirects=True)
        assert b'Invalid career ID' in resp1.data or b'error' in resp1.data.lower()

        # Nonexistent ID
        resp2 = client.post('/careers/select', data={'career_id': '9999'}, follow_redirects=True)
        assert b'does not exist' in resp2.data.lower()

        # Empty ID
        resp3 = client.post('/careers/select', data={'career_id': ''}, follow_redirects=True)
        assert b'select a valid career' in resp3.data.lower()


class TestUserIsolation:
    """Test that users can only modify their own career selections."""

    def test_user_isolation_on_career_selection(self, client, app):
        """User A's career selection does not affect or overwrite User B's selection."""
        with app.app_context():
            seed_careers_and_skills()

        # User A registers and selects Backend Developer (id = 2)
        register_user(client, email="usera@example.com", username="usera")
        login_user(client, email="usera@example.com")
        client.post('/careers/select', data={'career_id': '2'}, follow_redirects=True)
        client.get('/auth/logout')

        # User B registers and selects UI/UX Designer (id = 5)
        register_user(client, email="userb@example.com", username="userb")
        login_user(client, email="userb@example.com")
        client.post('/careers/select', data={'career_id': '5'}, follow_redirects=True)

        # Verify User B's dashboard
        b_dash = client.get('/dashboard')
        assert b'UI/UX Designer' in b_dash.data
        assert b'Backend Developer' not in b_dash.data

        client.get('/auth/logout')

        # Log back in as User A and verify User A's selection remains Backend Developer
        login_user(client, email="usera@example.com")
        a_dash = client.get('/dashboard')
        assert b'Backend Developer' in a_dash.data
        assert b'UI/UX Designer' not in a_dash.data
