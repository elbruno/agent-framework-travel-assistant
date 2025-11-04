
# 🌍 AI Travel Concierge (Agent Framework + Redis + Mem0)

A travel planning assistant with dual-layer memory: Redis-backed chat history and Mem0-powered long‑term memory. It provides time‑aware research via Tavily or Azure AI Foundry Search Agent, uses OpenAI models for planning, and can export finalized itineraries to an ICS calendar file, all wrapped in a polished Gradio UI with per‑user contexts.

## 🧠 Key features
- **Dual-layer memory**: Short‑term chat history in Redis; long‑term preferences via Mem0 (OpenAI or Azure OpenAI LLM + embeddings)
- **Per‑user isolation**: Separate memory contexts and chat history for each user
- **Time‑aware search**: Pluggable provider (Tavily or Azure AI Foundry Search Agent) for logistics and destination research
- **Calendar export (ICS)**: Generate calendar files for itineraries and open the folder via UI
- **Gradio UI**: Chat, user tabs, live agent event logs, clear‑chat control
- **Configurable**: Pydantic settings via environment variables, `.env` support

## 🧩 Architecture overview
- `gradio_app.py`: Launches the Gradio app, builds UI, wires event streaming, calendar open, and user switching
- `agent.py`: Implements `TravelAgent` using Agent Framework
  - Tools: `search_logistics`, `search_general`, `generate_calendar_ics`
  - Mem0 long‑term memory per user; Redis chat message store for short‑term context
  - Pluggable search provider (Tavily or Azure AI Foundry Search Agent) for fresh web info; ICS generation via `ics`
- `config.py`: Pydantic settings and dependency checks
- `context/seed.json`: Seeded users and initial long‑term memory entries
- `assets/styles.css`: Custom theme and styling

A diagram of a software company:



## ✅ Prerequisites
- Python >=3.11 
- Redis instance (local Docker, Redis Cloud, or Azure Managed Redis)
- API keys: OpenAI + Tavily (default) **or** Azure OpenAI + Azure AI Foundry Search Agent, plus Mem0

## 🔐 Required environment variables
Provide values via your shell environment or `.env`. Begin by selecting providers, then supply the keys for that provider.

- `LLM_PROVIDER` – `openai` (default) or `azure_openai`
- `SEARCH_PROVIDER` – `tavily` (default) or `azure_foundry_agent`

### When `LLM_PROVIDER=openai`
- `OPENAI_API_KEY` (must start with `sk-`; validated)

### When `LLM_PROVIDER=azure_openai`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT` (e.g., `https://my-resource.openai.azure.com`)
- `AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME` (deployment powering the agent)
- Optional overrides: `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME`, `AZURE_OPENAI_MEM0_LLM_DEPLOYMENT_NAME`

### Search providers
- `TAVILY_API_KEY` when `SEARCH_PROVIDER=tavily`
- When `SEARCH_PROVIDER=azure_foundry_agent`:
  - `AZURE_FOUNDRY_ENDPOINT` – Azure AI Foundry project endpoint URL (e.g., `https://<resource>.services.ai.azure.com/api/projects/<project>`)
  - `AZURE_FOUNDRY_SEARCH_AGENT_ID` – Search agent ID (e.g., `asst_xxxxx`)
  - Authentication uses `DefaultAzureCredential` (supports Azure CLI, Managed Identity, environment variables, and more)

### Mem0
- `MEM0_CLOUD` (default `false`). When `true`, set `MEM0_API_KEY` for Mem0 Cloud. Otherwise Redis-backed Mem0 is used.

### Recommended overrides (defaults shown)
- `TRAVEL_AGENT_MODEL` = `gpt-4o-mini`
- `MEM0_MODEL` = `gpt-4o-mini`
- `MEM0_EMBEDDING_MODEL` = `text-embedding-3-small`
- `MEM0_EMBEDDING_MODEL_DIMS` = `1536`
- `REDIS_URL` = `redis://localhost:6379`
- `MAX_CHAT_HISTORY_SIZE` = `40`
- `MAX_SEARCH_RESULTS` = `5`
- `SERVER_NAME` = `0.0.0.0`
- `SERVER_PORT` = `7860`
- `SHARE` = `false`

Example `.env` (OpenAI + Tavily):
```env
LLM_PROVIDER=openai
SEARCH_PROVIDER=tavily
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=...
MEM0_CLOUD=false
# MEM0_API_KEY=...
REDIS_URL=redis://localhost:6379
TRAVEL_AGENT_MODEL=gpt-4o-mini
MEM0_MODEL=gpt-4o-mini
MEM0_EMBEDDING_MODEL=text-embedding-3-small
MEM0_EMBEDDING_MODEL_DIMS=1536
MAX_CHAT_HISTORY_SIZE=40
MAX_SEARCH_RESULTS=5
SERVER_NAME=0.0.0.0
SERVER_PORT=7860
SHARE=false
```

Example `.env` (Azure OpenAI + Azure AI Foundry Search Agent):
```env
LLM_PROVIDER=azure_openai
SEARCH_PROVIDER=azure_foundry_agent
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=travel-agent
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME=mem0-embeddings
AZURE_OPENAI_MEM0_LLM_DEPLOYMENT_NAME=mem0-llm
# Azure AI Foundry - uses DefaultAzureCredential for authentication
AZURE_FOUNDRY_ENDPOINT=https://bruno-realtime-resource.services.ai.azure.com/api/projects/bruno-realtime
AZURE_FOUNDRY_SEARCH_AGENT_ID=asst_GRyvwZvi8SrAiZKVQbhQaqNM
MEM0_CLOUD=false
REDIS_URL=redis://localhost:6379
TRAVEL_AGENT_MODEL=travel-agent
MEM0_MODEL=mem0-llm
MEM0_EMBEDDING_MODEL=mem0-embeddings
MEM0_EMBEDDING_MODEL_DIMS=1536
```

### 🧠 Mem0 modes
- **Local (default)**: `MEM0_CLOUD=false`
  - Uses Redis as the vector store defined by `REDIS_URL`
  - Embeddings and LLM calls use OpenAI keys or Azure deployments based on `LLM_PROVIDER`
- **Cloud**: `MEM0_CLOUD=true`
  - Uses Mem0 Cloud. You must set `MEM0_API_KEY`
  - No Redis vector store is used for long‑term memory (Redis is still used for chat history)

### 🔍 Azure AI Foundry Search Agent Setup
When using `SEARCH_PROVIDER=azure_foundry_agent`, the application connects to an existing Azure AI Foundry agent using the Microsoft Agent Framework SDK:

1. **Create an Azure AI Foundry project** in the Azure portal
2. **Deploy a search agent** with appropriate search capabilities
3. **Note your project endpoint and agent ID**:
   - Project endpoint format: `https://<resource>.services.ai.azure.com/api/projects/<project-name>`
   - Agent ID format: `asst_xxxxx`
4. **Set up authentication** using one of the supported methods:
   - Azure CLI: Run `az login` before starting the application
   - Managed Identity: When deployed to Azure (App Service, Container Apps, etc.)
   - Environment variables: Set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`
   - Other methods supported by `DefaultAzureCredential`

For more details, see the [Agent Framework documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python).

The application communicates with the agent through the Agent Framework SDK, which handles authentication, message formatting, and response parsing automatically.

## 🗄️ Redis setup options
- Azure Managed Redis: This is an easy way to get a fully managed service that runs natively on Azure. You will require an Azure subscription to get started. Achieve unmatched performance with costs as low as USD 12 per month. Alternative methods for deploying Redis are outlined below. See quickstart guide through Azure portal: https://learn.microsoft.com/en-us/azure/redis/quickstart-create-managed-redis

  Note: Enable access key-based authentication on your cache if you want to run the agent locally. Note the endpoint URL and the password; this will be used later.
  
- Local (Docker):
```bash
docker run --name redis -p 6379:6379 -d redis:8.0.3
```
- Redis Cloud: create a free database and set `REDIS_URL`

To clear all app data in Redis (chat history, summaries):
```bash
make redis-clear
```

## ▶️ Install & run (uv)
This project uses `uv` for environment and dependency management.

1. **Install prerequisites**

  ```bash
  brew install uv redis
  # Optional: start a local Redis service when you're not using Docker/managed Redis
  brew services start redis
  ```

  > The devcontainer runs these Homebrew commands automatically the first time it starts.

2. **Sync Python dependencies**

  ```bash
  uv sync
  ```

3. **Create your environment file**

  ```bash
  cp -n .env.example .env 2>/dev/null || true
  # then edit .env and add your API keys
  ```

4. **Launch the app**

  ```bash
  uv run --env-file .env gradio_app.py
  ```

  The UI will be available at `http://localhost:7860`. You can also use `make start` if you export the same environment variables in your shell.

## 👤 Seed users and memory
- Users are defined in `context/seed.json` under `user_memories`
- On first run, each user's long‑term memory is seeded via Mem0
- The default selected user is the first key in `seed.json`
- Switch users via the tabs at the top of the UI

Example `context/seed.json`:
```json
{
  "user_memories": {
    "Alice": [ { "insight": "Prefers boutique hotels and walkable neighborhoods" } ],
    "Bob": [ { "insight": "Loves food tours and early morning flights" } ]
  }
}
```

## 💬 Using the app
- Ask for trip ideas, date‑bound logistics, or destination research
- The agent will call tools as needed:
  - `search_logistics(query, start_date?, end_date?)` for flights/hotels/transport
  - `search_general(query)` for activities, neighborhoods, dining, events
  - `generate_calendar_ics(...)` once your itinerary is finalized to produce an `.ics` file
- The right panel shows live agent events and tool logs
- Use “Clear Chat” to wipe the current user’s short‑term history from Redis

## 📅 Calendar export
- When an itinerary is finalized, the agent can export an `.ics` file
- Click “Open Calendar” to open the per‑user calendars folder in your OS file explorer
- Files are stored under `assets/calendars/<USER_ID>/`

## Recommended user flow

Try the following query flow to see the agent in action:

### Blank User (Mark) - No preferences (cold start case)
1. I like bears and the places where bears can be found. 
2. I think Christmas is quite a magical time of year and I enjoy visiting winter wonderland villages
3. What's a place to visit that I might like?
4. Can you give me a solid 3 day itinerary based on online recommendations? For what to do in (Pick one of the locations it mentions) 
5. Okay, can you recommend a flight and hotel? I live in (Pick a location) and I'm going to leave on 22nd December and will return 26th December. 
6. Give me the calendar. 

### Pre-filled User (Shreya) - User preferences known at startup
1. I'm planning to hit up Redis Released in London this year. Can you find more info about it?

## 🐛 Troubleshooting
- Missing API keys: app exits with a configuration error and hints for `.env`
- OpenAI key must start with `sk-` (validated in `config.py`)
- Redis connection errors: verify `REDIS_URL` and that Redis is reachable
- Mem0 errors when seeding: check `MEM0_API_KEY` and OpenAI settings
- Browser doesn’t open: navigate to `http://localhost:7860` manually

---

Built with Redis, Agent Framework, OpenAI, and Tavily. Enjoy!

