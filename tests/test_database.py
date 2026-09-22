"""
Tests for database storage, rankings, and natural language recommendations.
"""

from database.db import get_db, execute_query, fetch_one, fetch_all
from agents.scorer import ScorerAgent
from agents.ranking import RankingAgent
from agents.recommendation import RecommendationEngine


def test_database_and_pipeline(test_db):
    scorer = ScorerAgent()
    
    sample_wf = {
        "workflow_id": 999,
        "title": "Automated Telegram Bot with PostgreSQL",
        "slug": "automated-telegram-bot",
        "canonical_url": "https://n8n.io/workflows/999-automated-telegram-bot/",
        "creator_name": "Test Engineer",
        "creator_username": "tester",
        "creator_bio": "Automation specialist",
        "creator_verified": True,
        "description": "Connects Telegram bot to Postgres database for real-time queries.",
        "node_count": 4,
        "connection_count": 3,
        "complexity": "INTERMEDIATE",
        "complexity_score": 5.5,
        "complexity_reason": "4 nodes, database integration",
        "cost_class": "FREE",
        "paid_dependencies": [],
        "free_dependencies": ["Telegram", "PostgreSQL"],
        "cost_notes": "100% free stack",
        "security_score": 9.5,
        "security_risk_level": "LOW",
        "confidence_score": 90.0,
        "ai_score": None,
        "views": 500,
        "recent_views": 20,
        "price": 0.0,
        "content_hash": "hash999",
        "structure_hash": "struct999",
        "nodes": [
            {"node_name": "Telegram Trigger", "node_type": "n8n-nodes-base.telegramTrigger", "node_type_normalized": "telegram_trigger", "is_trigger": True, "is_ai": False, "is_custom": False, "node_category": "trigger", "credentials_needed": "telegram"},
            {"node_name": "Postgres Query", "node_type": "n8n-nodes-base.postgres", "node_type_normalized": "postgres", "is_trigger": False, "is_ai": False, "is_custom": False, "node_category": "database", "credentials_needed": "postgres"},
        ],
        "integrations": ["Telegram", "PostgreSQL"],
        "categories": ["Engineering", "Communication"],
    }
    
    # Persist workflow
    scorer.score_and_persist(sample_wf)
    
    # Query back
    stored = fetch_one("SELECT * FROM workflows WHERE workflow_id = 999")
    assert stored is not None
    assert stored["title"] == "Automated Telegram Bot with PostgreSQL"
    assert stored["overall_score"] > 0
    assert stored["rating_label"] in ["Exceptional", "Excellent", "Very Good", "Good"]

    # Test Rankings Agent
    ranker = RankingAgent()
    rankings = ranker.generate_all_rankings()
    assert len(rankings) > 0

    top_overall = ranker.get_ranking_list("top_overall")
    assert len(top_overall) >= 1
    assert top_overall[0]["workflow_id"] == 999

    # Test Recommendation Engine
    rec = RecommendationEngine()
    
    # Test natural language query
    recs = rec.recommend("Best free Telegram workflow with Postgres", limit=5)
    assert len(recs) >= 1
    assert recs[0]["workflow_id"] == 999
    assert "Telegram" in recs[0]["integrations"]
    assert recs[0]["cost"] == "FREE"
    assert len(recs[0]["strengths"]) > 0
    assert recs[0]["why_recommended"] != ""
