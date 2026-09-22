"""
Crawler Agent: Coordinates the polite crawling of discovered workflows with checkpointing and error handling.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from crawler import CrawlerClient, WorkflowPageCrawler
from database.db import get_db, execute_query, fetch_one, fetch_all

logger = logging.getLogger(__name__)


class CrawlerAgent:
    def __init__(self, client: Optional[CrawlerClient] = None, max_workers: int = 5):
        self.client = client or CrawlerClient()
        self.workflow_crawler = WorkflowPageCrawler(self.client)
        self.max_workers = max_workers

    def crawl_workflow(self, workflow_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Crawl a single workflow and store raw data."""
        logger.info(f"Crawling workflow {workflow_id}")
        
        # Mark as crawling
        execute_query(
            "UPDATE discovery_records SET crawl_status = 'crawling' WHERE workflow_id = ?",
            (workflow_id,)
        )

        try:
            result = self.workflow_crawler.crawl_workflow(workflow_id, force_refresh=force_refresh)
            
            # Mark as crawled
            execute_query(
                "UPDATE discovery_records SET crawl_status = 'crawled', last_seen = DATETIME('now') WHERE workflow_id = ?",
                (workflow_id,)
            )
            
            result["crawl_status"] = "crawled"
            return result
            
        except Exception as e:
            logger.error(f"Crawl failed for workflow {workflow_id}: {e}")
            execute_query(
                "UPDATE discovery_records SET crawl_status = 'failed', last_seen = DATETIME('now') WHERE workflow_id = ?",
                (workflow_id,)
            )
            return {
                "workflow_id": workflow_id,
                "crawl_status": "failed",
                "error": str(e)
            }

    def crawl_batch(self, workflow_ids: List[int], force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Crawl multiple workflows in parallel with thread pool."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_wf = {
                executor.submit(self.crawl_workflow, wf_id, force_refresh): wf_id 
                for wf_id in workflow_ids
            }
            
            for future in as_completed(future_to_wf):
                wf_id = future_to_wf[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Exception crawling workflow {wf_id}: {e}")
                    results.append({
                        "workflow_id": wf_id,
                        "crawl_status": "failed",
                        "error": str(e)
                    })
        
        crawled_count = sum(1 for r in results if r.get("crawl_status") == "crawled")
        failed_count = sum(1 for r in results if r.get("crawl_status") == "failed")
        logger.info(f"Batch crawl complete: {crawled_count} succeeded, {failed_count} failed")
        
        return results

    async def async_crawl_batch(self, workflow_ids: List[int], force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Asynchronously crawl multiple workflows."""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def crawl_one(wf_id: int) -> Dict[str, Any]:
            async with semaphore:
                logger.info(f"Async crawling workflow {wf_id}")
                execute_query(
                    "UPDATE discovery_records SET crawl_status = 'crawling' WHERE workflow_id = ?",
                    (wf_id,)
                )
                try:
                    result = await self.workflow_crawler.async_crawl_workflow(wf_id, force_refresh=force_refresh)
                    execute_query(
                        "UPDATE discovery_records SET crawl_status = 'crawled', last_seen = DATETIME('now') WHERE workflow_id = ?",
                        (wf_id,)
                    )
                    result["crawl_status"] = "crawled"
                    return result
                except Exception as e:
                    logger.error(f"Async crawl failed for workflow {wf_id}: {e}")
                    execute_query(
                        "UPDATE discovery_records SET crawl_status = 'failed', last_seen = DATETIME('now') WHERE workflow_id = ?",
                        (wf_id,)
                    )
                    return {"workflow_id": wf_id, "crawl_status": "failed", "error": str(e)}

        tasks = [crawl_one(wf_id) for wf_id in workflow_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append({
                    "workflow_id": workflow_ids[i],
                    "crawl_status": "failed",
                    "error": str(result)
                })
            else:
                processed.append(result)
        
        return processed

    def get_crawlable_ids(self, limit: int = 20, status: str = "pending") -> List[int]:
        """Get workflow IDs ready for crawling."""
        rows = fetch_all(
            "SELECT workflow_id FROM discovery_records WHERE crawl_status = ? ORDER BY first_seen ASC LIMIT ?",
            (status, limit)
        )
        return [r["workflow_id"] for r in rows]


if __name__ == "__main__":
    import argparse
    from database.db import init_db

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Workflow Crawler Agent")
    parser.add_argument("--limit", type=int, default=20, help="Max workflows to crawl (default: 20)")
    parser.add_argument("--refresh", action="store_true", help="Force re-crawl cached workflows")
    args = parser.parse_args()

    init_db()
    agent = CrawlerAgent()
    ids = agent.get_crawlable_ids(limit=args.limit)
    if not ids:
        # If no pending, crawl discovered
        rows = fetch_all("SELECT workflow_id FROM discovery_records ORDER BY first_seen ASC LIMIT ?", (args.limit,))
        ids = [r["workflow_id"] for r in rows]
    
    print(f"Crawling {len(ids)} workflows: {ids}")
    results = agent.crawl_batch(ids, force_refresh=args.refresh)
    success = sum(1 for r in results if r.get("crawl_status") == "crawled")
    print(f"\nFinished crawl batch: {success}/{len(results)} succeeded.")