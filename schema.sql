-- Skillora Database Schema
-- Foundation: Users and Authentication

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_demo_account INTEGER DEFAULT 0
);

-- Milestone 2: Career Profiles & Skill Requirements
CREATE TABLE IF NOT EXISTS careers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS career_skill_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    career_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    target_level INTEGER NOT NULL CHECK (target_level >= 1 AND target_level <= 5),
    importance_weight REAL NOT NULL CHECK (importance_weight > 0),
    is_core INTEGER NOT NULL DEFAULT 1 CHECK (is_core IN (0, 1)),
    FOREIGN KEY (career_id) REFERENCES careers (id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE,
    UNIQUE (career_id, skill_id)
);

CREATE TABLE IF NOT EXISTS career_selections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    career_id INTEGER,
    career_path TEXT NOT NULL,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (career_id) REFERENCES careers (id)
);

-- Milestone 3: Assessment Engine & Question Bank
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
    explanation TEXT,
    difficulty_level INTEGER DEFAULT 3 CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessment_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    score_percentage REAL NOT NULL,
    quiz_proficiency INTEGER NOT NULL CHECK (quiz_proficiency >= 1 AND quiz_proficiency <= 5),
    self_assessed_level INTEGER CHECK (self_assessed_level IS NULL OR (self_assessed_level >= 1 AND self_assessed_level <= 5)),
    combined_estimate REAL,
    has_discrepancy INTEGER NOT NULL DEFAULT 0 CHECK (has_discrepancy IN (0, 1)),
    discrepancy_message TEXT,
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('in_progress', 'completed', 'invalid')),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (skill_id) REFERENCES skills (id)
);

CREATE TABLE IF NOT EXISTS assessment_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option TEXT NOT NULL,
    is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
    FOREIGN KEY (attempt_id) REFERENCES assessment_attempts (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions (id)
);

CREATE TABLE IF NOT EXISTS user_skill_estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    quiz_proficiency INTEGER NOT NULL CHECK (quiz_proficiency >= 1 AND quiz_proficiency <= 5),
    self_assessed_level INTEGER CHECK (self_assessed_level IS NULL OR (self_assessed_level >= 1 AND self_assessed_level <= 5)),
    current_estimate REAL NOT NULL,
    last_attempt_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (skill_id) REFERENCES skills (id),
    FOREIGN KEY (last_attempt_id) REFERENCES assessment_attempts (id),
    UNIQUE (user_id, skill_id)
);

-- Milestone 4: Personalized Learning Roadmap
CREATE TABLE IF NOT EXISTS roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    career_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (career_id) REFERENCES careers (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS roadmap_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id INTEGER NOT NULL,
    skill_id INTEGER,
    stage TEXT NOT NULL CHECK (stage IN ('learn', 'practice', 'build', 'review')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    estimated_duration TEXT NOT NULL,
    recommended_order INTEGER NOT NULL,
    resource_title TEXT,
    resource_url TEXT,
    reason TEXT,
    is_project INTEGER DEFAULT 0 CHECK (is_project IN (0, 1)),
    is_completed INTEGER DEFAULT 0 CHECK (is_completed IN (0, 1)),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (roadmap_id) REFERENCES roadmaps (id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE SET NULL
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_careers_code ON careers(code);
CREATE INDEX IF NOT EXISTS idx_skills_code ON skills(code);
CREATE INDEX IF NOT EXISTS idx_career_skill_reqs_career ON career_skill_requirements(career_id);
CREATE INDEX IF NOT EXISTS idx_career_skill_reqs_skill ON career_skill_requirements(skill_id);
CREATE INDEX IF NOT EXISTS idx_career_selections_user ON career_selections(user_id);
CREATE INDEX IF NOT EXISTS idx_career_selections_active ON career_selections(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_questions_skill ON questions(skill_id);
CREATE INDEX IF NOT EXISTS idx_attempts_user_skill ON assessment_attempts(user_id, skill_id);
CREATE INDEX IF NOT EXISTS idx_estimates_user ON user_skill_estimates(user_id);
CREATE INDEX IF NOT EXISTS idx_roadmaps_user_career ON roadmaps(user_id, career_id);
CREATE INDEX IF NOT EXISTS idx_roadmaps_user_active ON roadmaps(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_roadmap ON roadmap_tasks(roadmap_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_stage ON roadmap_tasks(roadmap_id, stage);

