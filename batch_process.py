"""
Batch Processor: Picks up pending discovery records, crawls, extracts, analyzes, scores.
Supports checkpointing for crash recovery.
"""
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from database.db import init_db, get_db, fetch_all
from agents.crawler import CrawlerAgent
from agents.extractor import ExtractorAgent
from agents.analyst import AnalystAgent
from agents.security import SecurityAgent
from agents.scorer import ScorerAgent
from database.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BatchProcessor")

CHECKPOINT_FILE = Path("data/batch_checkpoint.json")


class BatchProcessor:
    def __init__(self, batch_size: int = 100, max_workers: int = 5):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.crawler = CrawlerAgent()
        self.extractor = ExtractorAgent()
        self.analyst = AnalystAgent()
        self.security = SecurityAgent()
        self.scorer = ScorerAgent()

    def get_pending_ids(self, limit: int) -> List[int]:
        """Get workflow IDs that are pending crawl and NOT yet in workflows table."""
        rows = fetch_all(
            """SELECT d.workflow_id
               FROM discovery_records d
               LEFT JOIN workflows w ON d.workflow_id = w.workflow_id
               WHERE d.crawl_status IN ('pending', 'failed')
                 AND w.workflow_id IS NULL
               ORDER BY d.workflow_id ASC
               LIMIT ?""",
            (limit,)
        )
        return [r["workflow_id"] for r in rows]

    def process_single(self, workflow_id: int) -> Dict[str, Any]:
        """Process one workflow through crawl->extract->analyze->score with checkpoint."""
        try:
            # Crawl
            logger.info(f"[{workflow_id}] Crawling...")
            crawl_res = self.crawler.crawl_workflow(workflow_id, force_refresh=False)

            if crawl_res.get("crawl_status") != "crawled":
                return {"workflow_id": workflow_id, "status": "crawl_failed", "error": crawl_res.get("error", "Unknown")}

            raw_data = crawl_res.get("data", {})
            if not raw_data or not isinstance(raw_data, dict):
                return {"workflow_id": workflow_id, "status": "crawl_failed", "error": "Empty or invalid data"}

            # Extract
            logger.info(f"[{workflow_id}] Extracting...")
            normalized = self.extractor.extract_and_normalize(workflow_id, raw_data)
            normalized["raw_storage_path"] = crawl_res.get("raw_path", "")
            norm_file = self.extractor.normalized_dir / f"{workflow_id}_normalized.json"
            with open(norm_file, "w", encoding="utf-8") as f:
                json.dump(normalized, f, indent=2, default=str)
            normalized["normalized_storage_path"] = str(norm_file)

            # Analyze (all 8 dimensions)
            logger.info(f"[{workflow_id}] Analyzing...")
            analyzed = self.analyst.analyze_workflow(normalized)

            # Security review
            reviewed = self.security.review(analyzed)

            # Score and persist
            logger.info(f"[{workflow_id}] Scoring...")
            with get_connection() as conn:
                scored = self.scorer.score_and_persist(reviewed, conn=conn)

            # Update discovery record
            with get_db() as conn:
                conn.execute(
                    "UPDATE discovery_records SET crawl_status = 'processed', last_seen = DATETIME('now') WHERE workflow_id = ?",
                    (workflow_id,)
                )
                conn.commit()

            logger.info(f"[{workflow_id}] Done — Score: {scored.get('overall_score', 0):.2f}")
            return {"workflow_id": workflow_id, "status": "success", "score": scored.get("overall_score", 0)}

        except Exception as e:
            logger.error(f"[{workflow_id}] Failed: {e}")
            # Mark as failed
            try:
                with get_db() as conn:
                    conn.execute(
                        "UPDATE discovery_records SET crawl_status = 'failed', last_seen = DATETIME('now') WHERE workflow_id = ?",
                        (workflow_id,)
                    )
                    conn.commit()
            except:
                pass
            return {"workflow_id": workflow_id, "status": "error", "error": str(e)}

    def save_checkpoint(self, processed: int, total: int, errors: List[int]):
        """Save progress checkpoint for crash recovery."""
        data = {"processed": processed, "total": total, "errors": errors, "timestamp": time.time()}
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(data, f)
        logger.info(f"Checkpoint saved: {processed}/{total} processed, {len(errors)} errors")

    def load_checkpoint(self) -> Optional[Dict]:
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE) as f:
                return json.load(f)
        return None

    def run(self, target_count: int = 500):
        """Run batch processing for target_count workflows."""
        init_db()
        checkpoint = self.load_checkpoint()

        if checkpoint:
            logger.info(f"Resuming from checkpoint: {checkpoint['processed']} already done")

        pending = self.get_pending_ids(limit=target_count)
        if not pending:
            logger.info("No pending workflows to process!")
            return

        logger.info(f"Processing {len(pending)} workflows in batches of {self.batch_size}...")

        total_processed = 0
        total_success = 0
        total_errors = []
        results = []

        # Process in batches
        for batch_start in range(0, len(pending), self.batch_size):
            batch = pending[batch_start:batch_start + self.batch_size]
            logger.info(f"\n=== Batch {batch_start//self.batch_size + 1}: IDs {batch[0]}..{batch[-1]} ({len(batch)} workflows) ===")

            # Process batch
            batch_results = []
            for wf_id in batch:
                result = self.process_single(wf_id)
                batch_results.append(result)
                if result["status"] == "success":
                    total_success += 1
                else:
                    total_errors.append(wf_id)
                total_processed += 1

                # Small delay between individual workflows to be polite
                time.sleep(0.1)

            results.extend(batch_results)

            # Checkpoint after each batch
            self.save_checkpoint(total_processed, len(pending), total_errors)

            # Batch summary
            success_count = sum(1 for r in batch_results if r["status"] == "success")
            logger.info(f"Batch complete: {success_count}/{len(batch)} succeeded ({len(batch) - success_count} failed)")

        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH PROCESSING COMPLETE")
        logger.info(f"  Total attempted: {total_processed}")
        logger.info(f"  Successful: {total_success}")
        logger.info(f"  Failed: {len(total_errors)}")
        logger.info(f"{'='*60}")

        # Save final results
        results_file = Path("data/batch_results.json")
        with open(results_file, "w") as f:
            json.dump({"results": results, "timestamp": time.time()}, f, indent=2)
        logger.info(f"Results saved to {results_file}")

        # Remove checkpoint on success
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()

        return {"attempted": total_processed, "success": total_success, "failed": len(total_errors)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Process Workflows")
    parser.add_argument("--count", type=int, default=500, help="Number of workflows to process (default: 500)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for checkpointing (default: 100)")
    parser.add_argument("--workers", type=int, default=5, help="Max concurrent workers (default: 5)")
    args = parser.parse_args()

    processor = BatchProcessor(batch_size=args.batch_size, max_workers=args.workers)
    result = processor.run(target_count=args.count)

    print(f"\nFinal result: {result}")