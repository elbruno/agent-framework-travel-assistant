"""Azure AI Foundry search agent client wrapper.

This module provides a client for delegating search queries to an Azure AI Foundry
managed agent that performs web searches and content extraction.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union

import httpx


class SearchProviderError(Exception):
    """Exception raised when the search provider encounters an error."""
    pass


class AzureFoundrySearchClient:
    """Client wrapper for Azure AI Foundry search agent.
    
    This client delegates search queries to a managed Azure AI Foundry agent
    that performs live web searches and returns structured results with extractions.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        agent_id: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
    ) -> None:
        """Initialize the Azure Foundry search client.
        
        Args:
            endpoint: Azure AI Foundry inference endpoint URL
            api_key: API key for authentication
            agent_id: ID of the search agent deployment
            timeout_seconds: Request timeout in seconds (default: 20.0)
            max_retries: Maximum number of retry attempts (default: 2)
        
        Raises:
            ValueError: If required parameters are missing
        """
        if not endpoint:
            raise ValueError("Azure AI Foundry endpoint is required")
        if not api_key:
            raise ValueError("Azure AI Foundry API key is required")
        if not agent_id:
            raise ValueError("Azure AI Foundry agent ID is required")
        
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def search(
        self,
        *,
        query: str,
        count: int = 10,
        include_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute a search via the Azure AI Foundry search agent.
        
        Args:
            query: Search query string
            count: Maximum number of results to return (default: 10)
            include_domains: Optional list of domains to prioritize
        
        Returns:
            Dictionary containing:
                - results: List of search results with title, url, content, score
                - extractions: List of extracted content from top URLs
        
        Raises:
            SearchProviderError: If the search fails or returns invalid data
        """
        payload = {
            "agent_id": self.agent_id,
            "input": {
                "query": query,
                "maxResults": count,
            }
        }
        
        # Add domain filters if provided
        if include_domains:
            payload["input"]["includeDomains"] = include_domains

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(
                        self.endpoint,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()

                # Parse and validate response
                return self._parse_response(data)

            except httpx.HTTPStatusError as e:
                last_exception = SearchProviderError(
                    f"Azure AI Foundry search failed with status {e.response.status_code}: {e.response.text}"
                )
            except httpx.TimeoutException as e:
                last_exception = SearchProviderError(
                    f"Azure AI Foundry search timed out after {self.timeout_seconds}s"
                )
            except Exception as e:
                last_exception = SearchProviderError(
                    f"Azure AI Foundry search error: {str(e)}"
                )

            # Exponential backoff: 1s for first retry, 3s for second retry
            if attempt < self.max_retries:
                backoff_time = 1 if attempt == 0 else 3
                time.sleep(backoff_time)

        # All retries exhausted
        raise last_exception

    def extract(
        self,
        urls: List[str],
        *,
        max_chars: int = 2000,
    ) -> List[Dict[str, str]]:
        """Extract content from URLs.
        
        Note: For Azure AI Foundry, extractions are included in the search response.
        This method is provided for API compatibility with other search providers,
        but returns an empty list since the Foundry search agent provides extractions
        directly in the search() response.
        
        Args:
            urls: List of URLs to extract content from (ignored)
            max_chars: Maximum characters per extraction (ignored)
        
        Returns:
            Empty list (extractions are provided by the search agent in the search response)
        """
        # Extractions are already provided by the Foundry search agent
        # in the search response, so this method returns empty list.
        # The agent.py module uses extractions directly from the search response.
        return []

    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate the Azure AI Foundry response.
        
        Args:
            data: Raw response data from the API
        
        Returns:
            Dictionary with normalized results and extractions
        
        Raises:
            SearchProviderError: If response format is invalid
        """
        try:
            outputs = data.get("outputs", [])
            if not outputs:
                raise SearchProviderError("No outputs in Azure AI Foundry response")

            first_output = outputs[0]
            content = first_output.get("content", {})
            
            if not isinstance(content, dict):
                raise SearchProviderError("Invalid content format in response")

            # Extract results
            raw_results = content.get("results", [])
            results = []
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("snippet", ""),
                    "score": item.get("score", 1.0),
                })

            # Extract content extractions
            extractions = []
            raw_extractions = content.get("extractions", [])
            for item in raw_extractions:
                extractions.append({
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                })

            return {
                "results": results,
                "extractions": extractions,
            }

        except KeyError as e:
            raise SearchProviderError(f"Missing required field in response: {e}")
        except Exception as e:
            raise SearchProviderError(f"Failed to parse response: {e}")
