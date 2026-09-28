"""HTTP client for fetching a job's detail page."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from config.logging_config import get_logger
from config.settings import HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT

logger = get_logger(__name__)



class FreepHttpClient:
    """Fetches and parses raw HTML pages from Freep."""

    def __init__(self, timeout_seconds: int = HTTP_TIMEOUT_SECONDS) -> None:
        self._timeout_seconds = timeout_seconds
        self._headers = {"User-Agent": HTTP_USER_AGENT}

    def get_detail_soup(self, url: str) -> BeautifulSoup:
        """Fetch a job detail page and return it as a parsed BeautifulSoup tree."""
        response = requests.get(url, headers=self._headers, timeout=self._timeout_seconds)

        logger.info("HTTP %s -> %s", response.status_code, url)
        response.raise_for_status()

        return BeautifulSoup(response.text, "html.parser")


if __name__ == "__main__":
    import sys
    DEFAULT_TEST_URL = "https://www.freep.nl/opdracht/ai-developer-1"


    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_URL

    client = FreepHttpClient()
    soup = client.get_detail_soup(url)

    title = soup.select_one("h1")
    print(f"Fetched {url}")
    print(f"HTML length: {len(str(soup))}")
    print(f"<h1> found: {title.get_text(strip=True) if title else None}")
