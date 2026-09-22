"""
Supervisor Agent: Orchestrates the entire pipeline from Discovery to Crawling, Extraction,
Analysis, Scoring, Deduplication, and Ranking.
"""

import sys
import argparse
import logging
from typing import Dict, Any, Optional
from database.db import init_db
from agents.discovery import DiscoveryAgent
from agents.crawler import CrawlerAgent
from agents.extractor import ExtractorAgent
from agents.analyst import AnalystAgent
from agents.security import SecurityAgent
from agents.scorer import ScorerAgent
from agents.deduplicator import DeduplicatorAgent
from agents.ranking import RankingAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Supervisor")


class SupervisorAgent:
    def __init__(self, limit: int = 20, timeout: int = 180):
        self.limit = limit
        self.timeout = timeout
        self.discovery_agent = DiscoveryAgent()
        self.crawler_agent = CrawlerAgent()
        self.extractor_agent = ExtractorAgent()
        self.analyst_agent = AnalystAgent()
        self.security_agent = SecurityAgent()
        self.scorer_agent = ScorerAgent()
        self.deduplicator_agent = DeduplicatorAgent()
        self.ranking_agent = RankingAgent()

    def run_pipeline(self, limit: Optional[int] = None) -> Dict[str, Any]:
        target_limit = limit or self.limit
        logger.info(f"=== Starting n8n Workflow Intelligence Pipeline (Limit: {target_limit}, Timeout: {self.timeout}s) ===")

        # 0. Ensure Database Initialized
        init_db()

        # 1. DISCOVERY
        logger.info("--- Step 1: Discovering Workflow Templates ---")
        discovered = self.discovery_agent.run_discovery(limit=target_limit)
        self.discovery_agent.store_discovered(discovered)
        wf_ids = [d["workflow_id"] for d in discovered]
        logger.info(f"Discovered {len(wf_ids)} workflows: {wf_ids}")

        # 2. CRAWL
        logger.info("--- Step 2: Crawling Workflows & Storing Raw Payloads ---")
        crawled_results = self.crawler_agent.crawl_batch(wf_ids)
        successful_crawls = [r for r in crawled_results if r.get("crawl_status") == "crawled"]
        logger.info(f"Successfully crawled {len(successful_crawls)}/{len(wf_ids)} workflows")

        # 3. EXTRACT, NORMALIZE, ANALYZE, REVIEW, SCORE
        logger.info("--- Step 3: Extracting, Normalizing, Analyzing, and Scoring ---")
        processed_count = 0
        scored_workflows = []

        from database.db import get_connection
        db_conn = get_connection()

        try:
            with db_conn:
                for item in successful_crawls:
                    wf_id = item["workflow_id"]
                    try:
                        # Extract & Normalize
                        normalized = self.extractor_agent.extract_and_normalize(wf_id, item["data"])
                        normalized["raw_storage_path"] = item["raw_path"]
                        # Save normalized to disk without separate DB transaction
                        norm_file = self.extractor_agent.normalized_dir / f"{wf_id}_normalized.json"
                        with open(norm_file, "w", encoding="utf-8") as f:
                            import json
                            json.dump(normalized, f, indent=2, default=str)
                        normalized["normalized_storage_path"] = str(norm_file)

                        # Multi-dimensional Analysis
                        analyzed = self.analyst_agent.analyze_workflow(normalized)

                        # Security Review
                        reviewed = self.security_agent.review(analyzed)

                        # Deterministic Scoring & Persistence
                        scored = self.scorer_agent.score_and_persist(reviewed, conn=db_conn)
                        scored_workflows.append(scored)
                        processed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing workflow {wf_id}: {e}")
        finally:
            db_conn.close()

        logger.info(f"Successfully analyzed and scored {processed_count} workflows.")

        # 4. DEDUPLICATION
        logger.info("--- Step 4: Multi-Layer Duplicate Detection ---")
        duplicates = self.deduplicator_agent.scan_for_duplicates()
        logger.info(f"Detected {len(duplicates)} duplicate/variant links.")

        # 5. RANKINGS GENERATION
        logger.info("--- Step 5: Generating Leaderboards & Category Rankings ---")
        rankings = self.ranking_agent.generate_all_rankings()
        logger.info(f"Generated {len(rankings)} category leaderboards.")

        logger.info("=== Pipeline Execution Complete! ===")
        return {
            "discovered": len(wf_ids),
            "crawled": len(successful_crawls),
            "scored": processed_count,
            "duplicates": len(duplicates),
            "rankings_generated": len(rankings),
        }


def main():
    parser = argparse.ArgumentParser(description="n8n Workflow Intelligence & Ranking System CLI")
    parser.add_argument("--limit", type=int, default=20, help="Number of workflows to process for MVP (default: 20)")
    parser.add_argument("--timeout", type=int, default=180, help="Pipeline timeout in seconds (default: 180)")
    parser.add_argument("--init-db", action="store_true", help="Initialize database only")
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("Database initialized.")
        return

    supervisor = SupervisorAgent(limit=args.limit)
    summary = supervisor.run_pipeline()
    print("\n" + "="*50)
    print("PIPELINE SUMMARY:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("="*50)


if __name__ == "__main__":
    main()
