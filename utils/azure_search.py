"""Lightweight Azure Bing search helper used when SEARCH_PROVIDER=azure_bing."""

from __future__ import annotations

import re
from html import unescape
from typing import Dict, List, Optional, Union

import httpx


class AzureBingSearchClient:
    """Wrapper around Bing Web Search API (Azure Cognitive Services)."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        market: str = "en-US",
        timeout_seconds: float = 20.0,
    ) -> None:
        if not endpoint:
            raise ValueError("Azure Bing Search endpoint is required")
        if not api_key:
            raise ValueError("Azure Bing Search API key is required")
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.market = market
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        *,
        query: str,
        count: int = 10,
        include_domains: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        """Execute a Bing web search."""
        if include_domains:
            # Apply site filters using OR semantics
            domain_filter = " OR ".join(f"site:{domain}" for domain in include_domains)
            query = f"({query}) ({domain_filter})"

        params = {
            "q": query,
            "count": count,
            "mkt": self.market,
            "responseFilter": "Webpages",
        }
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        url = f"{self.endpoint}/bing/v7.0/search"

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        results: List[Dict[str, Union[str, float]]] = []
        for item in payload.get("webPages", {}).get("value", []):
            results.append(
                {
                    "title": item.get("name") or "",
                    "url": item.get("url") or "",
                    "content": item.get("snippet") or "",
                    "score": 1.0,
                }
            )

        return {"results": results}

    def extract(self, urls: List[str], *, max_chars: int = 2000) -> List[Dict[str, str]]:
        """Fetch raw HTML and return simplified text snippets for top URLs."""
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TravelAgentBot/1.0; +https://github.com/elbruno/agent-framework-travel-assistant)",
        }
        extracts: List[Dict[str, str]] = []

        with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
            for url in urls:
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    text = self._strip_html(response.text)
                    if not text:
                        continue
                    snippet = text[:max_chars]
                    extracts.append({"url": url, "content": snippet})
                except Exception:
                    continue
        return extracts

    @staticmethod
    def _strip_html(raw_html: str) -> str:
        """Remove HTML tags and collapse whitespace."""
        # Remove script/style blocks
        cleaned = re.sub(r"<(script|style)[^>]*>.*?</\\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
        # Remove all tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()
