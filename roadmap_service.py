"""Skillora Learning Roadmap Service.

Provides database-backed, personalized learning roadmap generation and progress tracking.
Implements the 4-stage progression: Learn -> Practice -> Build -> Review.

Core principles:
- Generated based on active target career, required skills, and target proficiency levels.
- Takes into account user's current assessed skill estimates and gaps.
- Unassessed skills are treated as not yet assessed (NOT zero proficiency).
- Respects prerequisite ordering so foundational skills precede advanced ones.
- Task completion updates roadmap progress ONLY; never modifies skill proficiency.
- Preserves historical roadmaps when switching careers.
- Free-first, verified external learning resources.
"""

from datetime import datetime
import sqlite3

# ---------------------------------------------------------------------------
# Curated Verified Learning Resources & Templates
# ---------------------------------------------------------------------------

SKILL_LEARNING_RESOURCES = {
    "html-css": {
        "title": "MDN Web Docs: Learn HTML & CSS",
        "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Master semantic HTML5 markup, modern CSS layouts (Flexbox, CSS Grid), and cascade rules.",
        "practice_title": "Build a Responsive Multi-Section Landing Page",
        "practice_desc": "Code a clean, semantic web page layout using Flexbox and Grid without CSS frameworks.",
        "practice_duration": "2 hours (est.)",
    },
    "javascript": {
        "title": "MDN Web Docs: JavaScript Guide",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "duration": "2 hours (est.)",
        "learn_objective": "Understand JavaScript ES6+ fundamentals: scoping, closures, promises, async/await, and DOM APIs.",
        "practice_title": "Interactive DOM & Async API Consumer",
        "practice_desc": "Write pure vanilla JS to handle user input events, fetch dynamic JSON, and update UI state.",
        "practice_duration": "2 hours (est.)",
    },
    "responsive-design": {
        "title": "web.dev: Learn Responsive Design",
        "url": "https://web.dev/learn/design/",
        "duration": "1 hour (est.)",
        "learn_objective": "Study viewport mechanics, fluid typography, responsive images, and media query breakpoints.",
        "practice_title": "Mobile-First Layout Refactor",
        "practice_desc": "Convert a static desktop layout into a fully responsive mobile-first interface.",
        "practice_duration": "1.5 hours (est.)",
    },
    "frontend-frameworks": {
        "title": "React Official Documentation: Quick Start",
        "url": "https://react.dev/learn",
        "duration": "2 hours (est.)",
        "learn_objective": "Learn component-driven architecture, reactive state, props, and lifecycle management.",
        "practice_title": "Build a Component-Driven State Interface",
        "practice_desc": "Construct an interactive UI component tree with controlled inputs and shared state.",
        "practice_duration": "2 hours (est.)",
    },
    "git": {
        "title": "Pro Git Book by Scott Chacon",
        "url": "https://git-scm.com/book/en/v2",
        "duration": "1 hour (est.)",
        "learn_objective": "Master distributed version control: staging, branching strategies, commits, and merge resolution.",
        "practice_title": "Branching & Merge Conflict Drill",
        "practice_desc": "Simulate collaborative git workflow with feature branches, PR reviews, and clean rebase merges.",
        "practice_duration": "1 hour (est.)",
    },
    "web-performance": {
        "title": "web.dev: Fast Load Times & Core Web Vitals",
        "url": "https://web.dev/fast/",
        "duration": "1 hour (est.)",
        "learn_objective": "Understand critical rendering path, asset compression, lazy loading, and Core Web Vitals metrics.",
        "practice_title": "Lighthouse Audit & Performance Optimization",
        "practice_desc": "Run a browser Lighthouse audit on a sample web page and remediate LCP and layout shifts.",
        "practice_duration": "1.5 hours (est.)",
    },
    "accessibility": {
        "title": "W3C Web Accessibility Initiative (WAI)",
        "url": "https://www.w3.org/WAI/fundamentals/accessibility-intro/",
        "duration": "1 hour (est.)",
        "learn_objective": "Learn WCAG 2.1 AA principles, ARIA landmark roles, accessible color contrast, and keyboard navigation.",
        "practice_title": "Keyboard Navigation & Screen Reader Audit",
        "practice_desc": "Audit an interactive web form for keyboard tab-focus states, ARIA labels, and error announcements.",
        "practice_duration": "1 hour (est.)",
    },
    "python-backend": {
        "title": "Python Official Tutorial: Modules and Data Structures",
        "url": "https://docs.python.org/3/tutorial/",
        "duration": "2 hours (est.)",
        "learn_objective": "Review core Python idioms, object-oriented principles, exception handling, and virtual environments.",
        "practice_title": "Build Modular Python Web Controller",
        "practice_desc": "Write reusable Python functions and classes with structured logging and unit tests.",
        "practice_duration": "1.5 hours (est.)",
    },
    "relational-databases": {
        "title": "SQLite Official Documentation & SQL Tutorial",
        "url": "https://www.sqlite.org/docs.html",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Understand relational modeling, 3NF normalization, foreign key constraints, and indexing strategies.",
        "practice_title": "Schema Design & Relational Query Lab",
        "practice_desc": "Author a relational schema with constraints, populate sample data, and write multi-table JOINs.",
        "practice_duration": "2 hours (est.)",
    },
    "rest-apis": {
        "title": "MDN Web Docs: Working with Client-Side Web APIs",
        "url": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Client-side_web_APIs/Introduction",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Learn RESTful architectural constraints, HTTP status codes, idempotent methods, and JSON payloads.",
        "practice_title": "Implement RESTful CRUD Endpoints",
        "practice_desc": "Build REST API routes with request body validation, consistent error responses, and HTTP headers.",
        "practice_duration": "2 hours (est.)",
    },
    "auth-security": {
        "title": "OWASP Top Ten Web Application Security Risks",
        "url": "https://owasp.org/www-project-top-ten/",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Understand password hashing (PBKDF2/bcrypt), session hijacking, CSRF mitigation, and SQL injection prevention.",
        "practice_title": "Secure Authentication & Session Hardening",
        "practice_desc": "Implement hashed credential storage, parameterized queries, and login rate limiting.",
        "practice_duration": "2 hours (est.)",
    },
    "api-testing": {
        "title": "Postman Learning Center: API Testing Concepts",
        "url": "https://learning.postman.com/docs/getting-started/introduction/",
        "duration": "1 hour (est.)",
        "learn_objective": "Learn automated API test assertions, status code checks, payload schema validation, and test runs.",
        "practice_title": "Automated HTTP Endpoint Integration Tests",
        "practice_desc": "Write automated test scripts validating 200 OK, 400 Bad Request, and 401 Unauthorized responses.",
        "practice_duration": "1.5 hours (est.)",
    },
    "system-architecture": {
        "title": "The Architecture of Open Source Applications",
        "url": "https://aosabook.org/en/index.html",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Study layered software architecture, separation of concerns, caching patterns, and database connection pooling.",
        "practice_title": "Layered Application Architecture Refactoring",
        "practice_desc": "Decompose monolithic code into clean presentation, business logic, and data access layers.",
        "practice_duration": "2 hours (est.)",
    },
    "sql-querying": {
        "title": "Mode Analytics: SQL Tutorial for Beginners & Advanced",
        "url": "https://mode.com/sql-tutorial/",
        "duration": "2 hours (est.)",
        "learn_objective": "Master SELECT, WHERE, GROUP BY, HAVING, subqueries, and window functions (ROW_NUMBER, RANK).",
        "practice_title": "Complex Analytical SQL Query Challenge",
        "practice_desc": "Query a multi-table database to calculate rolling averages, user cohorts, and conversion rates.",
        "practice_duration": "2 hours (est.)",
    },
    "python-data": {
        "title": "Pandas Official User Guide: 10 Minutes to pandas",
        "url": "https://pandas.pydata.org/docs/user_guide/10min.html",
        "duration": "2 hours (est.)",
        "learn_objective": "Learn Pandas DataFrames and Series, indexing, vectorization, and data aggregation operations.",
        "practice_title": "DataFrame Transformation & Aggregation",
        "practice_desc": "Load real-world CSV files, perform group-by aggregations, and compute descriptive statistics.",
        "practice_duration": "1.5 hours (est.)",
    },
    "data-visualization": {
        "title": "Matplotlib Quick Start Guide",
        "url": "https://matplotlib.org/stable/users/explain/quick_start.html",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Study visual encoding, chart type selection, color blindness accessibility, and plot aesthetics.",
        "practice_title": "Exploratory Chart Dashboard",
        "practice_desc": "Create clear, annotated histograms, scatter plots, and time-series line charts with appropriate scales.",
        "practice_duration": "2 hours (est.)",
    },
    "exploratory-analysis": {
        "title": "Python Data Science Handbook: Exploratory Analysis",
        "url": "https://jakevdp.github.io/PythonDataScienceHandbook/",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Learn exploratory hypothesis generation, distribution checks, correlation analysis, and outlier detection.",
        "practice_title": "Dataset Exploration & Hypothesis Testing",
        "practice_desc": "Formulate 3 distinct business hypotheses and validate them against sample data distributions.",
        "practice_duration": "2 hours (est.)",
    },
    "statistics-basics": {
        "title": "OpenStax Introductory Statistics",
        "url": "https://openstax.org/details/books/introductory-statistics",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Understand mean, median, variance, standard deviation, normal distributions, and p-value significance.",
        "practice_title": "Statistical Metrics Calculation Lab",
        "practice_desc": "Compute central tendencies, interquartile ranges, and confidence intervals for skewed distributions.",
        "practice_duration": "1.5 hours (est.)",
    },
    "data-cleaning": {
        "title": "Pandas Documentation: Working with Missing Data",
        "url": "https://pandas.pydata.org/docs/user_guide/missing_data.html",
        "duration": "1 hour (est.)",
        "learn_objective": "Learn imputation strategies for missing values, deduplication, type casting, and outlier handling.",
        "practice_title": "Messy Data Cleaning Pipeline",
        "practice_desc": "Process a dataset containing missing fields, duplicate entries, and inconsistent date formats.",
        "practice_duration": "2 hours (est.)",
    },
    "user-research": {
        "title": "Nielsen Norman Group: UX Research Cheat Sheet",
        "url": "https://www.nngroup.com/articles/ux-research-cheat-sheet/",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Learn qualitative vs quantitative research methods, interview protocols, and survey bias reduction.",
        "practice_title": "User Persona & Journey Map Creation",
        "practice_desc": "Synthesize user interview notes into a comprehensive persona and journey pain-point map.",
        "practice_duration": "2 hours (est.)",
    },
    "wireframing-prototyping": {
        "title": "Interaction Design Foundation: Wireframing Guides",
        "url": "https://www.interaction-design.org/literature/topics/wireframing",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Master low-fidelity sketching, information hierarchy, layout zoning, and interactive click-throughs.",
        "practice_title": "Mid-Fidelity Interactive Flow",
        "practice_desc": "Wireframe a 3-step mobile checkout flow prioritizing clarity, error recovery, and minimal friction.",
        "practice_duration": "2 hours (est.)",
    },
    "design-systems": {
        "title": "Google Material Design 3 Guidelines",
        "url": "https://m3.material.io/",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Study design tokens: color palettes, typography scales, spacing grids, and component reusability.",
        "practice_title": "Atomic Design Component Kit",
        "practice_desc": "Design a reusable UI token set (buttons, input fields, badges) with consistent hover and active states.",
        "practice_duration": "2 hours (est.)",
    },
    "interaction-design": {
        "title": "Interaction Design Foundation: Interaction Principles",
        "url": "https://www.interaction-design.org/literature/topics/interaction-design",
        "duration": "1 hour (est.)",
        "learn_objective": "Learn affordances, signifiers, feedback loops, micro-interactions, and mental models.",
        "practice_title": "Interactive Feedback State Design",
        "practice_desc": "Design distinct loading, success, empty, and validation feedback states for complex UI actions.",
        "practice_duration": "1.5 hours (est.)",
    },
    "usability-testing": {
        "title": "Usability.gov: Usability Testing Guidelines",
        "url": "https://www.usability.gov/how-to-and-tools/methods/usability-testing.html",
        "duration": "1 hour (est.)",
        "learn_objective": "Learn think-aloud test protocols, task completion metrics, and usability severity ratings.",
        "practice_title": "Usability Test Protocol & Evaluation",
        "practice_desc": "Conduct a 3-task usability test on a prototype, log task completion time, and list severity-ranked fixes.",
        "practice_duration": "2 hours (est.)",
    },
    "test-planning": {
        "title": "ISTQB Certified Tester Foundation Level Syllabus",
        "url": "https://www.istqb.org/certifications/certified-tester-foundation-level",
        "duration": "1.5 hours (est.)",
        "learn_objective": "Study testing fundamentals: test pyramids, equivalence partitioning, boundary value analysis, and test suites.",
        "practice_title": "Test Strategy & Traceability Matrix",
        "practice_desc": "Author a test plan and requirement traceability matrix for a critical user authentication module.",
        "practice_duration": "2 hours (est.)",
    },
    "test-automation": {
        "title": "pytest Official Documentation: Getting Started",
        "url": "https://docs.pytest.org/en/stable/",
        "duration": "2 hours (est.)",
        "learn_objective": "Learn automated test structuring, assertions, test fixtures, parameterization, and mocking.",
        "practice_title": "Automated Regression Test Suite",
        "practice_desc": "Implement parametrized unit and functional tests covering success paths and edge cases.",
        "practice_duration": "2 hours (est.)",
    },
    "defect-reporting": {
        "title": "Software Testing Help: Defect Life Cycle & Bug Reporting",
        "url": "https://www.softwaretestinghelp.com/defect-life-cycle/",
        "duration": "1 hour (est.)",
        "learn_objective": "Learn bug severity vs priority, reproducible steps-to-reproduce, environment logs, and defect lifecycle.",
        "practice_title": "Comprehensive Defect Report Portfolio",
        "practice_desc": "Write 3 detailed bug reports containing reproduction steps, expected vs actual results, and logs.",
        "practice_duration": "1 hour (est.)",
    },
    "performance-testing": {
        "title": "Locust Load Testing Documentation",
        "url": "https://docs.locust.io/en/stable/",
        "duration": "1 hour (est.)",
        "learn_objective": "Understand throughput (RPS), response latency percentiles (p95, p99), bottlenecks, and concurrency.",
        "practice_title": "Load & Stress Test Simulation",
        "practice_desc": "Configure and execute a multi-user load test script and identify endpoint latency degradation thresholds.",
        "practice_duration": "1.5 hours (est.)",
    },
}

# Career Capstone Projects for the Build Stage
CAREER_CAPSTONES = {
    "frontend-dev": {
        "title": "Capstone Project: Responsive Interactive Web Application",
        "description": "Architect and code a complete, responsive multi-page web client. Incorporate accessible navigation, dynamic CSS Grid layouts, client-side input validation, and asynchronous JSON data fetching using vanilla JS.",
        "duration": "4 hours (est.)",
        "resource_title": "MDN Web Docs: Structuring the Web with HTML and CSS",
        "resource_url": "https://developer.mozilla.org/en-US/docs/Learn/HTML",
    },
    "backend-dev": {
        "title": "Capstone Project: Resilient RESTful API Service with SQLite",
        "description": "Design and build a production-grade REST API backend with modular blueprints, SQLite relational persistence, schema constraints, parameterized queries, and secure session authentication.",
        "duration": "4 hours (est.)",
        "resource_title": "Python Official Tutorial: Modules and Data Structures",
        "resource_url": "https://docs.python.org/3/tutorial/",
    },
    "fullstack-dev": {
        "title": "Capstone Project: End-to-End Full-Stack Task & Tracking System",
        "description": "Deliver a complete full-stack web application connecting responsive frontend components to a RESTful Python backend with SQLite persistence, user isolation, and structured error handling.",
        "duration": "5 hours (est.)",
        "resource_title": "MDN Web Docs: Working with Client-Side Web APIs",
        "resource_url": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Client-side_web_APIs/Introduction",
    },
    "data-analyst": {
        "title": "Capstone Project: End-to-End Business Performance Insights Report",
        "description": "Query raw multi-table operational data with complex SQL, clean and aggregate metrics using Pandas, and produce an explanatory visualization report answering key business questions.",
        "duration": "4 hours (est.)",
        "resource_title": "Mode Analytics: SQL Tutorial for Beginners & Advanced",
        "resource_url": "https://mode.com/sql-tutorial/",
    },
    "ui-ux-designer": {
        "title": "Capstone Project: End-to-End Mobile App Experience & Design System",
        "description": "Synthesize user research findings, craft an atomic design token system, and build high-fidelity interactive wireframe prototypes tested with representative usability tasks.",
        "duration": "4 hours (est.)",
        "resource_title": "Google Material Design 3 Guidelines",
        "resource_url": "https://m3.material.io/",
    },
    "software-qa-engineer": {
        "title": "Capstone Project: Automated End-to-End Test Suite & QA Pipeline",
        "description": "Author a comprehensive test strategy, develop automated regression test suites covering unit and API endpoints with pytest, and compile an actionable defect tracking log.",
        "duration": "4 hours (est.)",
        "resource_title": "pytest Official Documentation: Getting Started",
        "resource_url": "https://docs.pytest.org/en/stable/",
    },
}

# Skill prerequisite rank ordering (lower numbers are foundational)
SKILL_PREREQUISITE_ORDER = {
    # Frontend
    "html-css": 10,
    "javascript": 20,
    "responsive-design": 30,
    "git": 40,
    "frontend-frameworks": 50,
    "accessibility": 60,
    "web-performance": 70,
    # Backend
    "python-backend": 10,
    "relational-databases": 20,
    "rest-apis": 30,
    "auth-security": 40,
    "api-testing": 50,
    "system-architecture": 60,
    # Data Analyst
    "statistics-basics": 10,
    "sql-querying": 20,
    "python-data": 30,
    "data-cleaning": 40,
    "exploratory-analysis": 50,
    "data-visualization": 60,
    # UI/UX Designer
    "user-research": 10,
    "wireframing-prototyping": 20,
    "interaction-design": 30,
    "design-systems": 40,
    "usability-testing": 50,
    # Software QA Engineer
    "test-planning": 10,
    "defect-reporting": 20,
    "test-automation": 30,
    "performance-testing": 60,
}


# ---------------------------------------------------------------------------
# Core Service Functions
# ---------------------------------------------------------------------------

def generate_roadmap_for_user(db, user_id, career_id, refresh=False):
    """Generate or retrieve a personalized learning roadmap for a user and career.

    If an active roadmap already exists for this career:
    - If refresh=False: returns the existing roadmap without duplicating tasks.
    - If refresh=True: updates task descriptions/reasons to reflect latest assessment
      estimates while strictly preserving task completion status.

    If switching from another career:
    - Sets previously active roadmaps to is_active = 0.
    - Reactivates any existing historical roadmap for this career, or creates a new one.

    Args:
        db: SQLite database connection.
        user_id (int): Authenticated user ID.
        career_id (int): Target career ID.
        refresh (bool): Whether to regenerate/update tasks based on new assessments.

    Returns:
        int: The active roadmap ID.
    """
    # 1. Deactivate other active roadmaps for this user
    db.execute(
        "UPDATE roadmaps SET is_active = 0 WHERE user_id = ? AND career_id != ?",
        (user_id, career_id)
    )

    # 2. Check if a roadmap already exists for this user and career
    existing_roadmap = db.execute(
        "SELECT id, title, is_active FROM roadmaps WHERE user_id = ? AND career_id = ?",
        (user_id, career_id)
    ).fetchone()

    career_row = db.execute(
        "SELECT id, code, title FROM careers WHERE id = ?",
        (career_id,)
    ).fetchone()

    if not career_row:
        raise ValueError(f"Career with id {career_id} does not exist.")

    career_title = career_row['title']
    career_code = career_row['code']

    if existing_roadmap and not refresh:
        roadmap_id = existing_roadmap['id']
        if not existing_roadmap['is_active']:
            db.execute("UPDATE roadmaps SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (roadmap_id,))
            db.commit()
        return roadmap_id

    # Create new roadmap record if none exists
    if not existing_roadmap:
        cursor = db.execute(
            """
            INSERT INTO roadmaps (user_id, career_id, title, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (user_id, career_id, f"{career_title} Personalized Roadmap")
        )
        roadmap_id = cursor.lastrowid
        db.commit()
        completed_task_titles = set()
    else:
        roadmap_id = existing_roadmap['id']
        db.execute("UPDATE roadmaps SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (roadmap_id,))
        # Collect existing completed tasks to preserve completion status across refresh
        completed_rows = db.execute(
            "SELECT title FROM roadmap_tasks WHERE roadmap_id = ? AND is_completed = 1",
            (roadmap_id,)
        ).fetchall()
        completed_task_titles = {row['title'] for row in completed_rows}
        # Clear existing tasks to rebuild cleanly with updated assessment context
        db.execute("DELETE FROM roadmap_tasks WHERE roadmap_id = ?", (roadmap_id,))
        db.commit()

    # 3. Retrieve career skill requirements and user's current estimates
    reqs = db.execute(
        """
        SELECT csr.skill_id, csr.target_level, csr.importance_weight, csr.is_core,
               s.code as skill_code, s.name as skill_name, s.category,
               use.current_estimate, use.quiz_proficiency, use.self_assessed_level
        FROM career_skill_requirements csr
        JOIN skills s ON csr.skill_id = s.id
        LEFT JOIN user_skill_estimates use ON (csr.skill_id = use.skill_id AND use.user_id = ?)
        WHERE csr.career_id = ?
        """,
        (user_id, career_id)
    ).fetchall()

    # Sort requirements using prerequisite ordering and importance
    sorted_reqs = sorted(
        reqs,
        key=lambda r: (
            -r['is_core'],  # Core first
            SKILL_PREREQUISITE_ORDER.get(r['skill_code'], 50),  # Prerequisites first
            -r['importance_weight']  # Highest importance first
        )
    )

    tasks_to_insert = []
    order_counter = 1

    # -----------------------------------------------------------------------
    # STAGE 1: LEARN (Conceptual foundations, documentation, guided tutorials)
    # -----------------------------------------------------------------------
    for r in sorted_reqs:
        skill_id = r['skill_id']
        skill_code = r['skill_code']
        skill_name = r['skill_name']
        target_lvl = r['target_level']
        est = r['current_estimate']
        res_info = SKILL_LEARNING_RESOURCES.get(skill_code, {})

        # Determine personalized reasoning and objective
        if est is None or est == 0:
            reason = f"Unassessed {'core ' if r['is_core'] else ''}requirement for {career_title}. Foundational study recommended before assessment."
            learn_desc = f"Study fundamental principles and concepts of {skill_name}. {res_info.get('learn_objective', 'Build foundational conceptual clarity.')}"
        elif est < target_lvl:
            gap = round(target_lvl - est, 1)
            reason = f"Skill gap: Current estimate is {est:.1f}/5.0 vs Target {target_lvl}.0 ({gap} level gap to close)."
            learn_desc = f"Advance your understanding of {skill_name} from Level {int(est)} toward target Level {target_lvl}. {res_info.get('learn_objective', '')}"
        else:
            reason = f"Target achieved: Current estimate ({est:.1f}/5.0) meets career target ({target_lvl}.0). Review recommended for retention."
            learn_desc = f"Review modern patterns and best practices in {skill_name} to reinforce your target proficiency."

        task_title = f"Learn {skill_name}: Core Concepts & Documentation"
        is_comp = 1 if task_title in completed_task_titles else 0

        tasks_to_insert.append((
            roadmap_id,
            skill_id,
            'learn',
            task_title,
            learn_desc,
            res_info.get('duration', '1.5 hours (est.)'),
            order_counter,
            res_info.get('title', f"Official Documentation: {skill_name}"),
            res_info.get('url', "https://developer.mozilla.org/"),
            reason,
            0,  # is_project
            is_comp,
            datetime.now().isoformat() if is_comp else None
        ))
        order_counter += 1

    # -----------------------------------------------------------------------
    # STAGE 2: PRACTICE (Hands-on drills, problem sets, targeted code snippets)
    # -----------------------------------------------------------------------
    # Focus practice on core skills and skills with gaps
    for r in sorted_reqs:
        if r['is_core'] or (r['current_estimate'] is not None and r['current_estimate'] < r['target_level']):
            skill_id = r['skill_id']
            skill_code = r['skill_code']
            skill_name = r['skill_name']
            res_info = SKILL_LEARNING_RESOURCES.get(skill_code, {})

            practice_title = res_info.get('practice_title', f"Practice Exercise: {skill_name}")
            practice_desc = res_info.get('practice_desc', f"Complete practical exercises applying {skill_name} to real-world scenarios.")
            practice_duration = res_info.get('practice_duration', '1.5 hours (est.)')

            if r['current_estimate'] is not None and r['current_estimate'] < r['target_level']:
                p_reason = f"Active practice to close your remaining gap in {skill_name}."
            else:
                p_reason = f"Hands-on drill to build practical muscle memory in core skill {skill_name}."

            is_comp = 1 if practice_title in completed_task_titles else 0

            tasks_to_insert.append((
                roadmap_id,
                skill_id,
                'practice',
                practice_title,
                practice_desc,
                practice_duration,
                order_counter,
                res_info.get('title'),
                res_info.get('url'),
                p_reason,
                0,
                is_comp,
                datetime.now().isoformat() if is_comp else None
            ))
            order_counter += 1

    # -----------------------------------------------------------------------
    # STAGE 3: BUILD (Realistic capstone project milestone)
    # -----------------------------------------------------------------------
    capstone = CAREER_CAPSTONES.get(career_code, {
        "title": f"Capstone Project: {career_title} Production System",
        "description": f"Design, code, and deploy an end-to-end milestone project integrating the core skills required for a {career_title}.",
        "duration": "4 hours (est.)",
        "resource_title": "Project Specification & Guidelines",
        "resource_url": "https://developer.mozilla.org/",
    })

    capstone_title = capstone['title']
    capstone_comp = 1 if capstone_title in completed_task_titles else 0

    tasks_to_insert.append((
        roadmap_id,
        None,  # Multi-skill project
        'build',
        capstone_title,
        capstone['description'],
        capstone['duration'],
        order_counter,
        capstone['resource_title'],
        capstone['resource_url'],
        f"Culminating project milestone integrating key required skills for {career_title}.",
        1,  # is_project
        capstone_comp,
        datetime.now().isoformat() if capstone_comp else None
    ))
    order_counter += 1

    # -----------------------------------------------------------------------
    # STAGE 4: REVIEW (Code audit, documentation, and skill benchmark reassessment)
    # -----------------------------------------------------------------------
    review_tasks = [
        (
            f"Code Quality & Best Practices Audit ({career_title})",
            "Perform a structured self-audit of your capstone codebase: verify code clarity, edge-case handling, documentation, and accessibility/security guidelines.",
            "1 hour (est.)",
            "Google Engineering Practices Documentation",
            "https://google.github.io/eng-practices/",
            "Ensure production-readiness and code maintainability before presentation.",
            0
        ),
        (
            f"Reassess Skills & Benchmark Career Readiness",
            "Return to Skillora Skill Assessments to take or retake quizzes for your target skills. Measure your growth against the target proficiency levels and verify your updated Career Readiness score.",
            "45 mins (est.)",
            "Skillora Skill Assessments",
            "/assessment/",
            "Validates that hands-on learning translated into measurable, verified skill attainment.",
            0
        )
    ]

    for rev_title, rev_desc, rev_dur, rev_res_title, rev_res_url, rev_reason, is_proj in review_tasks:
        is_comp = 1 if rev_title in completed_task_titles else 0
        tasks_to_insert.append((
            roadmap_id,
            None,
            'review',
            rev_title,
            rev_desc,
            rev_dur,
            order_counter,
            rev_res_title,
            rev_res_url,
            rev_reason,
            is_proj,
            is_comp,
            datetime.now().isoformat() if is_comp else None
        ))
        order_counter += 1

    # Bulk insert all tasks
    db.executemany(
        """
        INSERT INTO roadmap_tasks (
            roadmap_id, skill_id, stage, title, description,
            estimated_duration, recommended_order, resource_title,
            resource_url, reason, is_project, is_completed, completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tasks_to_insert
    )
    db.commit()

    return roadmap_id


def get_user_active_roadmap(db, user_id):
    """Retrieve the full roadmap details, progress metrics, and tasks for a user's active career.

    Returns:
        dict or None: Roadmap structure, or None if user has no active roadmap or career.
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
        return None

    career_id = active_career['cid']

    # 2. Find or auto-generate active roadmap for this career
    roadmap_row = db.execute(
        "SELECT id, title, created_at, updated_at FROM roadmaps WHERE user_id = ? AND career_id = ? AND is_active = 1",
        (user_id, career_id)
    ).fetchone()

    if not roadmap_row:
        roadmap_id = generate_roadmap_for_user(db, user_id, career_id)
        roadmap_row = db.execute(
            "SELECT id, title, created_at, updated_at FROM roadmaps WHERE id = ?",
            (roadmap_id,)
        ).fetchone()
    else:
        roadmap_id = roadmap_row['id']

    # 3. Fetch all tasks for this roadmap
    tasks = db.execute(
        """
        SELECT rt.*, s.name as skill_name, s.code as skill_code
        FROM roadmap_tasks rt
        LEFT JOIN skills s ON rt.skill_id = s.id
        WHERE rt.roadmap_id = ?
        ORDER BY rt.recommended_order ASC
        """,
        (roadmap_id,)
    ).fetchall()

    # 4. Compute overall and per-stage progress
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t['is_completed'])
    overall_progress = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    stages = {
        'learn': {'title': 'Learn', 'icon': '📚', 'tasks': [], 'completed': 0, 'total': 0, 'progress': 0},
        'practice': {'title': 'Practice', 'icon': '⚡', 'tasks': [], 'completed': 0, 'total': 0, 'progress': 0},
        'build': {'title': 'Build', 'icon': '🛠️', 'tasks': [], 'completed': 0, 'total': 0, 'progress': 0},
        'review': {'title': 'Review', 'icon': '🔍', 'tasks': [], 'completed': 0, 'total': 0, 'progress': 0},
    }

    next_recommended_task = None

    for task in tasks:
        stage_key = task['stage']
        if stage_key in stages:
            stages[stage_key]['tasks'].append(task)
            stages[stage_key]['total'] += 1
            if task['is_completed']:
                stages[stage_key]['completed'] += 1
            elif next_recommended_task is None:
                next_recommended_task = task

    for s_key in stages:
        t = stages[s_key]['total']
        c = stages[s_key]['completed']
        stages[s_key]['progress'] = round((c / t * 100)) if t > 0 else 0

    # 5. Fetch readiness and assessment coverage context
    from assessment_engine import calculate_career_readiness
    reqs = db.execute(
        """
        SELECT csr.skill_id, csr.target_level, csr.importance_weight, csr.is_core,
               use.current_estimate
        FROM career_skill_requirements csr
        LEFT JOIN user_skill_estimates use ON (csr.skill_id = use.skill_id AND use.user_id = ?)
        WHERE csr.career_id = ?
        """,
        (user_id, career_id)
    ).fetchall()

    reqs_list = []
    user_estimates = {}
    for r in reqs:
        reqs_list.append({
            'skill_id': r['skill_id'],
            'target_level': r['target_level'],
            'importance_weight': r['importance_weight'],
            'is_core': r['is_core']
        })
        if r['current_estimate'] is not None and r['current_estimate'] > 0:
            user_estimates[r['skill_id']] = r['current_estimate']

    readiness = calculate_career_readiness(reqs_list, user_estimates)

    return {
        'roadmap_id': roadmap_id,
        'title': roadmap_row['title'],
        'career': active_career,
        'stages': stages,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overall_progress': overall_progress,
        'next_recommended_task': next_recommended_task,
        'readiness': readiness,
        'is_provisional': readiness['is_provisional'] if readiness else False,
        'coverage_percentage': readiness['coverage_percentage'] if readiness else 0,
        'unassessed_count': (readiness['total_skills_count'] - readiness['assessed_skills_count']) if readiness else 0,
    }



def toggle_task_completion(db, user_id, task_id):
    """Toggle the completion status of a roadmap task for the authenticated user.

    Strict rule: Updates ONLY roadmap_tasks (is_completed and completed_at).
    Never modifies skill proficiency, assessment history, or career readiness.

    Args:
        db: SQLite database connection.
        user_id (int): Authenticated user ID.
        task_id (int): ID of the task to toggle.

    Returns:
        dict: Updated task status ('is_completed', 'stage', 'title').

    Raises:
        PermissionError: If the task does not belong to the user's roadmap.
        ValueError: If the task does not exist.
    """
    task = db.execute(
        """
        SELECT rt.id, rt.roadmap_id, rt.stage, rt.title, rt.is_completed, r.user_id
        FROM roadmap_tasks rt
        JOIN roadmaps r ON rt.roadmap_id = r.id
        WHERE rt.id = ?
        """,
        (task_id,)
    ).fetchone()

    if not task:
        raise ValueError(f"Task with id {task_id} not found.")

    if task['user_id'] != user_id:
        raise PermissionError("You do not have permission to modify this roadmap task.")

    new_status = 0 if task['is_completed'] else 1
    completed_at = datetime.now().isoformat() if new_status == 1 else None

    db.execute(
        """
        UPDATE roadmap_tasks
        SET is_completed = ?, completed_at = ?
        WHERE id = ?
        """,
        (new_status, completed_at, task_id)
    )
    db.commit()

    return {
        'task_id': task_id,
        'is_completed': new_status,
        'stage': task['stage'],
        'title': task['title']
    }
