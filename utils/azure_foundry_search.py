"""Azure AI Foundry search agent client wrapper using Agent Framework SDK.

This module provides a client for delegating search queries to an Azure AI Foundry
managed agent that performs web searches and content extraction using the
Microsoft Agent Framework SDK.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from agent_framework.azure import AzureAIFoundryAgent
from azure.identity import DefaultAzureCredential


class SearchProviderError(Exception):
    """Exception raised when the search provider encounters an error."""
    pass


class AzureFoundrySearchClient:
    """Client wrapper for Azure AI Foundry search agent using Agent Framework SDK.
    
    This client delegates search queries to a managed Azure AI Foundry agent
    using the Microsoft Agent Framework SDK for authentication and communication.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        agent_id: str,
    ) -> None:
        """Initialize the Azure Foundry search client.
        
        Uses DefaultAzureCredential for authentication, which supports:
        - Azure CLI authentication
        - Managed Identity
        - Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
        - Visual Studio Code authentication
        - And more...
        
        Args:
            endpoint: Azure AI Foundry project endpoint URL 
                     (e.g., https://<resource>.services.ai.azure.com/api/projects/<project>)
            agent_id: ID of the search agent deployment (e.g., asst_xxxxx)
        
        Raises:
            ValueError: If required parameters are missing
        """
        if not endpoint:
            raise ValueError("Azure AI Foundry endpoint is required")
        if not agent_id:
            raise ValueError("Azure AI Foundry agent ID is required")
        
        self.endpoint = endpoint.rstrip("/")
        self.agent_id = agent_id
        
        # Initialize Azure credential for authentication
        self.credential = DefaultAzureCredential()
        
        # Initialize the Azure AI Foundry Agent client
        try:
            self.agent_client = AzureAIFoundryAgent(
                endpoint=self.endpoint,
                agent_id=self.agent_id,
                credential=self.credential,
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Azure AI Foundry agent: {e}")

    def search(
        self,
        *,
        query: str,
        count: int = 10,
        include_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute a search via the Azure AI Foundry search agent using the SDK.
        
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
        try:
            # Build the search query message
            search_query = query
            if include_domains:
                domain_filter = " OR ".join(f"site:{domain}" for domain in include_domains)
                search_query = f"{query} ({domain_filter})"
            
            # Create the message to send to the agent
            user_message = f"Search for: {search_query}. Return up to {count} results."
            
            # Run the agent with the search query
            response = self.agent_client.run(
                messages=[{"role": "user", "content": user_message}]
            )
            
            # Parse and validate response
            return self._parse_response(response)
            
        except Exception as e:
            raise SearchProviderError(f"Azure AI Foundry search error: {str(e)}")

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

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse and validate the Azure AI Foundry agent response.
        
        The Agent Framework SDK returns structured responses from the agent.
        We need to extract search results and content from the agent's response.
        
        Args:
            response: Response object from agent_client.run()
        
        Returns:
            Dictionary with normalized results and extractions
        
        Raises:
            SearchProviderError: If response format is invalid
        """
        try:
            results = []
            extractions = []
            
            # The agent response may contain messages
            if hasattr(response, 'messages'):
                for message in response.messages:
                    if hasattr(message, 'content') and message.content:
                        content_str = message.content
                        
                        # Try to parse JSON content from the agent response
                        try:
                            content_data = json.loads(content_str) if isinstance(content_str, str) else content_str
                            
                            # Extract results if present
                            if isinstance(content_data, dict):
                                raw_results = content_data.get("results", [])
                                for item in raw_results:
                                    results.append({
                                        "title": item.get("title", ""),
                                        "url": item.get("url", ""),
                                        "content": item.get("snippet", item.get("content", "")),
                                        "score": item.get("score", 1.0),
                                    })
                                
                                # Extract content extractions if present
                                raw_extractions = content_data.get("extractions", [])
                                for item in raw_extractions:
                                    extractions.append({
                                        "url": item.get("url", ""),
                                        "content": item.get("content", ""),
                                    })
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, treat as plain text result
                            results.append({
                                "title": "Search Result",
                                "url": "",
                                "content": content_str[:500] if isinstance(content_str, str) else str(content_str)[:500],
                                "score": 1.0,
                            })
            
            # If no results extracted yet, try alternative response formats
            if not results and hasattr(response, 'content'):
                content = response.content
                if isinstance(content, str):
                    results.append({
                        "title": "Search Result",
                        "url": "",
                        "content": content[:500],
                        "score": 1.0,
                    })
            
            return {
                "results": results,
                "extractions": extractions,
            }

        except Exception as e:
            raise SearchProviderError(f"Failed to parse agent response: {e}")
