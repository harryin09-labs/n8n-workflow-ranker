-- SQLite Schema for n8n Workflow Intelligence & Ranking System
-- Designed for PostgreSQL compatibility (standard SQL data types and conventions)

PRAGMA foreign_keys = ON;

-- 1. Discovery records tracking URLs and discovery pipeline status
CREATE TABLE IF NOT EXISTS discovery_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER UNIQUE NOT NULL,
    canonical_url TEXT NOT NULL,
    slug TEXT,
    discovery_source TEXT NOT NULL DEFAULT 'sitemap', -- 'sitemap', 'search_api', 'catalog', 'manual'
    first_seen TEXT NOT NULL DEFAULT (DATETIME('now')),
    last_seen TEXT NOT NULL DEFAULT (DATETIME('now')),
    crawl_status TEXT NOT NULL DEFAULT 'pending' -- 'pending', 'crawled', 'failed', 'skipped'
);
CREATE INDEX IF NOT EXISTS idx_discovery_status ON discovery_records(crawl_status);
CREATE INDEX IF NOT EXISTS idx_discovery_source ON discovery_records(discovery_source);

-- 2. Crawl Runs metadata
CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    start_time TEXT NOT NULL DEFAULT (DATETIME('now')),
    end_time TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    workflows_discovered INTEGER NOT NULL DEFAULT 0,
    workflows_crawled INTEGER NOT NULL DEFAULT 0,
    workflows_failed INTEGER NOT NULL DEFAULT 0,
    summary TEXT
);

-- 3. Crawl Errors log
CREATE TABLE IF NOT EXISTS crawl_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    workflow_id INTEGER,
    url TEXT,
    error_type TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES discovery_records(workflow_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_crawl_errors_wf ON crawl_errors(workflow_id);

-- 4. Main Workflows catalog
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    slug TEXT,
    canonical_url TEXT NOT NULL,
    creator_name TEXT,
    creator_username TEXT,
    creator_bio TEXT,
    creator_verified INTEGER DEFAULT 0,
    description TEXT,
    problem_it_solves TEXT, -- One concise line: what real-world problem this workflow solves
    node_count INTEGER NOT NULL DEFAULT 0,
    connection_count INTEGER NOT NULL DEFAULT 0,
    -- Classification & Taxonomy
    complexity TEXT NOT NULL DEFAULT 'INTERMEDIATE', -- 'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'
    complexity_score REAL NOT NULL DEFAULT 5.0,
    complexity_reason TEXT,
    cost_class TEXT NOT NULL DEFAULT 'FREE', -- 'FREE', 'MOSTLY_FREE', 'LOW_COST', 'PAID', 'EXPENSIVE', 'UNKNOWN'
    paid_dependencies TEXT, -- JSON array of paid services
    free_dependencies TEXT, -- JSON array of free services
    cost_notes TEXT,
    -- Scoring
    overall_score REAL NOT NULL DEFAULT 0.0,
    base_score REAL NOT NULL DEFAULT 0.0,
    rating_label TEXT NOT NULL DEFAULT 'Average', -- 'Exceptional', 'Excellent', 'Very Good', 'Good', 'Average', 'Below Average', 'Poor'
    confidence_score REAL NOT NULL DEFAULT 0.0, -- 0 to 100%
    ai_score REAL, -- NULL for non-AI, 0-10 for AI workflows
    security_score REAL NOT NULL DEFAULT 10.0,
    security_risk_level TEXT NOT NULL DEFAULT 'LOW', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    value_score REAL NOT NULL DEFAULT 0.0,
    value_reason TEXT,
    hidden_gem_score REAL NOT NULL DEFAULT 0.0,
    -- Daily-Life Practicality (15% weight in overall score)
    daily_life_practicality_score REAL NOT NULL DEFAULT 0.0, -- 0-10
    daily_life_practicality_label TEXT, -- 'Extremely Practical', 'Highly Practical', etc.
    daily_life_practicality_reason TEXT,
    daily_life_use_frequency TEXT, -- 'Daily', 'Weekly', 'Monthly', 'Rarely', 'Almost Never'
    -- Metadata & Stats from n8n
    views INTEGER NOT NULL DEFAULT 0,
    recent_views INTEGER NOT NULL DEFAULT 0,
    price REAL NOT NULL DEFAULT 0.0,
    -- Fingerprints & Versioning
    content_hash TEXT,
    structure_hash TEXT,
    first_seen TEXT NOT NULL DEFAULT (DATETIME('now')),
    last_seen TEXT NOT NULL DEFAULT (DATETIME('now')),
    last_checked TEXT NOT NULL DEFAULT (DATETIME('now')),
    last_changed TEXT NOT NULL DEFAULT (DATETIME('now')),
    current_version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'possibly_removed', 'removed'
    created_at_source TEXT,
    updated_at_source TEXT,
    raw_storage_path TEXT,
    normalized_storage_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_workflows_score ON workflows(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_complexity ON workflows(complexity);
CREATE INDEX IF NOT EXISTS idx_workflows_cost ON workflows(cost_class);
CREATE INDEX IF NOT EXISTS idx_workflows_ai_score ON workflows(ai_score);
CREATE INDEX IF NOT EXISTS idx_workflows_hidden_gem ON workflows(hidden_gem_score DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_hashes ON workflows(content_hash, structure_hash);

-- 5. Workflow Versions for change detection
CREATE TABLE IF NOT EXISTS workflow_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    title TEXT,
    description TEXT,
    node_count INTEGER,
    content_hash TEXT,
    structure_hash TEXT,
    overall_score REAL,
    raw_storage_path TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    change_summary TEXT,
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(workflow_id, version_number)
);
CREATE INDEX IF NOT EXISTS idx_versions_wf ON workflow_versions(workflow_id);

-- 6. Workflow Nodes
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    node_name TEXT NOT NULL,
    node_type TEXT NOT NULL,
    node_type_normalized TEXT NOT NULL,
    node_category TEXT, -- 'trigger', 'action', 'ai', 'logic', 'data_transform', 'code', 'custom'
    is_trigger INTEGER DEFAULT 0,
    is_ai INTEGER DEFAULT 0,
    is_custom INTEGER DEFAULT 0,
    credentials_needed TEXT,
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_nodes_wf ON workflow_nodes(workflow_id);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON workflow_nodes(node_type_normalized);

-- 7. Workflow Integrations
CREATE TABLE IF NOT EXISTS workflow_integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    integration_name TEXT NOT NULL,
    integration_normalized TEXT NOT NULL,
    is_paid INTEGER DEFAULT 0,
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(workflow_id, integration_normalized)
);
CREATE INDEX IF NOT EXISTS idx_integrations_wf ON workflow_integrations(workflow_id);
CREATE INDEX IF NOT EXISTS idx_integrations_name ON workflow_integrations(integration_normalized);

-- 8. Workflow Categories
CREATE TABLE IF NOT EXISTS workflow_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    category_id INTEGER,
    category_name TEXT NOT NULL,
    category_normalized TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(workflow_id, category_normalized)
);
CREATE INDEX IF NOT EXISTS idx_categories_wf ON workflow_categories(workflow_id);
CREATE INDEX IF NOT EXISTS idx_categories_name ON workflow_categories(category_normalized);

-- 9. Detailed Evidence-Based Scores
CREATE TABLE IF NOT EXISTS score_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    criterion TEXT NOT NULL,
    raw_score REAL NOT NULL,
    weight REAL NOT NULL,
    weighted_score REAL NOT NULL,
    evidence TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 100.0,
    evidence_type TEXT NOT NULL DEFAULT 'OBSERVED', -- 'OBSERVED', 'DERIVED', 'INFERRED', 'UNKNOWN'
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(workflow_id, criterion)
);
CREATE INDEX IF NOT EXISTS idx_score_evidence_wf ON score_evidence(workflow_id);

-- 10. Penalties Applied
CREATE TABLE IF NOT EXISTS penalties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    penalty_type TEXT NOT NULL,
    penalty_amount REAL NOT NULL,
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_penalties_wf ON penalties(workflow_id);

-- 11. Security Findings
CREATE TABLE IF NOT EXISTS security_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    finding_type TEXT NOT NULL,
    risk_level TEXT NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    description TEXT NOT NULL,
    evidence TEXT,
    recommendation TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_security_wf ON security_findings(workflow_id);

-- 12. Duplicates tracking
CREATE TABLE IF NOT EXISTS duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    duplicate_of_id INTEGER NOT NULL,
    duplicate_type TEXT NOT NULL, -- 'EXACT_DUPLICATE', 'NEAR_DUPLICATE', 'VARIANT', 'UNIQUE'
    similarity_score REAL NOT NULL,
    similarity_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    FOREIGN KEY(duplicate_of_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(workflow_id, duplicate_of_id)
);
CREATE INDEX IF NOT EXISTS idx_duplicates_wf ON duplicates(workflow_id);

-- 13. Curated and Dynamic Rankings
CREATE TABLE IF NOT EXISTS rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ranking_list TEXT NOT NULL,
    workflow_id INTEGER NOT NULL,
    rank_position INTEGER NOT NULL,
    score_value REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(ranking_list, rank_position)
);
CREATE INDEX IF NOT EXISTS idx_rankings_list ON rankings(ranking_list, rank_position);

-- 13. Curated and Dynamic Rankings (continued)
CREATE TABLE IF NOT EXISTS workflow_duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    duplicate_of_id INTEGER NOT NULL,
    duplicate_type TEXT NOT NULL, -- 'EXACT_DUPLICATE', 'NEAR_DUPLICATE', 'VARIANT', 'UNIQUE'
    similarity_score REAL NOT NULL,
    similarity_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    FOREIGN KEY(duplicate_of_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    UNIQUE(workflow_id, duplicate_of_id)
);
CREATE INDEX IF NOT EXISTS idx_workflow_duplicates_wf ON workflow_duplicates(workflow_id);