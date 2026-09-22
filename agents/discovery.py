"""
Discovery Agent: Coordinates workflow discovery from multiple sources and persists discovery records.
"""

import logging
from typing import List, Dict, Any, Optional
from crawler import DiscoverySource, CrawlerClient

logger = logging.getLogger(__name__)


class DiscoveryAgent:
    def __init__(self, client: Optional[CrawlerClient] = None):
        self.client = client or CrawlerClient()
        self.discovery_source = DiscoverySource(self.client)

    def run_discovery(
        self,
        limit: int = 20,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Run discovery from configured sources."""
        sources = sources or ["sitemap", "search_api"]
        all_discovered = []

        if "sitemap" in sources:
            sitemap_discovered = self.discovery_source.discover_from_sitemap(limit=limit)
            all_discovered.extend(sitemap_discovered)
            logger.info(f"Sitemap discovery yielded {len(sitemap_discovered)} workflows")

        if "search_api" in sources:
            remaining = max(0, limit - len(all_discovered))
            if remaining > 0:
                search_discovered = self.discovery_source.discover_from_search_api(limit=remaining)
                all_discovered.extend(search_discovered)
                logger.info(f"Search API discovery yielded {len(search_discovered)} workflows")

        # Deduplicate by workflow_id
        seen = set()
        deduped = []
        for item in all_discovered:
            wf_id = item.get("workflow_id")
            if wf_id and wf_id not in seen:
                seen.add(wf_id)
                deduped.append(item)

        logger.info(f"Total unique workflows discovered: {len(deduped)}")
        return deduped[:limit]

    def store_discovered(self, discovered_list: List[Dict[str, Any]]) -> int:
        """Persist discovery records to database."""
        return self.discovery_source.store_discovered(discovered_list)

    def get_pending_crawl(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get workflows that are pending crawl from discovery_records."""
        from database.db import fetch_all
        rows = fetch_all(
            """
            SELECT workflow_id, canonical_url, slug, discovery_source, crawl_status
            FROM discovery_records
            WHERE crawl_status = 'pending'
            ORDER BY first_seen ASC
            LIMIT ?
            """,
            (limit,)
        )
        return rows

    def mark_crawl_status(self, workflow_id: int, status: str) -> int:
        """Update crawl status for a workflow."""
        from database.db import execute_query
        return execute_query(
            "UPDATE discovery_records SET crawl_status = ?, last_seen = DATETIME('now') WHERE workflow_id = ?",
            (status, workflow_id)
        )


if __name__ == "__main__":
    import argparse
    from database.db import init_db

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Workflow Discovery Agent")
    parser.add_argument("--limit", type=int, default=20, help="Max workflows to discover (default: 20)")
    args = parser.parse_args()

    init_db()
    agent = DiscoveryAgent()
    discovered = agent.run_discovery(limit=args.limit)
    agent.store_discovered(discovered)
    print(f"\nDiscovered and stored {len(discovered)} workflows.")
    for d in discovered:
        print(f" - #{d['workflow_id']}: {d['canonical_url']}")