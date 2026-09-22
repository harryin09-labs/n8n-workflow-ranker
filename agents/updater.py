"""
Incremental Update Agent: Continuously discovers, verifies, detects version diffs, and updates rankings.
"""

import logging
from typing import Dict, Any, List
from crawler.discovery_sources import DiscoverySource
from crawler.workflow_page import WorkflowPageCrawler
from extraction.normalization import Normalizer
from agents.extractor import ExtractorAgent
from agents.analyst import AnalystAgent
from agents.security import SecurityAgent
from agents.scorer import ScorerAgent
from agents.ranking import RankingAgent
from database.db import get_db, execute_query, fetch_one, fetch_all

logger = logging.getLogger(__name__)


class IncrementalUpdateAgent:
    def __init__(self):
        self.discovery = DiscoverySource()
        self.crawler = WorkflowPageCrawler()
        self.extractor = ExtractorAgent()
        self.analyst = AnalystAgent()
        self.security = SecurityAgent()
        self.scorer = ScorerAgent()
        self.ranking = RankingAgent()
        self.normalizer = Normalizer()

    def check_and_update_workflow(self, workflow_id: int) -> Dict[str, Any]:
        """
        Processes a single workflow incrementally:
        - Detects whether it is NEW, CHANGED, or UNCHANGED.
        - Archives historical version if changed.
        """
        existing = fetch_one("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))

        try:
            # Fetch fresh raw data
            crawl_res = self.crawler.crawl_workflow(workflow_id, force_refresh=True)
            raw_data = crawl_res["data"]
            new_content_hash = self.normalizer.compute_content_hash(raw_data)
            
            if not existing:
                # NEW WORKFLOW
                logger.info(f"Processing NEW workflow {workflow_id}")
                norm_data = self.extractor.extract_and_normalize(workflow_id, raw_data)
                norm_data["raw_storage_path"] = crawl_res["raw_path"]
                norm_data["normalized_storage_path"] = self.extractor.save_normalized(norm_data)
                
                analyzed = self.analyst.analyze_workflow(norm_data)
                reviewed = self.security.review_and_store(analyzed)
                scored = self.scorer.score_and_persist(reviewed)
                
                return {"workflow_id": workflow_id, "action": "created", "score": scored["overall_score"]}

            elif existing["content_hash"] != new_content_hash:
                # CHANGED WORKFLOW -> Versioning
                old_ver = existing["current_version"] or 1
                new_ver = old_ver + 1
                logger.info(f"Workflow {workflow_id} changed! Archiving v{old_ver} and upgrading to v{new_ver}")

                # Save historical version
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO workflow_versions (
                            workflow_id, version_number, title, description, node_count,
                            content_hash, structure_hash, overall_score, raw_storage_path, created_at, change_summary
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'), 'Automated incremental change detection update.')
                        """,
                        (
                            workflow_id,
                            old_ver,
                            existing["title"],
                            existing["description"],
                            existing["node_count"],
                            existing["content_hash"],
                            existing["structure_hash"],
                            existing["overall_score"],
                            existing["raw_storage_path"],
                        )
                    )

                norm_data = self.extractor.extract_and_normalize(workflow_id, raw_data)
                norm_data["current_version"] = new_ver
                norm_data["raw_storage_path"] = crawl_res["raw_path"]
                norm_data["normalized_storage_path"] = self.extractor.save_normalized(norm_data)

                analyzed = self.analyst.analyze_workflow(norm_data)
                reviewed = self.security.review_and_store(analyzed)
                scored = self.scorer.score_and_persist(reviewed)

                execute_query(
                    "UPDATE workflows SET current_version = ?, last_changed = DATETIME('now') WHERE workflow_id = ?",
                    (new_ver, workflow_id)
                )

                return {"workflow_id": workflow_id, "action": "version_upgraded", "new_version": new_ver, "score": scored["overall_score"]}

            else:
                # UNCHANGED WORKFLOW
                logger.debug(f"Workflow {workflow_id} unchanged. Updating last_checked timestamp.")
                execute_query(
                    "UPDATE workflows SET last_checked = DATETIME('now') WHERE workflow_id = ?",
                    (workflow_id,)
                )
                return {"workflow_id": workflow_id, "action": "unchanged"}

        except Exception as e:
            logger.error(f"Error checking/updating workflow {workflow_id}: {e}")
            return {"workflow_id": workflow_id, "action": "error", "error": str(e)}

    def run_update_cycle(self, limit: int = 20) -> Dict[str, Any]:
        """Runs a complete incremental update cycle."""
        logger.info(f"Starting incremental update cycle (limit={limit})...")
        
        # Discover latest
        discovered = self.discovery.discover_from_search_api(limit=limit)
        self.discovery.store_discovered(discovered)

        summary = {"created": 0, "version_upgraded": 0, "unchanged": 0, "errors": 0}

        for item in discovered:
            wf_id = item["workflow_id"]
            res = self.check_and_update_workflow(wf_id)
            act = res.get("action")
            if act in summary:
                summary[act] += 1
            else:
                summary["errors"] += 1

        # Refresh rankings
        self.ranking.generate_all_rankings()

        logger.info(f"Incremental update cycle completed: {summary}")
        return summary


if __name__ == "__main__":
    import argparse
    from database.db import init_db

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Incremental Update Agent")
    parser.add_argument("--limit", type=int, default=20, help="Number of workflows to check for updates (default: 20)")
    args = parser.parse_args()

    init_db()
    agent = IncrementalUpdateAgent()
    summary = agent.run_update_cycle(limit=args.limit)
    print("\n" + "="*50)
    print("UPDATE CYCLE SUMMARY:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("="*50)
