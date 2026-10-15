# Skillora

**Career Readiness & Skill Gap Analysis Platform**

Built by **Logic Ninjas** for the college hackathon.

Skillora helps students explore career paths, assess their skills, identify gaps, and follow personalized learning roadmaps.

---

## Supported Career Paths

- Frontend Developer
- Backend Developer
- Full-Stack Developer
- Data Analyst
- UI/UX Designer
- Software QA Engineer

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML, CSS, Vanilla JavaScript |
| **Backend** | Python, Flask |
| **Database** | SQLite |
| **Charts** | Chart.js *(upcoming)* |

---

## Quick Start

### Prerequisites

- **Python 3.9** or higher
- **pip** (included with Python)

### Installation

```bash
# Navigate to the project directory
cd Skillora

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Setup & Seeding

```bash
# Initialize schema and seed default careers and skill requirements
flask --app app init-db

# Or to re-seed/update careers and skills without affecting existing users:
flask --app app seed-db
```

### Running the Application

```bash
python app.py
```

The application will be available at **http://localhost:5000**.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SKILLORA_SECRET_KEY` | Flask secret key for session cookies | `dev-secret-key-change-in-production` |

> **Production:** Always set a strong, unique `SKILLORA_SECRET_KEY`.

---

## Demo / Judge Access

Visit **http://localhost:5000/demo** to instantly log in with a pre-configured demo account.

| Field | Value |
|---|---|
| Email | `demo@skillora.app` |
| Username | `demo_user` |
| Name | Demo User |

This route:
- Creates the demo user on first visit.
- Logs you in automatically on every visit.
- Is safe to visit multiple times (idempotent).
- Does not expose any other user's data.

---

## Running Tests

```bash
# Install test dependency (if not already installed)
pip install pytest

# Run all tests with verbose output
python -m pytest tests/ -v
```

---

## Project Structure

```
Skillora/
├── app.py              # Application factory
├── config.py           # Configuration classes (Dev/Prod/Test)
├── db.py               # Database utilities, safe migrations & CLI commands (init-db, seed-db)
├── seeds.py            # Career, skill & starter question bank definitions and seed engine
├── assessment_engine.py# Scoring logic, formula S=0.7Q+0.3A, discrepancy detection & readiness
├── assessment.py       # Assessment blueprint (quizzes, scoring, attempts review)
├── roadmap_service.py  # Personalized roadmap generation (Learn->Practice->Build->Review)
├── roadmap.py          # Learning Roadmap blueprint (stage views, task toggling, refresh)
├── analytics_service.py# Analytics calculations, skill gap analysis, and chart data compilation
├── analytics.py        # Analytics blueprint (dashboard, Chart.js charts, printable report)
├── auth.py             # Authentication blueprint (register/login/logout)
├── main.py             # Core routes (landing, dashboard, demo, careers, select)
├── schema.sql          # Database schema (users, careers, skills, questions, roadmaps, tasks)
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── HANDOFF.md          # Structured milestone handoff log
├── instance/           # Database files (auto-created)
│   └── skillora.db
├── static/
│   ├── css/
│   │   └── style.css   # Complete stylesheet matching visual identity
│   └── js/
│       └── main.js     # Client-side enhancements
├── templates/
│   ├── base.html       # Base layout template
│   ├── landing.html    # Landing/hero page
│   ├── dashboard.html  # Authenticated dashboard with readiness/coverage, roadmap & analytics
│   ├── careers/
│   │   ├── index.html  # Career catalog with selection controls and history
│   │   └── detail.html # Career skill requirements table with weights & targets
│   ├── assessment/
│   │   ├── index.html  # Career skill assessment overview & attempt history
│   │   ├── take.html   # Assessment form with self-rating & technical questions
│   │   └── result.html # Score breakdown, proficiency mapping, discrepancy alerts
│   ├── roadmap/
│   │   └── index.html  # 4-stage interactive roadmap (Learn, Practice, Build, Review)
│   ├── analytics/
│   │   ├── index.html  # Progress Tracking & Analytics with interactive Chart.js charts
│   │   └── report.html # Printable/dated student career readiness report
│   └── auth/
│       ├── login.html
│       └── register.html
└── tests/
    ├── __init__.py
    ├── conftest.py         # Test fixtures and helpers
    ├── test_analytics.py  # 13 tests: skill gaps, readiness/coverage separation, charts, reports, regression
    ├── test_roadmap.py    # 16 tests: 4 stages, ordering, gaps, toggle, isolation, refresh
    ├── test_assessment.py # 14 tests: engine boundaries, formulas, discrepancy, flow, isolation
    ├── test_auth.py       # 17 tests: authentication, registration, session, access control
    ├── test_careers.py    # 14 tests: career profiles, skill requirements, seeding & selection
    ├── test_db.py         # 5 tests: database connections, initialization & schema upgrade
    └── test_demo.py       # 3 tests: demo user creation, idempotency, dashboard access
```

---

## Current Status

### ✅ Implemented (Milestone 1 — Foundation)
- Flask application structure with factory pattern
- SQLite database with safe initialization
- User registration, login, logout, and password hashing
- Session management and route protection
- Responsive landing page and dashboard empty states
- Demo judge access (`/demo`)

### ✅ Implemented (Milestone 2 — Career Profiles & Skill Requirements)
- Database schema for 6 careers, reusable skills catalog, and career-to-skill requirements
- Positive importance weights and 1–5 target proficiency levels
- Repeatable, idempotent seeding engine (`flask --app app seed-db`) preserving existing users
- Career catalog view (`/careers`) and detailed requirements breakdown (`/careers/<career_code>`)
- Persistent target career selection and switching with complete selection history preserved
- Strict user isolation and input validation

### ✅ Implemented (Milestone 3 — Assessment Engine)
- Mathematical scoring engine (`assessment_engine.py`) with documented percentage-to-level mapping (Levels 1–5; Level 0 exclusively for unassessed)
- Initial combined skill estimate formula: $S = 0.7Q + 0.3A$, with strict handling of missing data
- Discrepancy detection ($|Q - A| \ge 2$) prompting constructive guidance without forcing retakes
- Importance-weighted career readiness with capped skill attainment at target level ($E_i \le T_i$)
- Independent assessment coverage calculation and provisional readiness status (< 70% coverage)
- Curated starter question bank (33 questions across 8 representative skills)
- Interactive quiz interface with self-assessment rating and server-side answer validation
- Upserting of current skill estimates upon valid completion while preserving full attempt history
- User isolation: prevention of unauthorized access to other users' assessment attempts

### ✅ Implemented (Milestone 4 — Personalized Learning Roadmap)
- Structured 4-stage progression: **Learn → Practice → Build → Review**
- Service layer (`roadmap_service.py`) generating career-tailored roadmaps from required skills, target proficiencies, current skill estimates, and prerequisite relationships
- Unassessed skills receive foundational learning recommendations without being treated as zero proficiency
- Curated free-first learning resources (MDN, Python.org, SQLite.org, OWASP, W3C, pytest, Pandas, Material Design)
- Capstone portfolio projects for all 6 careers in the Build stage
- Task persistence, completion toggling, and reopening in SQLite
- Task completion updates roadmap progress ONLY; never alters skill proficiency, assessments, or career readiness
- Career switching preserves historical roadmaps and completed tasks
- Roadmap refresh capability based on new assessment scores while preserving completed tasks

### ✅ Implemented (Milestone 5 — Progress Tracking & Analytics)
- Analytics service (`analytics_service.py`) deriving real progress metrics without fabricated history
- Interactive Chart.js charts:
  - Skill Proficiency comparison: Target Level vs Current Estimate (unassessed skills omitted and never plotted as zero)
  - Roadmap Stage Completion: Completed vs Total tasks across Learn, Practice, Build, Review
  - Assessment Score Timeline: Chronological quiz score trajectory for completed attempts (requires $\ge 2$ real attempts; explains when more data is needed)
- Career readiness and coverage tracked and displayed independently with provisional warnings
- Detailed Skill Gap table showing target, estimate, gap, and status badge
- Milestone tracking for completed projects in the Build stage
- Formatted, printable/PDF-ready Student Career Readiness Progress Report (`/analytics/report`)
- Live dashboard card integration replacing placeholder
- 82 total automated tests passing with 0 warnings




---

## License

Hackathon project — **Logic Ninjas**.
