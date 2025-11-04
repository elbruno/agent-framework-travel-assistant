"""Azure AI Foundry search agent client wrapper using Agent Framework SDK."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential


class SearchProviderError(Exception):
    """Exception raised when the search provider encounters an error."""


class AzureFoundrySearchClient:
    """Client wrapper for Azure AI Foundry search agent using Agent Framework SDK."""

    def __init__(
        self,
        *,
        endpoint: str,
        agent_id: str,
    ) -> None:
        if not endpoint:
            raise ValueError("Azure AI Foundry endpoint is required")
        if not agent_id:
            raise ValueError("Azure AI Foundry agent ID is required")

        self.endpoint = endpoint.rstrip("/")
        self.agent_id = agent_id

    def search(
        self,
        *,
        query: str,
        count: int = 10,
        include_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute a search via the Azure AI Foundry search agent."""

        def _run(coro):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(coro)
                loop.run_until_complete(loop.shutdown_asyncgens())
                return result
            finally:
                asyncio.set_event_loop(None)
                loop.close()

        try:
            return _run(self._search_async(query=query, count=count, include_domains=include_domains))
        except SearchProviderError:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch
            raise SearchProviderError(f"Azure AI Foundry search error: {exc}") from exc

    async def _search_async(
        self,
        *,
        query: str,
        count: int,
        include_domains: Optional[List[str]],
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(query=query, count=count, include_domains=include_domains)

        async with DefaultAzureCredential() as credential:
            chat_client = AzureAIAgentClient(
                project_endpoint=self.endpoint,
                agent_id=self.agent_id,
                async_credential=credential,
            )

            async with ChatAgent(chat_client=chat_client) as agent:
                response = await agent.run(prompt)

        return self._parse_response(response)

    def extract(
        self,
        urls: List[str],
        *,
        max_chars: int = 2000,
    ) -> List[Dict[str, str]]:
        """Extraction is handled directly in the search response."""

        return []

    def _build_prompt(
        self,
        *,
        query: str,
        count: int,
        include_domains: Optional[List[str]],
    ) -> str:
        parts: List[str] = [
            f"Please perform a fresh web search for: {query.strip()}.",
            f"Return at most {max(1, count)} high quality results.",
            "Respond strictly with JSON containing 'results' (list) and 'extractions' (list).",
            "Each result must include title, url, content snippet, and score fields.",
            "If you extract detailed content, include it under 'extractions' as objects with url and content.",
        ]

        if include_domains:
            domains = ", ".join(include_domains)
            parts.append(f"Prioritize sources from the following domains: {domains}.")

        return " ".join(parts)

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        text_payload = ""
        value_payload: Any = None

        try:
            value_payload = getattr(response, "value", None)
        except Exception:
            value_payload = None

        if isinstance(value_payload, dict):
            data = value_payload
        else:
            try:
                text_payload = (response.text or "").strip()
            except Exception:
                text_payload = ""
            data = self._extract_json(text_payload)

        if not isinstance(data, dict):
            raise SearchProviderError("Search agent response was not a JSON object")

        results_raw = data.get("results", [])
        extractions_raw = data.get("extractions", [])

        results = [self._normalize_result(item) for item in results_raw if isinstance(item, dict)]
        extractions = [self._normalize_extraction(item) for item in extractions_raw if isinstance(item, dict)]

        return {
            "results": [r for r in results if r is not None],
            "extractions": [e for e in extractions if e is not None],
        }

    def _extract_json(self, payload: str) -> Dict[str, Any]:
        if not payload:
            raise SearchProviderError("Empty response from search agent")

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", payload, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise SearchProviderError("Unable to parse JSON from search agent response") from exc

        raise SearchProviderError("Search agent response was not valid JSON")

    def _normalize_result(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = str(item.get("title") or item.get("headline") or "").strip()
        url = str(item.get("url") or item.get("link") or "").strip()
        content = str(item.get("content") or item.get("snippet") or "").strip()
        score = item.get("score") or item.get("confidence") or 1.0

        if not (title or url or content):
            return None

        try:
            score_val = float(score)
        except (TypeError, ValueError):
            score_val = 1.0

        return {
            "title": title,
            "url": url,
            "content": content,
            "score": score_val,
        }

    def _normalize_extraction(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = str(item.get("url") or item.get("source_url") or "").strip()
        content = str(item.get("content") or item.get("text") or "").strip()

        if not content:
            return None

        return {
            "url": url,
            "content": content,
        }

