"""Data seeding script and data definitions for Skillora.

Seeds the 6 target careers, modular skills, and skill requirements with
explicit target proficiency levels (1-5), positive importance weights,
and core/supplementary classifications.
"""

from db import get_db

CAREERS_DATA = [
    {
        "code": "frontend-dev",
        "title": "Frontend Developer",
        "icon": "💻",
        "description": "Build responsive, accessible, and high-performance user interfaces for modern web applications.",
        "skills": [
            {"code": "html-css", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "javascript", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "responsive-design", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "frontend-frameworks", "target": 3, "weight": 2.5, "is_core": 1},
            {"code": "git", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "web-performance", "target": 3, "weight": 1.5, "is_core": 0},
            {"code": "accessibility", "target": 3, "weight": 1.5, "is_core": 0},
        ]
    },
    {
        "code": "backend-dev",
        "title": "Backend Developer",
        "icon": "⚙️",
        "description": "Design resilient server architectures, scalable APIs, and secure business logic and data persistence.",
        "skills": [
            {"code": "python-backend", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "relational-databases", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "rest-apis", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "auth-security", "target": 3, "weight": 2.5, "is_core": 1},
            {"code": "git", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "api-testing", "target": 3, "weight": 1.5, "is_core": 0},
            {"code": "system-architecture", "target": 3, "weight": 1.5, "is_core": 0},
        ]
    },
    {
        "code": "fullstack-dev",
        "title": "Full-Stack Developer",
        "icon": "🔗",
        "description": "Deliver end-to-end web applications across client interfaces, backend services, and relational databases.",
        "skills": [
            {"code": "javascript", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "python-backend", "target": 3, "weight": 2.5, "is_core": 1},
            {"code": "html-css", "target": 3, "weight": 2.0, "is_core": 1},
            {"code": "relational-databases", "target": 3, "weight": 2.5, "is_core": 1},
            {"code": "rest-apis", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "git", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "auth-security", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "frontend-frameworks", "target": 3, "weight": 2.0, "is_core": 0},
        ]
    },
    {
        "code": "data-analyst",
        "title": "Data Analyst",
        "icon": "📊",
        "description": "Transform raw datasets into actionable insights through statistical analysis, SQL querying, and visualizations.",
        "skills": [
            {"code": "sql-querying", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "python-data", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "data-visualization", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "exploratory-analysis", "target": 3, "weight": 2.5, "is_core": 1},
            {"code": "statistics-basics", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "data-cleaning", "target": 4, "weight": 2.0, "is_core": 0},
        ]
    },
    {
        "code": "ui-ux-designer",
        "title": "UI/UX Designer",
        "icon": "🎨",
        "description": "Craft intuitive user journeys, wireframes, interaction prototypes, and cohesive visual design systems.",
        "skills": [
            {"code": "user-research", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "wireframing-prototyping", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "design-systems", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "interaction-design", "target": 3, "weight": 2.5, "is_core": 1},
            {"code": "accessibility", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "usability-testing", "target": 3, "weight": 2.0, "is_core": 0},
        ]
    },
    {
        "code": "software-qa-engineer",
        "title": "Software QA Engineer",
        "icon": "🧪",
        "description": "Ensure software quality and stability through test automation, defect prevention, and regression testing.",
        "skills": [
            {"code": "test-planning", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "test-automation", "target": 4, "weight": 3.0, "is_core": 1},
            {"code": "api-testing", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "defect-reporting", "target": 4, "weight": 2.5, "is_core": 1},
            {"code": "git", "target": 3, "weight": 2.0, "is_core": 0},
            {"code": "performance-testing", "target": 3, "weight": 1.5, "is_core": 0},
        ]
    }
]

SKILLS_DATA = [
    {"code": "html-css", "name": "HTML5 & Modern CSS", "category": "Frontend", "description": "Semantic markup, CSS Grid, Flexbox, variables, and responsive layout styling."},
    {"code": "javascript", "name": "JavaScript (ES6+)", "category": "Frontend", "description": "DOM manipulation, asynchronous operations, promises, and modern syntax patterns."},
    {"code": "responsive-design", "name": "Responsive Web Design", "category": "Frontend", "description": "Media queries, mobile-first design, fluid layouts, and cross-device testing."},
    {"code": "frontend-frameworks", "name": "Frontend Frameworks & Components", "category": "Frontend", "description": "Component hierarchies, reactive state patterns, and lifecycle handling."},
    {"code": "web-performance", "name": "Web Performance & Core Vitals", "category": "Frontend", "description": "Asset optimization, critical rendering path, caching, and LCP/FID tuning."},
    {"code": "accessibility", "name": "Web Accessibility (WCAG & ARIA)", "category": "Design & Frontend", "description": "Screen-reader compatibility, keyboard navigation, color contrast, and ARIA roles."},
    {"code": "python-backend", "name": "Python Backend Architecture", "category": "Backend", "description": "Flask/FastAPI, routing, dependency injection, and middleware orchestration."},
    {"code": "relational-databases", "name": "Relational Databases & SQL", "category": "Backend", "description": "Schema modeling, normalization, transactions, indexing, and SQL queries."},
    {"code": "rest-apis", "name": "RESTful API Design & Integration", "category": "Backend", "description": "Resource naming, HTTP status codes, pagination, and payload validation."},
    {"code": "auth-security", "name": "Authentication & App Security", "category": "Backend", "description": "Password hashing, session handling, CSRF defense, and least privilege."},
    {"code": "system-architecture", "name": "Backend System Design", "category": "Backend", "description": "Layered architecture, error handling strategies, and horizontal scaling basics."},
    {"code": "git", "name": "Version Control with Git", "category": "General Engineering", "description": "Branching workflows, commits, conflict resolution, and PR review practices."},
    {"code": "sql-querying", "name": "Advanced SQL for Analytics", "category": "Data", "description": "Complex joins, window functions, CTEs, and aggregation pipelines."},
    {"code": "python-data", "name": "Data Analysis with Python", "category": "Data", "description": "Data wrangling, tabular manipulation, and numeric computing."},
    {"code": "data-visualization", "name": "Data Visualization & Dashboards", "category": "Data", "description": "Chart design, metric presentation, storytelling, and visual clarity."},
    {"code": "exploratory-analysis", "name": "Exploratory Data Analysis (EDA)", "category": "Data", "description": "Hypothesis generation, anomaly detection, and summary statistics."},
    {"code": "statistics-basics", "name": "Applied Statistics & Probability", "category": "Data", "description": "Distributions, sampling, correlation, and significance testing."},
    {"code": "data-cleaning", "name": "Data Cleaning & Preparation", "category": "Data", "description": "Missing values imputation, outlier handling, and format standardization."},
    {"code": "user-research", "name": "User Research & Personas", "category": "Design", "description": "User interviews, surveys, empathy mapping, and user journey definition."},
    {"code": "wireframing-prototyping", "name": "Wireframing & Interactive Prototyping", "category": "Design", "description": "Low-to-high fidelity prototyping, click-through flows, and mockups."},
    {"code": "design-systems", "name": "Design Systems & UI Kits", "category": "Design", "description": "Color tokens, typography scale, component libraries, and style guides."},
    {"code": "interaction-design", "name": "Interaction Design & Micro-interactions", "category": "Design", "description": "State transitions, feedback cues, animation timing, and ergonomics."},
    {"code": "usability-testing", "name": "Usability Testing & Evaluation", "category": "Design", "description": "Task-based evaluation, heuristic audits, and user observation synthesis."},
    {"code": "test-planning", "name": "Test Strategy & Test Cases", "category": "QA", "description": "Test matrices, boundary condition analysis, and risk-based test planning."},
    {"code": "test-automation", "name": "Automated Testing Frameworks", "category": "QA", "description": "Unit, integration, and end-to-end automated test suites."},
    {"code": "api-testing", "name": "API Testing & Validation", "category": "QA", "description": "Endpoint contracts, status verification, payload validation, and mocking."},
    {"code": "defect-reporting", "name": "Bug Reporting & Defect Tracking", "category": "QA", "description": "Reproduction steps, severity vs priority triage, and issue lifecycle."},
    {"code": "performance-testing", "name": "Performance & Load Testing", "category": "QA", "description": "Response time profiling, stress testing, and throughput measurement."}
]


def seed_careers_and_skills(db=None):
    """Safely and repeatably seeds careers, skills, and career_skill_requirements.
    
    Can be run repeatedly without creating duplicates or altering existing users.
    """
    if db is None:
        db = get_db()

    # 1. Seed or update skills
    skill_id_map = {}
    for s in SKILLS_DATA:
        db.execute(
            """
            INSERT INTO skills (code, name, category, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                description = excluded.description
            """,
            (s["code"], s["name"], s["category"], s["description"])
        )
    db.commit()

    # Build skill code -> id map
    rows = db.execute("SELECT id, code FROM skills").fetchall()
    for row in rows:
        skill_id_map[row["code"]] = row["id"]

    # 2. Seed or update careers
    career_id_map = {}
    for c in CAREERS_DATA:
        db.execute(
            """
            INSERT INTO careers (code, title, icon, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                title = excluded.title,
                icon = excluded.icon,
                description = excluded.description
            """,
            (c["code"], c["title"], c["icon"], c["description"])
        )
    db.commit()

    rows = db.execute("SELECT id, code FROM careers").fetchall()
    for row in rows:
        career_id_map[row["code"]] = row["id"]

    # 3. Seed career-skill requirements
    for c in CAREERS_DATA:
        c_id = career_id_map[c["code"]]
        for req in c["skills"]:
            s_id = skill_id_map[req["code"]]
            db.execute(
                """
                INSERT INTO career_skill_requirements (career_id, skill_id, target_level, importance_weight, is_core)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(career_id, skill_id) DO UPDATE SET
                    target_level = excluded.target_level,
                    importance_weight = excluded.importance_weight,
                    is_core = excluded.is_core
                """,
                (c_id, s_id, req["target"], req["weight"], req["is_core"])
            )
    db.commit()

    # 4. Seed question bank
    seed_questions(db, skill_id_map)


QUESTIONS_DATA = [
    # --- HTML5 & Modern CSS ---
    {
        "skill_code": "html-css",
        "question_text": "Which CSS display property establishes a two-dimensional grid-based layout container?",
        "option_a": "display: flex",
        "option_b": "display: grid",
        "option_c": "display: table-row",
        "option_d": "display: inline-block",
        "correct_option": "B",
        "explanation": "CSS Grid is a two-dimensional layout system for both rows and columns, whereas Flexbox is primarily one-dimensional.",
        "difficulty_level": 2
    },
    {
        "skill_code": "html-css",
        "question_text": "In semantic HTML5, which element is specifically designated for enclosing primary navigational links?",
        "option_a": "<menu>",
        "option_b": "<nav>",
        "option_c": "<section>",
        "option_d": "<aside>",
        "correct_option": "B",
        "explanation": "The <nav> element represents a section of a page whose purpose is to provide navigation links.",
        "difficulty_level": 1
    },
    {
        "skill_code": "html-css",
        "question_text": "What is the effect of setting 'box-sizing: border-box' in CSS?",
        "option_a": "Margin and padding are included inside the specified width and height",
        "option_b": "Padding and border are included inside the specified width and height",
        "option_c": "Border is completely excluded from width calculation",
        "option_d": "The box shadow is rendered inside the element content area",
        "correct_option": "B",
        "explanation": "With border-box, the width and height properties include content, padding, and border, making responsive sizing predictable.",
        "difficulty_level": 2
    },
    {
        "skill_code": "html-css",
        "question_text": "Which of the following CSS selectors carries the highest specificity?",
        "option_a": "div.container .btn-primary",
        "option_b": "#main-navigation",
        "option_c": "button[type='submit']:hover",
        "option_d": "body main section ul li a",
        "correct_option": "B",
        "explanation": "An ID selector (#id) carries specificity (1, 0, 0), which overrides any combination of class, attribute, or element selectors.",
        "difficulty_level": 3
    },

    # --- JavaScript (ES6+) ---
    {
        "skill_code": "javascript",
        "question_text": "What does the expression 'typeof null' evaluate to in JavaScript?",
        "option_a": "'null'",
        "option_b": "'undefined'",
        "option_c": "'object'",
        "option_d": "'boolean'",
        "correct_option": "C",
        "explanation": "In JavaScript, 'typeof null' historically returns 'object'. This is a well-known legacy quirk in the language.",
        "difficulty_level": 2
    },
    {
        "skill_code": "javascript",
        "question_text": "Which Array method returns a new array with the results of applying a callback function to each element?",
        "option_a": "Array.prototype.forEach()",
        "option_b": "Array.prototype.map()",
        "option_c": "Array.prototype.filter()",
        "option_d": "Array.prototype.reduce()",
        "correct_option": "B",
        "explanation": "map() transforms elements and returns a new array without mutating the original array.",
        "difficulty_level": 2
    },
    {
        "skill_code": "javascript",
        "question_text": "What is the primary scoping difference between 'let' and 'var'?",
        "option_a": "'let' is function-scoped; 'var' is block-scoped",
        "option_b": "'let' is block-scoped; 'var' is function-scoped",
        "option_c": "'let' declarations cannot be reassigned; 'var' can",
        "option_d": "'let' attaches variables to the global window object in browsers",
        "correct_option": "B",
        "explanation": "'let' and 'const' are block-scoped ({ ... }), whereas 'var' variables are scoped to their enclosing function or global scope.",
        "difficulty_level": 2
    },
    {
        "skill_code": "javascript",
        "question_text": "When a Promise fails or encounters an unhandled exception, what state does it transition into?",
        "option_a": "Pending",
        "option_b": "Fulfilled",
        "option_c": "Rejected",
        "option_d": "Settled-Empty",
        "correct_option": "C",
        "explanation": "A Promise transitions from Pending to either Fulfilled (resolved) or Rejected (failed).",
        "difficulty_level": 3
    },
    {
        "skill_code": "javascript",
        "question_text": "What is evaluated by the strict equality operator (===)?",
        "option_a": "Value equality after automatic type coercion",
        "option_b": "Type equality only, ignoring values",
        "option_c": "Both value and type equality without type coercion",
        "option_d": "Object memory address equality for all primitives",
        "correct_option": "C",
        "explanation": "Strict equality (===) compares both type and value without performing implicit type coercion.",
        "difficulty_level": 1
    },

    # --- Python Backend Architecture ---
    {
        "skill_code": "python-backend",
        "question_text": "In Flask, which decorator connects a URL path to a controller view function?",
        "option_a": "@app.route()",
        "option_b": "@app.controller()",
        "option_c": "@app.endpoint()",
        "option_d": "@app.handle()",
        "correct_option": "A",
        "explanation": "@app.route('/path') registers a view function for a specific URL endpoint.",
        "difficulty_level": 1
    },
    {
        "skill_code": "python-backend",
        "question_text": "Which standard HTTP status code should be returned when a client attempts to access a protected route without valid authentication credentials?",
        "option_a": "400 Bad Request",
        "option_b": "401 Unauthorized",
        "option_c": "403 Forbidden",
        "option_d": "405 Method Not Allowed",
        "correct_option": "B",
        "explanation": "HTTP 401 Unauthorized indicates that the request requires user authentication credentials that were missing or invalid.",
        "difficulty_level": 2
    },
    {
        "skill_code": "python-backend",
        "question_text": "Why should production user passwords be hashed with salted key-derivation functions (like scrypt/bcrypt) rather than fast hashes like MD5 or SHA-256?",
        "option_a": "Salted slow hashes resist GPU-accelerated brute-force and precomputed rainbow table attacks",
        "option_b": "SHA-256 cannot hash strings containing numbers",
        "option_c": "MD5 and SHA-256 are reversible using standard decompression utilities",
        "option_d": "Operating systems prohibit storing SHA-256 strings in SQLite",
        "correct_option": "A",
        "explanation": "Key-derivation functions include random per-user salts and configurable computational cost to defend against brute-force attacks.",
        "difficulty_level": 3
    },
    {
        "skill_code": "python-backend",
        "question_text": "What is the role of Flask's application context (app.app_context())?",
        "option_a": "It manages client web-socket streaming connections",
        "option_b": "It binds application-level proxies like current_app and g when executing outside an active HTTP request",
        "option_c": "It automatically compresses HTTP responses with gzip",
        "option_d": "It compiles Python byte-code to machine code",
        "correct_option": "B",
        "explanation": "The application context makes application-level state and extensions available in CLI commands, background tasks, and tests.",
        "difficulty_level": 3
    },

    # --- Relational Databases & SQL ---
    {
        "skill_code": "relational-databases",
        "question_text": "What does the 'A' in the ACID database transaction properties represent?",
        "option_a": "Availability",
        "option_b": "Atomicity",
        "option_c": "Authentication",
        "option_d": "Asynchrony",
        "correct_option": "B",
        "explanation": "Atomicity guarantees that all operations within a transaction succeed together or are completely rolled back ('all-or-nothing').",
        "difficulty_level": 2
    },
    {
        "skill_code": "relational-databases",
        "question_text": "Which normal form requires eliminating transitive dependencies so that non-key attributes depend only on candidate keys?",
        "option_a": "First Normal Form (1NF)",
        "option_b": "Second Normal Form (2NF)",
        "option_c": "Third Normal Form (3NF)",
        "option_d": "Domain-Key Normal Form (DKNF)",
        "correct_option": "C",
        "explanation": "3NF requires a table to be in 2NF and have no transitive functional dependencies between non-prime attributes.",
        "difficulty_level": 3
    },
    {
        "skill_code": "relational-databases",
        "question_text": "In SQLite, what pragma command must be executed to enforce foreign key constraints?",
        "option_a": "PRAGMA foreign_keys = ON",
        "option_b": "PRAGMA enforce_integrity = TRUE",
        "option_c": "PRAGMA strict_mode = ENABLE",
        "option_d": "PRAGMA check_references = YES",
        "correct_option": "A",
        "explanation": "SQLite turns foreign key enforcement off by default for backwards compatibility; 'PRAGMA foreign_keys = ON' enables it per connection.",
        "difficulty_level": 3
    },
    {
        "skill_code": "relational-databases",
        "question_text": "Which SQL clause filters groups produced by an aggregate function (such as COUNT or AVG)?",
        "option_a": "WHERE",
        "option_b": "HAVING",
        "option_c": "ORDER BY",
        "option_d": "LIMIT",
        "correct_option": "B",
        "explanation": "WHERE filters rows before aggregation; HAVING filters aggregated groups after GROUP BY.",
        "difficulty_level": 2
    },

    # --- Advanced SQL for Analytics ---
    {
        "skill_code": "sql-querying",
        "question_text": "Which window function assigns contiguous sequential ranks without gaps when tied values occur?",
        "option_a": "RANK()",
        "option_b": "DENSE_RANK()",
        "option_c": "ROW_NUMBER()",
        "option_d": "PERCENT_RANK()",
        "correct_option": "B",
        "explanation": "DENSE_RANK() assigns ranks without gaps in the sequence (e.g., 1, 2, 2, 3), whereas RANK() leaves gaps (1, 2, 2, 4).",
        "difficulty_level": 3
    },
    {
        "skill_code": "sql-querying",
        "question_text": "What is the primary utility of a Common Table Expression (CTE) defined with 'WITH' in SQL?",
        "option_a": "To physically persist a materialized index on disk",
        "option_b": "To define a readable, reusable temporary named result set within the scope of a single query",
        "option_c": "To bypass column data type validation constraints",
        "option_d": "To encrypt sensitive query parameters in the database log",
        "correct_option": "B",
        "explanation": "CTEs simplify complex joins and aggregations by structuring queries into modular named components.",
        "difficulty_level": 2
    },
    {
        "skill_code": "sql-querying",
        "question_text": "What is the operational difference between 'UNION' and 'UNION ALL' in SQL?",
        "option_a": "'UNION' includes duplicate rows; 'UNION ALL' removes duplicates",
        "option_b": "'UNION' removes duplicate rows by performing a distinct sort; 'UNION ALL' retains all duplicate rows",
        "option_c": "'UNION' can only combine tables from different schemas",
        "option_d": "'UNION ALL' operates strictly on numeric columns",
        "correct_option": "B",
        "explanation": "'UNION' performs deduplication which incurs sorting overhead; 'UNION ALL' concatenates result sets directly with duplicates preserved.",
        "difficulty_level": 2
    },
    {
        "skill_code": "sql-querying",
        "question_text": "In a SQL query, what does the window clause 'OVER (PARTITION BY department_id ORDER BY salary DESC)' accomplish?",
        "option_a": "It deletes duplicate department rows",
        "option_b": "It defines a window frame isolated to each department with rows ordered by salary descending",
        "option_c": "It forces an index scan on the primary key",
        "option_d": "It returns only the top 1 row per department",
        "correct_option": "B",
        "explanation": "PARTITION BY subdivides the result set into distinct partitions, and ORDER BY establishes the sequence of evaluation within each partition.",
        "difficulty_level": 4
    },

    # --- User Research & Personas ---
    {
        "skill_code": "user-research",
        "question_text": "What is the primary objective of qualitative user interviews during discovery?",
        "option_a": "To validate statistical sample sizes across thousands of anonymous respondents",
        "option_b": "To uncover user motivations, pain points, mental models, and contextual workflows",
        "option_c": "To finalize pixel-perfect visual color tokens",
        "option_d": "To benchmark database query latency",
        "correct_option": "B",
        "explanation": "Qualitative interviews provide deep contextual insight into user motivations, mental models, and unarticulated friction points.",
        "difficulty_level": 2
    },
    {
        "skill_code": "user-research",
        "question_text": "In user-centered design, what is a 'User Persona'?",
        "option_a": "A fictional composite character synthesizing empirical behavioral patterns from real research",
        "option_b": "A direct copy of an individual customer's real confidential contact record",
        "option_c": "A list of marketing slogans approved by stakeholders",
        "option_d": "A CSS layout stylesheet representing visual styles",
        "correct_option": "A",
        "explanation": "Personas are evidence-grounded archetype models representing common needs, goals, and behavioral patterns of target user groups.",
        "difficulty_level": 1
    },
    {
        "skill_code": "user-research",
        "question_text": "Which testing methodology asks participants to speak their thoughts, feelings, and rationale out loud while executing representative tasks?",
        "option_a": "Think-Aloud Usability Protocol",
        "option_b": "A/B Multivariant Testing",
        "option_c": "Card Sorting Assessment",
        "option_d": "Semantic Differential Surveying",
        "correct_option": "A",
        "explanation": "The think-aloud protocol gives researchers direct visibility into user comprehension, expectations, and cognitive friction in real time.",
        "difficulty_level": 2
    },
    {
        "skill_code": "user-research",
        "question_text": "According to Jakob Nielsen's foundational usability engineering research, approximately how many participants are typically sufficient to identify ~80% of usability flaws in an iterative test?",
        "option_a": "5 participants",
        "option_b": "50 participants",
        "option_c": "200 participants",
        "option_d": "1,000 participants",
        "correct_option": "A",
        "explanation": "Nielsen showed that 5 qualitative testing participants uncover approximately 85% of core usability issues before diminishing returns set in.",
        "difficulty_level": 3
    },

    # --- Automated Testing Frameworks ---
    {
        "skill_code": "test-automation",
        "question_text": "In the standard Test Automation Pyramid model, which layer should contain the largest volume of tests?",
        "option_a": "Manual exploratory tests",
        "option_b": "End-to-end browser UI tests",
        "option_c": "Integration tests",
        "option_d": "Fast, isolated Unit tests",
        "correct_option": "D",
        "explanation": "Unit tests form the broad foundation: they execute in milliseconds, isolate specific units of logic, and are inexpensive to maintain.",
        "difficulty_level": 2
    },
    {
        "skill_code": "test-automation",
        "question_text": "In automated testing frameworks like pytest, what is a 'test fixture'?",
        "option_a": "A defect that cannot be reproduced locally",
        "option_b": "A reusable mechanism that provides fixed baseline preconditions, resources, or configurations to tests",
        "option_c": "A production deployment script",
        "option_d": "A linter error that prevents test execution",
        "correct_option": "B",
        "explanation": "Fixtures initialize databases, mock dependencies, create sample data, and cleanly tear them down after test completion.",
        "difficulty_level": 2
    },
    {
        "skill_code": "test-automation",
        "question_text": "What distinguishes a 'Mock' from a 'Stub' in automated testing test doubles?",
        "option_a": "Mocks verify that specific interactions and methods occurred; Stubs provide predefined canned responses without verifying calls",
        "option_b": "Stubs can only test frontend code; Mocks can only test backend code",
        "option_c": "Mocks run exclusively in production; Stubs run only in development",
        "option_d": "There is no difference; they are exact synonyms",
        "correct_option": "A",
        "explanation": "Mocks are used for behavioral verification (verifying how an object was called), while stubs supply state without assertions on interaction.",
        "difficulty_level": 3
    },
    {
        "skill_code": "test-automation",
        "question_text": "What is the primary objective of regression testing?",
        "option_a": "To ensure software continues to work properly after changes, bug fixes, or enhancements have been introduced",
        "option_b": "To stress test network hardware under peak traffic",
        "option_c": "To convert Python source code into compiled binaries",
        "option_d": "To test visual appearance on unsupported legacy monitors",
        "correct_option": "A",
        "explanation": "Regression testing ensures that recent modifications have not inadvertently broken existing, previously working features.",
        "difficulty_level": 1
    },

    # --- Version Control with Git ---
    {
        "skill_code": "git",
        "question_text": "Which Git command simultaneously creates a new branch and checks it out?",
        "option_a": "git branch -new <name>",
        "option_b": "git checkout -b <name>",
        "option_c": "git switch --force <name>",
        "option_d": "git commit -b <name>",
        "correct_option": "B",
        "explanation": "'git checkout -b <name>' (or 'git switch -c <name>') creates the specified branch and switches the working directory to it.",
        "difficulty_level": 1
    },
    {
        "skill_code": "git",
        "question_text": "What role does the Git 'Staging Area' (Index) serve?",
        "option_a": "It acts as a temporary trash can for deleted branches",
        "option_b": "It is an intermediate staging area where changes are organized and reviewed before being recorded into a commit",
        "option_c": "It is the remote server hosting GitHub or GitLab repositories",
        "option_d": "It compiles Git hooks into native shell scripts",
        "correct_option": "B",
        "explanation": "The staging area allows developers to selectively compose granular commits rather than committing all modified files at once.",
        "difficulty_level": 2
    },
    {
        "skill_code": "git",
        "question_text": "What does 'git pull' execute behind the scenes?",
        "option_a": "'git fetch' followed by 'git merge' into the current branch",
        "option_b": "'git clone' followed by 'git push'",
        "option_c": "'git reset --hard' to match the remote branch",
        "option_d": "'git checkout' of the main branch",
        "correct_option": "A",
        "explanation": "'git pull' downloads new remote commits with 'git fetch' and merges them into the current active local branch.",
        "difficulty_level": 2
    },
    {
        "skill_code": "git",
        "question_text": "What is the core distinction between 'git rebase' and 'git merge'?",
        "option_a": "Rebase creates a 3-way merge commit; Merge rewrites branch commit timestamps",
        "option_b": "Rebase reapplies commits on top of another base tip for a linear history; Merge joins two branch histories together with a merge commit",
        "option_c": "Rebase permanently deletes uncommitted working directory files",
        "option_d": "Merge can only be used on the master branch",
        "correct_option": "B",
        "explanation": "Rebase re-plays commits sequentially on top of another branch tip, producing a clean linear project history.",
        "difficulty_level": 3
    }
]


def seed_questions(db, skill_id_map):
    """Seed starter curated question bank for representative skills."""
    for q in QUESTIONS_DATA:
        s_id = skill_id_map.get(q["skill_code"])
        if not s_id:
            continue

        # Check if question already exists for this skill
        existing = db.execute(
            "SELECT id FROM questions WHERE skill_id = ? AND question_text = ?",
            (s_id, q["question_text"])
        ).fetchone()

        if existing:
            db.execute(
                """
                UPDATE questions SET
                    option_a = ?, option_b = ?, option_c = ?, option_d = ?,
                    correct_option = ?, explanation = ?, difficulty_level = ?
                WHERE id = ?
                """,
                (q["option_a"], q["option_b"], q["option_c"], q["option_d"],
                 q["correct_option"], q["explanation"], q["difficulty_level"],
                 existing["id"])
            )
        else:
            db.execute(
                """
                INSERT INTO questions (
                    skill_id, question_text, option_a, option_b, option_c, option_d,
                    correct_option, explanation, difficulty_level
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (s_id, q["question_text"], q["option_a"], q["option_b"],
                 q["option_c"], q["option_d"], q["correct_option"],
                 q["explanation"], q["difficulty_level"])
            )
    db.commit()

