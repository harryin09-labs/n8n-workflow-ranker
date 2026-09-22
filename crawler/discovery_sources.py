"""
Discovery Sources: Sitemaps, Search API, and Catalog Crawling for n8n workflow discovery.
"""

import re
import xml.etree.ElementTree as ET
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from crawler.client import CrawlerClient
from database.db import get_db, execute_query, fetch_all

logger = logging.getLogger(__name__)

WORKFLOW_URL_REGEX = re.compile(r"https?://n8n\.io/workflows/(\d+)(?:-([^/]+))?/?", re.IGNORECASE)


def parse_workflow_url(url: str) -> Optional[Tuple[int, Optional[str], str]]:
    """Extract (workflow_id, slug, canonical_url) from a workflow URL."""
    m = WORKFLOW_URL_REGEX.search(url)
    if not m:
        return None
    wf_id = int(m.group(1))
    slug = m.group(2)
    if slug:
        canonical_url = f"https://n8n.io/workflows/{wf_id}-{slug}/"
    else:
        canonical_url = f"https://n8n.io/workflows/{wf_id}/"
    return wf_id, slug, canonical_url


class DiscoverySource:
    def __init__(self, client: Optional[CrawlerClient] = None):
        self.client = client or CrawlerClient()

    def discover_from_sitemap(
        self,
        sitemap_url: str = "https://n8n.io/sitemap-workflows.xml",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Parse workflow URLs from n8n sitemap."""
        logger.info(f"Discovering workflows from sitemap: {sitemap_url}")
        res = self.client.fetch(sitemap_url)
        if res["status_code"] != 200:
            logger.error(f"Failed to fetch sitemap: HTTP {res['status_code']}")
            return []

        xml_content = res["content"]
        # Strip namespaces for simple parsing
        xml_clean = re.sub(r' xmlns="[^"]+"', '', xml_content, count=1)
        root = ET.fromstring(xml_clean)

        discovered = []
        for url_node in root.findall(".//url"):
            loc = url_node.find("loc")
            if loc is not None and loc.text:
                parsed = parse_workflow_url(loc.text.strip())
                if parsed:
                    wf_id, slug, canon_url = parsed
                    lastmod = url_node.find("lastmod")
                    lastmod_val = lastmod.text if lastmod is not None else None
                    discovered.append({
                        "workflow_id": wf_id,
                        "slug": slug,
                        "canonical_url": canon_url,
                        "discovery_source": "sitemap",
                        "lastmod": lastmod_val
                    })
                    if limit and len(discovered) >= limit:
                        break

        logger.info(f"Discovered {len(discovered)} workflows from sitemap.")
        return discovered

    def discover_from_search_api(
        self,
        search_api_url: str = "https://api.n8n.io/api/templates/search",
        limit: int = 20,
        page_size: int = 20,
        search_query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover workflows using n8n official search API."""
        logger.info(f"Discovering workflows from search API: {search_api_url} (limit={limit})")
        discovered = []
        page = 1

        while len(discovered) < limit:
            params = f"?page={page}&rows={page_size}"
            if search_query:
                params += f"&search={search_query}"
            if category:
                params += f"&categories={category}"

            url = f"{search_api_url}{params}"
            try:
                res = self.client.fetch(url)
                if res["status_code"] != 200:
                    logger.error(f"Search API returned {res['status_code']}")
                    break

                data = json.loads(res["content"])
                workflows = data.get("workflows", [])
                if not workflows:
                    break

                for wf in workflows:
                    wf_id = wf.get("id")
                    if not wf_id:
                        continue
                    name = wf.get("name", "")
                    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
                    canon_url = f"https://n8n.io/workflows/{wf_id}-{slug}/" if slug else f"https://n8n.io/workflows/{wf_id}/"

                    discovered.append({
                        "workflow_id": wf_id,
                        "slug": slug,
                        "canonical_url": canon_url,
                        "discovery_source": "search_api",
                        "initial_data": wf
                    })
                    if len(discovered) >= limit:
                        break

                total_available = data.get("totalWorkflows", 0)
                if len(discovered) >= total_available:
                    break
                page += 1
            except Exception as e:
                logger.error(f"Error querying search API page {page}: {e}")
                break

        logger.info(f"Discovered {len(discovered)} workflows from search API.")
        return discovered

    def store_discovered(self, discovered_list: List[Dict[str, Any]]) -> int:
        """Store discovered workflows in database, avoiding duplicate inserts."""
        inserted_count = 0
        with get_db() as conn:
            for item in discovered_list:
                wf_id = item["workflow_id"]
                canon_url = item["canonical_url"]
                slug = item.get("slug")
                source = item.get("discovery_source", "sitemap")

                cursor = conn.execute(
                    """
                    INSERT INTO discovery_records (workflow_id, canonical_url, slug, discovery_source, first_seen, last_seen, crawl_status)
                    VALUES (?, ?, ?, ?, DATETIME('now'), DATETIME('now'), 'pending')
                    ON CONFLICT(workflow_id) DO UPDATE SET
                        last_seen = DATETIME('now'),
                        canonical_url = excluded.canonical_url
                    """,
                    (wf_id, canon_url, slug, source)
                )
                if cursor.rowcount > 0:
                    inserted_count += 1
        logger.info(f"Updated/Inserted {inserted_count} records into discovery_records.")
        return inserted_count
