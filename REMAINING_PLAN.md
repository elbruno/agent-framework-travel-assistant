# Continuation Plan for Azure AI Foundry Integration

## 1. Update Search Strategy
- **Remove Azure Bing wiring** from `config.py`, `agent.py`, and `.env.example`.
- **Introduce an Azure AI Foundry "search agent" client wrapper** (e.g., `utils/azure_foundry_search.py`) that delegates search queries to the managed agent.
- **Extend configuration** with the parameters that agent requires (deployment name, endpoint, keys, etc.).
- **Refactor `_perform_search`** to call the new Foundry agent instead of Tavily when `SEARCH_PROVIDER=azure_foundry_agent`.
- Ensure the search response shape (results + extractions) matches current expectations.

### Foundry Search Agent Contract
- **Invocation**: POST to Azure AI Foundry inference endpoint with payload
	```json
	{
		"agent_id": "<SEARCH_AGENT_ID>",
		"input": {
			"query": "<search query>",
			"includeDomains": ["domain1.com", "domain2.com"],
			"maxResults": <int>
		}
	}
	```
- **Expected response schema**:
	```json
	{
		"outputs": [
			{
				"role": "assistant",
				"content": {
					"results": [
						{
							"title": "<string>",
							"url": "<string>",
							"snippet": "<string>",
							"score": <float>
						}
					],
					"extractions": [
						{
							"url": "<string>",
							"content": "<string>"
						}
					]
				}
			}
		]
	}
	```
- **Error handling**: Non-200 status or missing fields should raise a `SearchProviderError` and emit a UI log entry.
- **Timeout/retry** defaults: 20s timeout, retry up to 2 times with exponential backoff (e.g., 1s, 3s).

### Agent instructions (to deliver to Azure AI Foundry)
- System prompt:
	> "You are the Travel Concierge Search Agent. Given a query, optional domain filters and a max result limit, return fresh web results and concise extractions suitable for travel planning. You MUST search the live web and include recent information (within the past 24 months when possible). Provide neutral, factual snippets."
- Output format: ensure the response fits the JSON schema above.
- For domain restrictions, respect `includeDomains` by prioritizing those sources before falling back to broader web results.
- Limit extractions to the top 2 URLs, keeping each snippet under 2000 characters.

## 2. Align Provider Defaults & Validation
- Update `AppConfig` to replace `azure_bing` with the new provider option and validate the required settings (key, endpoint, agent ID, etc.).
- Adjust `validate_dependencies()` to perform a lightweight health check against the Foundry search agent, handling timeouts gracefully.

## 3. Refresh Environment Templates & Docs
- Modify `.env.example` and README sections to document the new search agent variables.
- Clarify that Tavily is optional and Azure users should deploy the Foundry agent for search.
- Add short guidance on provisioning the Azure AI Foundry agent and granting search capabilities.

## 4. Update UI Copy & Logging
- Replace any “Azure Bing” phrasing in `gradio_app.py`/README with "Azure AI Foundry Search Agent".
- Double-check `emit_ui_event` messaging so users see accurate provider names in tool logs.

## 5. QA & Testing
- Run `uv run python -m compileall ...` after each major edit.
- Execute any available unit/system tests (or create smoke tests) to verify both OpenAI+Tavily and Azure Foundry configurations.
- Perform a manual chat run (if feasible) hitting the new search path to confirm response formatting.

## 6. Stretch / Nice-to-haves
- Add retry/backoff logic around Foundry agent calls to handle transient Azure errors.
- Instrument telemetry (if available) to measure search latency per provider.
- Consider caching search responses for short intervals to minimize Foundry usage costs.
