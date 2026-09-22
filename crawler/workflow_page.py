"""
Workflow Page Crawler: Fetches detailed workflow templates and stores raw responses.
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from crawler.client import CrawlerClient
from database.db import get_db

logger = logging.getLogger(__name__)


class WorkflowPageCrawler:
    def __init__(
        self,
        client: Optional[CrawlerClient] = None,
        raw_dir: str = "data/raw",
        api_base_url: str = "https://api.n8n.io/api/templates/workflows"
    ):
        self.client = client or CrawlerClient()
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.api_base_url = api_base_url.rstrip("/")

    def _get_raw_path(self, workflow_id: int) -> Path:
        return self.raw_dir / f"{workflow_id}_raw.json"

    def crawl_workflow(self, workflow_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch full workflow payload and save to raw data directory."""
        raw_file = self._get_raw_path(workflow_id)
        if not force_refresh and raw_file.exists():
            try:
                with open(raw_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {
                    "workflow_id": workflow_id,
                    "data": data,
                    "raw_path": str(raw_file),
                    "from_raw_file": True
                }
            except Exception as e:
                logger.warning(f"Failed to read local raw file {raw_file}: {e}")

        api_url = f"{self.api_base_url}/{workflow_id}"
        logger.info(f"Crawling workflow {workflow_id} from {api_url}")

        res = self.client.fetch(api_url, force_refresh=force_refresh)
        if res["status_code"] != 200:
            err_msg = f"Failed to fetch workflow {workflow_id}: HTTP {res['status_code']}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        data = json.loads(res["content"])
        
        # Save raw payload
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {
            "workflow_id": workflow_id,
            "data": data,
            "raw_path": str(raw_file),
            "from_raw_file": False
        }

    async def async_crawl_workflow(self, workflow_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Asynchronously fetch full workflow payload."""
        raw_file = self._get_raw_path(workflow_id)
        if not force_refresh and raw_file.exists():
            try:
                with open(raw_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {
                    "workflow_id": workflow_id,
                    "data": data,
                    "raw_path": str(raw_file),
                    "from_raw_file": True
                }
            except Exception as e:
                logger.warning(f"Failed to read local raw file {raw_file}: {e}")

        api_url = f"{self.api_base_url}/{workflow_id}"
        logger.info(f"Async crawling workflow {workflow_id} from {api_url}")

        res = await self.client.async_fetch(api_url, force_refresh=force_refresh)
        if res["status_code"] != 200:
            err_msg = f"Failed to fetch workflow {workflow_id}: HTTP {res['status_code']}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        data = json.loads(res["content"])

        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {
            "workflow_id": workflow_id,
            "data": data,
            "raw_path": str(raw_file),
            "from_raw_file": False
        }
