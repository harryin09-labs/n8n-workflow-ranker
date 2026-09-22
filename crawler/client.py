"""
Resilient HTTP Crawler Client with rate limiting, caching, retry backoff, and error handling.
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import httpx
from crawler.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class CrawlerClient:
    def __init__(
        self,
        user_agent: str = "n8n-Workflow-Ranker/1.0 (+https://github.com/n8n-ranker)",
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        delay_seconds: float = 0.5,
        cache_dir: str = "data/cache",
        cache_enabled: bool = True,
        cache_ttl_hours: float = 24.0,
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.cache_dir = Path(cache_dir)
        self.cache_enabled = cache_enabled
        self.cache_ttl_seconds = cache_ttl_hours * 3600.0
        self.rate_limiter = RateLimiter(delay_seconds=delay_seconds)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/html, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _get_cache_key(self, url: str) -> Path:
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def _read_cache(self, url: str) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled:
            return None
        cache_file = self._get_cache_key(url)
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if time.time() - entry.get("timestamp", 0) < self.cache_ttl_seconds:
                    logger.debug(f"Cache hit for {url}")
                    return entry
            except Exception as e:
                logger.warning(f"Failed to read cache for {url}: {e}")
        return None

    def _write_cache(self, url: str, status_code: int, content: str, content_type: str) -> None:
        if not self.cache_enabled or status_code != 200:
            return
        cache_file = self._get_cache_key(url)
        entry = {
            "url": url,
            "timestamp": time.time(),
            "status_code": status_code,
            "content_type": content_type,
            "content": content,
        }
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f)
        except Exception as e:
            logger.warning(f"Failed to write cache for {url}: {e}")

    def fetch(self, url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Synchronously fetch URL with caching and backoff."""
        if not force_refresh:
            cached = self._read_cache(url)
            if cached:
                return {
                    "url": url,
                    "status_code": cached["status_code"],
                    "content": cached["content"],
                    "content_type": cached.get("content_type", ""),
                    "from_cache": True,
                }

        retries = 0
        last_error = None

        while retries <= self.max_retries:
            self.rate_limiter.wait()
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True, headers=self.headers) as client:
                    response = client.get(url)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        text_content = response.text
                        self._write_cache(url, response.status_code, text_content, content_type)
                        return {
                            "url": str(response.url),
                            "status_code": response.status_code,
                            "content": text_content,
                            "content_type": content_type,
                            "from_cache": False,
                        }
                    elif response.status_code in (429, 500, 502, 503, 504):
                        logger.warning(f"HTTP {response.status_code} for {url}, retrying ({retries+1}/{self.max_retries})...")
                        time.sleep(self.backoff_factor ** retries)
                    else:
                        return {
                            "url": str(response.url),
                            "status_code": response.status_code,
                            "content": response.text,
                            "content_type": response.headers.get("content-type", ""),
                            "from_cache": False,
                        }
            except Exception as e:
                last_error = e
                logger.warning(f"Fetch error for {url}: {e}, retrying ({retries+1}/{self.max_retries})...")
                time.sleep(self.backoff_factor ** retries)
            retries += 1

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} retries: {last_error}")

    async def async_fetch(self, url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Asynchronously fetch URL with caching and backoff."""
        if not force_refresh:
            cached = self._read_cache(url)
            if cached:
                return {
                    "url": url,
                    "status_code": cached["status_code"],
                    "content": cached["content"],
                    "content_type": cached.get("content_type", ""),
                    "from_cache": True,
                }

        retries = 0
        last_error = None

        while retries <= self.max_retries:
            await self.rate_limiter.async_wait()
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True, headers=self.headers) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        text_content = response.text
                        self._write_cache(url, response.status_code, text_content, content_type)
                        return {
                            "url": str(response.url),
                            "status_code": response.status_code,
                            "content": text_content,
                            "content_type": content_type,
                            "from_cache": False,
                        }
                    elif response.status_code in (429, 500, 502, 503, 504):
                        logger.warning(f"HTTP {response.status_code} for {url}, retrying ({retries+1}/{self.max_retries})...")
                        await asyncio.sleep(self.backoff_factor ** retries)
                    else:
                        return {
                            "url": str(response.url),
                            "status_code": response.status_code,
                            "content": response.text,
                            "content_type": response.headers.get("content-type", ""),
                            "from_cache": False,
                        }
            except Exception as e:
                last_error = e
                logger.warning(f"Async fetch error for {url}: {e}, retrying ({retries+1}/{self.max_retries})...")
                await asyncio.sleep(self.backoff_factor ** retries)
            retries += 1

        raise RuntimeError(f"Async fetch failed for {url} after {self.max_retries} retries: {last_error}")
