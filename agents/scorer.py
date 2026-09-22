"""
Scorer Agent: Computes deterministic 11-dimension scores, persists evidence, penalties, security findings, and database records.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from scoring.score import ScoringEngine
from scoring.value_gem import ValueAndGemScorer
from database.db import get_db, execute_query

logger = logging.getLogger(__name__)


class ScorerAgent:
    def __init__(self):
        self.scoring_engine = ScoringEngine()
        self.value_gem_scorer = ValueAndGemScorer()

    def score_and_persist(self, workflow_data: Dict[str, Any], conn: Optional[Any] = None) -> Dict[str, Any]:
        """Calculates all scores, penalties, value/gem metrics, and saves all tables atomically."""
        workflow_id = workflow_data["workflow_id"]
        logger.info(f"Scoring workflow {workflow_id}: {workflow_data.get('title')}")

        # 1. 12-dimension scoring
        scoring_res = self.scoring_engine.score_workflow(workflow_data)
        
        overall_score = scoring_res["overall_score"]
        base_score = scoring_res["base_score"]
        rating_label = scoring_res["rating_label"]
        daily_life_score = scoring_res["daily_life_practicality_score"]
        daily_life_label = scoring_res["daily_life_practicality_label"]
        daily_life_reason = scoring_res["daily_life_practicality_reason"]
        daily_life_freq = scoring_res["daily_life_use_frequency"]
        evidence_list = scoring_res["evidence_list"]
        penalties_list = scoring_res["penalties_list"]

        # 2. Value Score & Hidden Gem Score
        complexity_score = workflow_data.get("complexity_score", 5.0)
        cost_class = workflow_data.get("cost_class", "FREE")
        node_count = workflow_data.get("node_count", 0)
        views = workflow_data.get("views", 0)
        confidence_score = workflow_data.get("confidence_score", 0.0)

        value_score, value_reason = self.value_gem_scorer.calculate_value_score(
            overall_score=overall_score,
            complexity_score=complexity_score,
            cost_class=cost_class,
            node_count=node_count,
            views=views
        )

        hidden_gem_score = self.value_gem_scorer.calculate_hidden_gem_score(
            overall_score=overall_score,
            value_score=value_score,
            views=views,
            confidence_score=confidence_score
        )

        # Update workflow_data
        workflow_data["overall_score"] = overall_score
        workflow_data["base_score"] = base_score
        workflow_data["rating_label"] = rating_label
        workflow_data["daily_life_practicality_score"] = daily_life_score
        workflow_data["daily_life_practicality_label"] = daily_life_label
        workflow_data["daily_life_practicality_reason"] = daily_life_reason
        workflow_data["daily_life_use_frequency"] = daily_life_freq
        workflow_data["value_score"] = value_score
        workflow_data["value_reason"] = value_reason
        workflow_data["hidden_gem_score"] = hidden_gem_score
        workflow_data["evidence_list"] = evidence_list
        workflow_data["penalties_list"] = penalties_list

        def _do_persist(c):
            # 1. Upsert into workflows table
            c.execute(
                """
                INSERT INTO workflows (
                    workflow_id, title, slug, canonical_url,
                    creator_name, creator_username, creator_bio, creator_verified,
                    description, problem_it_solves, node_count, connection_count,
                    complexity, complexity_score, complexity_reason,
                    cost_class, paid_dependencies, free_dependencies, cost_notes,
                    overall_score, base_score, rating_label, confidence_score,
                    ai_score, security_score, security_risk_level,
                    value_score, value_reason, hidden_gem_score,
                    daily_life_practicality_score, daily_life_practicality_label,
                    daily_life_practicality_reason, daily_life_use_frequency,
                    views, recent_views, price,
                    content_hash, structure_hash,
                    first_seen, last_seen, last_checked, last_changed,
                    current_version, status,
                    created_at_source, updated_at_source,
                    raw_storage_path, normalized_storage_path
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    DATETIME('now'), DATETIME('now'), DATETIME('now'), DATETIME('now'),
                    1, 'active',
                    ?, ?,
                    ?, ?
                )
                ON CONFLICT(workflow_id) DO UPDATE SET
                    title = excluded.title,
                    slug = excluded.slug,
                    canonical_url = excluded.canonical_url,
                    creator_name = excluded.creator_name,
                    creator_username = excluded.creator_username,
                    creator_bio = excluded.creator_bio,
                    creator_verified = excluded.creator_verified,
                    description = excluded.description,
                    problem_it_solves = excluded.problem_it_solves,
                    node_count = excluded.node_count,
                    connection_count = excluded.connection_count,
                    complexity = excluded.complexity,
                    complexity_score = excluded.complexity_score,
                    complexity_reason = excluded.complexity_reason,
                    cost_class = excluded.cost_class,
                    paid_dependencies = excluded.paid_dependencies,
                    free_dependencies = excluded.free_dependencies,
                    cost_notes = excluded.cost_notes,
                    overall_score = excluded.overall_score,
                    base_score = excluded.base_score,
                    rating_label = excluded.rating_label,
                    confidence_score = excluded.confidence_score,
                    ai_score = excluded.ai_score,
                    security_score = excluded.security_score,
                    security_risk_level = excluded.security_risk_level,
                    value_score = excluded.value_score,
                    value_reason = excluded.value_reason,
                    hidden_gem_score = excluded.hidden_gem_score,
                    daily_life_practicality_score = excluded.daily_life_practicality_score,
                    daily_life_practicality_label = excluded.daily_life_practicality_label,
                    daily_life_practicality_reason = excluded.daily_life_practicality_reason,
                    daily_life_use_frequency = excluded.daily_life_use_frequency,
                    views = excluded.views,
                    recent_views = excluded.recent_views,
                    price = excluded.price,
                    content_hash = excluded.content_hash,
                    structure_hash = excluded.structure_hash,
                    last_seen = DATETIME('now'),
                    last_checked = DATETIME('now'),
                    normalized_storage_path = excluded.normalized_storage_path
                """,
                (
                    workflow_id,
                    workflow_data["title"],
                    workflow_data.get("slug"),
                    workflow_data["canonical_url"],
                    workflow_data.get("creator_name"),
                    workflow_data.get("creator_username"),
                    workflow_data.get("creator_bio"),
                    1 if workflow_data.get("creator_verified") else 0,
                    workflow_data.get("description"),
                    workflow_data.get("problem_it_solves"),
                    workflow_data.get("node_count", 0),
                    workflow_data.get("connection_count", 0),
                    workflow_data.get("complexity", "INTERMEDIATE"),
                    workflow_data.get("complexity_score", 5.0),
                    workflow_data.get("complexity_reason"),
                    workflow_data.get("cost_class", "FREE"),
                    json.dumps(workflow_data.get("paid_dependencies", [])),
                    json.dumps(workflow_data.get("free_dependencies", [])),
                    workflow_data.get("cost_notes"),
                    overall_score,
                    base_score,
                    rating_label,
                    confidence_score,
                    workflow_data.get("ai_score"),
                    workflow_data.get("security_score", 10.0),
                    workflow_data.get("security_risk_level", "LOW"),
                    value_score,
                    value_reason,
                    hidden_gem_score,
                    daily_life_score,
                    daily_life_label,
                    daily_life_reason,
                    daily_life_freq,
                    workflow_data.get("views", 0),
                    workflow_data.get("recent_views", 0),
                    workflow_data.get("price", 0.0),
                    workflow_data.get("content_hash"),
                    workflow_data.get("structure_hash"),
                    workflow_data.get("created_at_source"),
                    workflow_data.get("updated_at_source"),
                    workflow_data.get("raw_storage_path"),
                    workflow_data.get("normalized_storage_path"),
                )
            )

            # 2. Persist Nodes
            c.execute("DELETE FROM workflow_nodes WHERE workflow_id = ?", (workflow_id,))
            for node in workflow_data.get("nodes", []):
                c.execute(
                    """
                    INSERT INTO workflow_nodes (
                        workflow_id, node_name, node_type, node_type_normalized,
                        node_category, is_trigger, is_ai, is_custom, credentials_needed
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workflow_id,
                        node.get("node_name", "Node"),
                        node.get("node_type", "unknown"),
                        node.get("node_type_normalized", "unknown"),
                        node.get("node_category", "general"),
                        1 if node.get("is_trigger") else 0,
                        1 if node.get("is_ai") else 0,
                        1 if node.get("is_custom") else 0,
                        node.get("credentials_needed"),
                    )
                )

            # 3. Persist Integrations
            c.execute("DELETE FROM workflow_integrations WHERE workflow_id = ?", (workflow_id,))
            for integ in workflow_data.get("integrations", []):
                c.execute(
                    """
                    INSERT OR IGNORE INTO workflow_integrations (
                        workflow_id, integration_name, integration_normalized, is_paid
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        workflow_id,
                        integ,
                        integ.lower(),
                        1 if integ in workflow_data.get("paid_dependencies", []) else 0,
                    )
                )

            # 4. Persist Categories
            c.execute("DELETE FROM workflow_categories WHERE workflow_id = ?", (workflow_id,))
            for i, cat in enumerate(workflow_data.get("categories", [])):
                c.execute(
                    """
                    INSERT OR IGNORE INTO workflow_categories (
                        workflow_id, category_name, category_normalized, is_primary
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        workflow_id,
                        cat,
                        cat.lower(),
                        1 if i == 0 else 0,
                    )
                )

            # 5. Persist Score Evidence
            c.execute("DELETE FROM score_evidence WHERE workflow_id = ?", (workflow_id,))
            for ev in evidence_list:
                c.execute(
                    """
                    INSERT INTO score_evidence (
                        workflow_id, criterion, raw_score, weight, weighted_score,
                        evidence, reasoning, confidence, evidence_type
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workflow_id,
                        ev["criterion"],
                        ev["raw_score"],
                        ev["weight"],
                        ev["weighted_score"],
                        ev["evidence"],
                        ev["reasoning"],
                        ev["confidence"],
                        ev["evidence_type"],
                    )
                )

            # 6. Persist Penalties
            c.execute("DELETE FROM penalties WHERE workflow_id = ?", (workflow_id,))
            for p in penalties_list:
                c.execute(
                    """
                    INSERT INTO penalties (workflow_id, penalty_type, penalty_amount, evidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (workflow_id, p["penalty_type"], p["penalty_amount"], p["evidence"])
                )

            # 7. Persist Security Findings
            c.execute("DELETE FROM security_findings WHERE workflow_id = ?", (workflow_id,))
            for f in workflow_data.get("security_findings", []):
                c.execute(
                    """
                    INSERT INTO security_findings (workflow_id, finding_type, risk_level, description, evidence, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (workflow_id, f["finding_type"], f["risk_level"], f["description"], f.get("evidence"), f.get("recommendation"))
                )

        if conn is not None:
            _do_persist(conn)
        else:
            with get_db() as c:
                _do_persist(c)

        logger.info(f"Successfully persisted workflow {workflow_id} with score {overall_score:.2f} ({rating_label})")
        return workflow_data
