"""
Internal FastAPI REST API for n8n Workflow Intelligence & Ranking System.
"""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = str(Path(__file__).parent.parent.resolve())
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from database.db import fetch_all, fetch_one
from agents.recommendation import RecommendationEngine
from agents.ranking import RankingAgent

app = FastAPI(
    title="n8n Workflow Intelligence API",
    description="Autonomous intelligence, ranking, daily-life practicality scoring, and recommendation API for n8n workflow templates",
    version="1.0.0"
)

rec_engine = RecommendationEngine()
ranking_agent = RankingAgent()


@app.get("/stats")
def get_stats() -> Dict[str, Any]:
    """Summary overview of indexed workflows and platform metrics."""
    total_wf = fetch_one("SELECT COUNT(*) as count FROM workflows")["count"]
    total_disc = fetch_one("SELECT COUNT(*) as count FROM discovery_records")["count"]
    avg_score = fetch_one("SELECT AVG(overall_score) as avg_score FROM workflows")["avg_score"] or 0.0
    avg_daily_life = fetch_one("SELECT AVG(daily_life_practicality_score) as avg_score FROM workflows")["avg_score"] or 0.0
    
    complexity_counts = fetch_all("SELECT complexity, COUNT(*) as count FROM workflows GROUP BY complexity")
    cost_counts = fetch_all("SELECT cost_class, COUNT(*) as count FROM workflows GROUP BY cost_class")
    rating_counts = fetch_all("SELECT rating_label, COUNT(*) as count FROM workflows GROUP BY rating_label")
    daily_life_counts = fetch_all("SELECT daily_life_practicality_label, COUNT(*) as count FROM workflows GROUP BY daily_life_practicality_label")

    return {
        "total_discovered": total_disc,
        "total_analyzed": total_wf,
        "average_overall_score": round(avg_score, 2),
        "average_daily_life_score": round(avg_daily_life, 2),
        "complexity_distribution": {r["complexity"]: r["count"] for r in complexity_counts},
        "cost_distribution": {r["cost_class"]: r["count"] for r in cost_counts},
        "rating_distribution": {r["rating_label"]: r["count"] for r in rating_counts},
        "daily_life_distribution": {r["daily_life_practicality_label"]: r["count"] for r in daily_life_counts if r["daily_life_practicality_label"]},
    }


@app.get("/workflows")
def list_workflows(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    min_score: Optional[float] = None,
    min_daily_life: Optional[float] = None,
    complexity: Optional[str] = None,
    cost_class: Optional[str] = None,
    category: Optional[str] = None,
    integration: Optional[str] = None
) -> Dict[str, Any]:
    """List indexed workflows with multi-criteria filtering and pagination."""
    offset = (page - 1) * limit
    sql = "SELECT * FROM workflows WHERE status = 'active'"
    params = []

    if min_score is not None:
        sql += " AND overall_score >= ?"
        params.append(min_score)
    if min_daily_life is not None:
        sql += " AND daily_life_practicality_score >= ?"
        params.append(min_daily_life)
    if complexity:
        sql += " AND complexity = ?"
        params.append(complexity.upper())
    if cost_class:
        sql += " AND cost_class = ?"
        params.append(cost_class.upper())
    if category:
        sql += " AND workflow_id IN (SELECT workflow_id FROM workflow_categories WHERE category_normalized LIKE ?)"
        params.append(f"%{category.lower()}%")
    if integration:
        sql += " AND workflow_id IN (SELECT workflow_id FROM workflow_integrations WHERE integration_normalized LIKE ?)"
        params.append(f"%{integration.lower()}%")

    count_sql = f"SELECT COUNT(*) as total FROM ({sql})"
    total = fetch_one(count_sql, tuple(params))["total"]

    sql += " ORDER BY overall_score DESC, confidence_score DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    items = fetch_all(sql, tuple(params))

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "workflows": items
    }


@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: int) -> Dict[str, Any]:
    """Get complete workflow details, nodes, integrations, evidence breakdown, and security findings."""
    wf = fetch_one("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    nodes = fetch_all("SELECT * FROM workflow_nodes WHERE workflow_id = ?", (workflow_id,))
    integrations = fetch_all("SELECT * FROM workflow_integrations WHERE workflow_id = ?", (workflow_id,))
    categories = fetch_all("SELECT * FROM workflow_categories WHERE workflow_id = ?", (workflow_id,))
    evidence = fetch_all("SELECT * FROM score_evidence WHERE workflow_id = ?", (workflow_id,))
    penalties = fetch_all("SELECT * FROM penalties WHERE workflow_id = ?", (workflow_id,))
    security_findings = fetch_all("SELECT * FROM security_findings WHERE workflow_id = ?", (workflow_id,))
    versions = fetch_all("SELECT * FROM workflow_versions WHERE workflow_id = ? ORDER BY version_number DESC", (workflow_id,))
    duplicates = fetch_all("SELECT * FROM duplicates WHERE workflow_id = ? OR duplicate_of_id = ?", (workflow_id, workflow_id))

    wf_dict = dict(wf)
    wf_dict["nodes"] = nodes
    wf_dict["integrations"] = integrations
    wf_dict["categories"] = categories
    wf_dict["score_evidence"] = evidence
    wf_dict["penalties"] = penalties
    wf_dict["security_findings"] = security_findings
    wf_dict["versions"] = versions
    wf_dict["duplicates"] = duplicates

    return wf_dict


@app.get("/rankings")
def list_rankings() -> List[str]:
    """List all available leaderboard categories."""
    rows = fetch_all("SELECT DISTINCT ranking_list FROM rankings ORDER BY ranking_list ASC")
    return [r["ranking_list"] for r in rows]


@app.get("/rankings/daily-life")
def get_daily_life_rankings(limit: int = 20) -> List[Dict[str, Any]]:
    """Get top rankings specifically for Daily-Life Practicality."""
    return ranking_agent.get_ranking_list("top_daily_life", limit=limit)


@app.get("/rankings/{list_name}")
def get_ranking_leaderboard(list_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get leaderboard rankings for a specific list."""
    return ranking_agent.get_ranking_list(list_name, limit=limit)


@app.get("/categories")
def list_categories() -> List[Dict[str, Any]]:
    """List all workflow categories with template counts."""
    return fetch_all(
        """
        SELECT category_name, category_normalized, COUNT(DISTINCT workflow_id) as workflow_count
        FROM workflow_categories
        GROUP BY category_normalized
        ORDER BY workflow_count DESC
        """
    )


@app.get("/integrations")
def list_integrations() -> List[Dict[str, Any]]:
    """List all connected integrations with template counts."""
    return fetch_all(
        """
        SELECT integration_name, integration_normalized, COUNT(DISTINCT workflow_id) as workflow_count
        FROM workflow_integrations
        GROUP BY integration_normalized
        ORDER BY workflow_count DESC
        """
    )


@app.get("/search")
def search_workflows(q: str = Query(..., description="Keywords to search in title, description, and problem statement"), limit: int = 20) -> List[Dict[str, Any]]:
    """Search workflows across title, description, and problem statement."""
    return fetch_all(
        """
        SELECT workflow_id, title, problem_it_solves, canonical_url, overall_score,
               daily_life_practicality_score, daily_life_use_frequency, complexity, cost_class
        FROM workflows
        WHERE status = 'active' AND (title LIKE ? OR description LIKE ? OR problem_it_solves LIKE ?)
        ORDER BY overall_score DESC
        LIMIT ?
        """,
        (f"%{q}%", f"%{q}%", f"%{q}%", limit)
    )


@app.get("/recommend")
def recommend_workflows(q: str = Query(..., description="Natural language query, e.g. 'Best free Telegram AI agent'"), limit: int = 5) -> List[Dict[str, Any]]:
    """Evidence-based natural language recommendation engine."""
    return rec_engine.recommend(q, limit=limit)


@app.get("/duplicates")
def get_duplicates() -> List[Dict[str, Any]]:
    """List all detected duplicate and variant pairs."""
    return fetch_all("SELECT * FROM duplicates ORDER BY similarity_score DESC")
