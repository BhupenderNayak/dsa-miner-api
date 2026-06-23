CREATE TABLE IF NOT EXISTS companies (
    company_id BIGSERIAL PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS problems (
    problem_id BIGSERIAL PRIMARY KEY,
    leetcode_id INTEGER,
    title TEXT NOT NULL,
    slug TEXT,
    difficulty TEXT CHECK (difficulty IN ('Easy', 'Medium', 'Hard') OR difficulty IS NULL),
    acceptance_rate NUMERIC(6, 4),
    url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (title)
);

CREATE TABLE IF NOT EXISTS patterns (
    pattern_id BIGSERIAL PRIMARY KEY,
    pattern_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS problem_patterns (
    problem_id BIGINT NOT NULL REFERENCES problems(problem_id) ON DELETE CASCADE,
    pattern_id BIGINT NOT NULL REFERENCES patterns(pattern_id) ON DELETE CASCADE,
    PRIMARY KEY (problem_id, pattern_id)
);

CREATE TABLE IF NOT EXISTS company_problem_frequencies (
    company_id BIGINT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    problem_id BIGINT NOT NULL REFERENCES problems(problem_id) ON DELETE CASCADE,
    timeframe TEXT NOT NULL DEFAULT 'all_time',
    frequency_count NUMERIC(10, 2) NOT NULL DEFAULT 0,
    source_file TEXT,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (company_id, problem_id, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_company_problem_frequencies_company
    ON company_problem_frequencies(company_id);

CREATE INDEX IF NOT EXISTS idx_company_problem_frequencies_problem
    ON company_problem_frequencies(problem_id);

CREATE INDEX IF NOT EXISTS idx_problem_patterns_pattern
    ON problem_patterns(pattern_id);

CREATE OR REPLACE VIEW company_problem_pattern_view AS
SELECT
    c.company_name,
    p.title AS problem_title,
    p.leetcode_id,
    p.difficulty,
    p.acceptance_rate,
    p.url,
    pat.pattern_name,
    cpf.timeframe,
    cpf.frequency_count,
    cpf.source_file
FROM company_problem_frequencies cpf
JOIN companies c ON c.company_id = cpf.company_id
JOIN problems p ON p.problem_id = cpf.problem_id
LEFT JOIN problem_patterns pp ON pp.problem_id = p.problem_id
LEFT JOIN patterns pat ON pat.pattern_id = pp.pattern_id;
