"""
Ranking Agent: Dynamically calculates and caches curated category and metric leaderboards in the database.
"""

import logging
from typing import Dict, Any, List
from database.db import get_db, fetch_all

logger = logging.getLogger(__name__)

RANKING_DEFINITIONS = [
    # Top Overall
    ("top_overall", "SELECT workflow_id, overall_score FROM workflows WHERE status = 'active' ORDER BY overall_score DESC, confidence_score DESC LIMIT 20"),
    
    # Top Daily-Life Automations & Practicality
    ("top_daily_life", "SELECT workflow_id, daily_life_practicality_score as score FROM workflows WHERE status = 'active' ORDER BY daily_life_practicality_score DESC, overall_score DESC LIMIT 20"),
    ("most_practical", "SELECT workflow_id, round((daily_life_practicality_score * 0.6 + overall_score * 0.4), 2) as score FROM workflows WHERE status = 'active' ORDER BY score DESC, daily_life_practicality_score DESC LIMIT 20"),
    ("top_personal_productivity", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_categories c ON w.workflow_id = c.workflow_id WHERE c.category_normalized LIKE '%productivity%' OR w.description LIKE '%productivity%' OR w.title LIKE '%task%' OR w.title LIKE '%todo%' ORDER BY w.daily_life_practicality_score DESC, w.overall_score DESC LIMIT 20"),
    
    # Top AI & RAG
    ("top_ai_agents", "SELECT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_nodes n ON w.workflow_id = n.workflow_id WHERE (n.is_ai = 1 OR w.ai_score IS NOT NULL) GROUP BY w.workflow_id ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_rag", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_nodes n ON w.workflow_id = n.workflow_id WHERE (n.node_type LIKE '%vectordb%' OR n.node_type LIKE '%pinecone%' OR n.node_type LIKE '%qdrant%' OR n.node_type LIKE '%rag%' OR w.description LIKE '%rag%') ORDER BY w.overall_score DESC LIMIT 20"),
    
    # Business Functional Categories
    ("top_business_automation", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_categories c ON w.workflow_id = c.workflow_id WHERE c.category_normalized IN ('business', 'operations', 'productivity', 'finance') OR w.description LIKE '%business%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_sales", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_categories c ON w.workflow_id = c.workflow_id WHERE c.category_normalized LIKE '%sales%' OR w.description LIKE '%sales%' OR w.description LIKE '%crm%' OR w.description LIKE '%lead%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_marketing", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_categories c ON w.workflow_id = c.workflow_id WHERE c.category_normalized LIKE '%marketing%' OR w.description LIKE '%social%' OR w.description LIKE '%campaign%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_customer_support", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_categories c ON w.workflow_id = c.workflow_id WHERE c.category_normalized LIKE '%support%' OR c.category_normalized LIKE '%customer%' OR w.description LIKE '%ticket%' OR w.description LIKE '%support%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_document_automation", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%pdf%' OR i.integration_normalized LIKE '%drive%' OR i.integration_normalized LIKE '%dropbox%' OR w.description LIKE '%document%' OR w.description LIKE '%invoice%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_appointment_booking", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%calendar%' OR i.integration_normalized LIKE '%calendly%' OR w.description LIKE '%schedule%' OR w.description LIKE '%booking%' OR w.description LIKE '%appointment%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_developer_workflows", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_categories c ON w.workflow_id = c.workflow_id WHERE c.category_normalized LIKE '%engineering%' OR c.category_normalized LIKE '%developer%' OR w.description LIKE '%github%' OR w.description LIKE '%gitlab%' ORDER BY w.overall_score DESC LIMIT 20"),

    # Top Integrations
    ("top_gmail", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%gmail%' OR i.integration_normalized LIKE '%email%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_google_sheets", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%googlesheets%' OR i.integration_normalized LIKE '%google sheets%' OR i.integration_normalized LIKE '%spreadsheet%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_google_drive", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%googledrive%' OR i.integration_normalized LIKE '%drive%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_telegram", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%telegram%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_slack", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%slack%' ORDER BY w.overall_score DESC LIMIT 20"),
    ("top_postgres", "SELECT DISTINCT w.workflow_id, w.overall_score FROM workflows w JOIN workflow_integrations i ON w.workflow_id = i.workflow_id WHERE i.integration_normalized LIKE '%postgres%' ORDER BY w.overall_score DESC LIMIT 20"),
    
    # Cost & Hosting Rankings
    ("top_completely_free", "SELECT workflow_id, overall_score FROM workflows WHERE cost_class = 'FREE' ORDER BY overall_score DESC LIMIT 20"),
    ("top_mostly_free", "SELECT workflow_id, overall_score FROM workflows WHERE cost_class IN ('FREE', 'MOSTLY_FREE') ORDER BY overall_score DESC LIMIT 20"),
    ("top_self_hosted", "SELECT workflow_id, overall_score FROM workflows WHERE cost_class IN ('FREE', 'MOSTLY_FREE') AND (paid_dependencies = '[]' OR paid_dependencies IS NULL) ORDER BY overall_score DESC LIMIT 20"),
    ("top_privacy_friendly", "SELECT workflow_id, overall_score FROM workflows WHERE cost_class = 'FREE' AND security_risk_level = 'LOW' AND (paid_dependencies = '[]' OR paid_dependencies IS NULL) ORDER BY overall_score DESC LIMIT 20"),
    
    # Complexity Rankings
    ("top_beginner", "SELECT workflow_id, overall_score FROM workflows WHERE complexity = 'BEGINNER' ORDER BY overall_score DESC LIMIT 20"),
    ("top_intermediate", "SELECT workflow_id, overall_score FROM workflows WHERE complexity = 'INTERMEDIATE' ORDER BY overall_score DESC LIMIT 20"),
    ("top_advanced", "SELECT workflow_id, overall_score FROM workflows WHERE complexity = 'ADVANCED' ORDER BY overall_score DESC LIMIT 20"),
    
    # Value & Metrics
    ("best_roi_value", "SELECT workflow_id, value_score as overall_score FROM workflows ORDER BY value_score DESC, overall_score DESC LIMIT 20"),
    ("hidden_gems", "SELECT workflow_id, hidden_gem_score as overall_score FROM workflows WHERE hidden_gem_score > 0 ORDER BY hidden_gem_score DESC LIMIT 20"),
    ("best_security", "SELECT workflow_id, security_score as overall_score FROM workflows WHERE security_score >= 9.0 ORDER BY security_score DESC, overall_score DESC LIMIT 20"),
    ("best_documentation", "SELECT w.workflow_id, e.raw_score as overall_score FROM workflows w JOIN score_evidence e ON w.workflow_id = e.workflow_id WHERE e.criterion = 'documentation' ORDER BY e.raw_score DESC, w.overall_score DESC LIMIT 20"),
    ("best_quick_wins", "SELECT workflow_id, overall_score FROM workflows WHERE complexity = 'BEGINNER' AND overall_score >= 7.0 ORDER BY overall_score DESC LIMIT 20"),
]


class RankingAgent:
    def generate_all_rankings(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Executes all ranking queries and caches results into rankings table.
        """
        logger.info("Generating and caching all leaderboard rankings...")
        results = {}

        with get_db() as conn:
            conn.execute("DELETE FROM rankings")
            
            for list_name, query in RANKING_DEFINITIONS:
                try:
                    cursor = conn.execute(query)
                    rows = cursor.fetchall()
                    
                    list_items = []
                    for pos, r in enumerate(rows, start=1):
                        wf_id = r[0]
                        score_val = float(r[1])
                        
                        conn.execute(
                            """
                            INSERT INTO rankings (ranking_list, workflow_id, rank_position, score_value, updated_at)
                            VALUES (?, ?, ?, ?, DATETIME('now'))
                            """,
                            (list_name, wf_id, pos, score_val)
                        )
                        list_items.append({"workflow_id": wf_id, "rank": pos, "score": score_val})
                        
                    results[list_name] = list_items
                    logger.debug(f"Ranked {len(list_items)} items for '{list_name}'")
                except Exception as e:
                    logger.error(f"Error generating ranking '{list_name}': {e}")

        logger.info(f"Successfully generated {len(results)} ranking leaderboards.")
        return results

    def get_ranking_list(self, list_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch cached rankings for a specific list with full workflow card details."""
        rows = fetch_all(
            """
            SELECT r.rank_position, r.score_value, w.workflow_id, w.title, w.canonical_url,
                   w.creator_name, w.complexity, w.cost_class, w.overall_score, w.rating_label,
                   w.confidence_score, w.ai_score, w.views, w.description,
                   w.problem_it_solves, w.daily_life_practicality_score,
                   w.daily_life_practicality_label, w.daily_life_use_frequency,
                   w.value_score, w.hidden_gem_score, w.security_score, w.security_risk_level
            FROM rankings r
            JOIN workflows w ON r.workflow_id = w.workflow_id
            WHERE r.ranking_list = ?
            ORDER BY r.rank_position ASC
            LIMIT ?
            """,
            (list_name, limit)
        )
        return rows


if __name__ == "__main__":
    import argparse
    from database.db import init_db

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    init_db()
    agent = RankingAgent()
    rankings = agent.generate_all_rankings()
    print(f"\nGenerated {len(rankings)} ranking leaderboards:")
    for list_name, items in rankings.items():
        print(f" - {list_name}: {len(items)} workflows")
    
    print("\n--- Top 5 Daily-Life Automations ---")
    daily_life_top = agent.get_ranking_list("top_daily_life", limit=5)
    for row in daily_life_top:
        print(f" #{row['rank_position']} [{row['daily_life_practicality_score']:.1f}/10 - {row['daily_life_use_frequency']}] {row['title']}")
        print(f"    Problem: {row['problem_it_solves']}")
