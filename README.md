# n8n Workflow Intelligence & Ranking System

An autonomous, evidence-based intelligence and ranking system for n8n workflow templates. It discovers, crawls, analyzes, scores, categorizes, deduplicates, stores, ranks, and continuously monitors workflow templates published on [n8n.io/workflows](https://n8n.io/workflows/).

---

## 🚀 Key Capabilities

- **Automated Discovery**: Discovers workflow templates via official sitemaps (`https://n8n.io/sitemap-workflows.xml`) and search APIs.
- **Polite & Resilient Crawler**: Token bucket rate limiting, disk caching, retry backoff, and raw JSON archiving.
- **Deep Graph Extraction**: Parses nodes, trigger types, connections, code blocks, AI components, credentials, and databases.
- **Multi-Dimensional Classification**:
  - **Complexity**: `BEGINNER`, `INTERMEDIATE`, `ADVANCED`, `EXPERT`
  - **Cost Footprint**: `FREE`, `MOSTLY_FREE`, `LOW_COST`, `PAID`, `EXPENSIVE`
  - **Security Audit**: Static vulnerability detection (hardcoded secrets, dynamic `eval`, unprotected webhooks)
- **11-Dimension Deterministic Scoring**:
  - Practical usefulness (18%)
  - Automation/time-saving value (15%)
  - Workflow design quality (12%)
  - Reliability/robustness (10%)
  - Ease of setup (10%)
  - Reusability/customization (9%)
  - Documentation quality (6%)
  - Integration quality (5%)
  - Security (5%)
  - Maintenance/current relevance (5%)
  - Cost efficiency (5%)
- **Multi-Layer Duplicate Detection**: Exact hash, structural fingerprinting, and semantic Jaccard similarity.
- **Curated Leaderboards**: 18+ auto-generated ranking categories (Top AI Agents, Top Free, Best Quick Wins, Hidden Gems, etc.).
- **Natural Language Recommendation Engine**: Answers automation questions backed by database evidence.
- **Interactive Streamlit Dashboard**: Full GUI for browsing, filtering, auditing, and ranking workflows.

---

## 📂 Project Structure

```
n8n-workflow-ranker/
│
├── agents/                      # Autonomous Agents Pipeline
│   ├── supervisor.py            # End-to-end pipeline orchestrator
│   ├── discovery.py             # Discovers templates from sitemaps & search
│   ├── crawler.py               # Polite batch crawler
│   ├── extractor.py             # Normalization and database extraction
│   ├── analyst.py               # Complexity, cost, and usefulness analysis
│   ├── security.py              # Security review and finding generation
│   ├── scorer.py                # 11-dimension scoring and persistence
│   ├── deduplicator.py          # Multi-layer duplicate detection
│   ├── ranking.py               # Generates and caches leaderboards
│   ├── updater.py               # Incremental monitoring and versioning
│   └── recommendation.py       # Natural language query engine
│
├── crawler/                     # Low-Level Crawling Infrastructure
│   ├── client.py                # HTTP client with retry, backoff, disk cache
│   ├── discovery_sources.py     # Sitemap XML and Search API parser
│   ├── workflow_page.py         # Full workflow JSON fetcher
│   └── rate_limiter.py          # Token bucket rate limiter
│
├── extraction/                  # Extraction & Normalization
│   ├── metadata.py              # Top-level template metadata
│   ├── workflow_json.py         # Node graph, connections, credentials
│   └── normalization.py         # Type aliases and fingerprint hashes
│
├── analysis/                    # Specialized Analyzers
│   ├── complexity.py            # Complexity classification (Beginner to Expert)
│   ├── cost.py                  # Paid vs Free dependencies & cost notes
│   ├── security.py              # Embedded secrets & vulnerability scanner
│   └── usefulness.py            # Business domain & time saved
│
├── scoring/                     # Scoring Rubric & Metrics
│   ├── rubric.yaml              # Weights and rating label bounds
│   ├── penalties.yaml           # Penalty rules and deductions
│   ├── score.py                 # 11-criterion deterministic score engine
│   ├── confidence.py            # 0-100% evidence completeness score
│   ├── ai_capability.py         # 0-10 AI agent capability score
│   └── value_gem.py             # Value Score and Hidden Gem Score
│
├── database/                    # SQLite Storage & Models
│   ├── schema.sql               # PostgreSQL-compatible SQL schema
│   ├── db.py                    # Connection manager, transactions, WAL mode
│   └── models.py                # Pydantic data models
│
├── embeddings/                  # Similarity & Deduplication
│   └── similarity.py            # Multi-layer duplicate detection
│
├── ai/                          # AI Provider Layer
│   └── provider.py              # OpenAI-compatible API abstraction
│
├── dashboard/                   # Streamlit GUI
│   └── app.py                   # Interactive web dashboard
│
├── api/                         # FastAPI Internal API
│   └── app.py                   # REST endpoints
│
├── tests/                       # Pytest Test Suite
│   ├── conftest.py              # Shared fixtures and mock workflows
│   ├── test_discovery.py
│   ├── test_extraction.py
│   ├── test_analysis.py
│   ├── test_scoring.py
│   └── test_database.py
│
├── data/                        # Local Storage
│   ├── raw/                     # Raw JSON payloads
│   ├── normalized/              # Clean normalized workflow JSON
│   ├── cache/                   # HTTP response disk cache
│   └── n8n_workflows.db         # SQLite database
│
├── config.yaml                  # System configuration
├── .env                         # Environment settings
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🛠️ Installation & Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure Environment** (Optional):
The default configuration is ready out of the box in `.env`.
To configure an OpenAI-compatible local LLM endpoint:
```env
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://127.0.0.1:20128/v1
ENABLE_AI_SCORING=false
```

---

## 💻 Running the System

### 1. Run Complete Pipeline (MVP 20 Workflows)
```bash
python -m agents.supervisor --limit 20
```

### 2. Launch Interactive Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

### 3. Run Incremental Update Cycle
```bash
python -m agents.updater
```

### 4. Run Pytest Suite
```bash
python -m pytest -v
```

### 5. Launch FastAPI Backend
```bash
uvicorn api.app:app --reload --port 8000
```

---

## 📊 Database Schema Summary

The SQLite database is stored at `data/n8n_workflows.db` with 13 relational tables:
1. `discovery_records`: Discovery URLs, sources, and crawl status.
2. `workflows`: Main catalog table with scores, complexity, cost class, security, hashes, and views.
3. `workflow_nodes`: Extracted nodes, types, triggers, AI flags, and credentials.
4. `workflow_integrations`: Connected apps and services.
5. `workflow_categories`: Taxonomy categories.
6. `score_evidence`: Breakdown across all 11 criteria with exact evidence and confidence.
7. `penalties`: Deductions applied with cited evidence.
8. `security_findings`: Static audit findings with severity and recommendations.
9. `duplicates`: Multi-layer duplicate and variant links.
10. `rankings`: Cached category leaderboards.
11. `workflow_versions`: Historical snapshots for change detection.
12. `crawl_runs`: Crawl session execution logs.
13. `crawl_errors`: Failed URL error queue.
