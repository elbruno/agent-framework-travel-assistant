# 🐳 Running the Travel Assistant in a DevContainer

This guide explains how to run the AI Travel Concierge application using DevContainers, either locally with Docker or in GitHub Codespaces.

## 📋 Table of Contents

- [What is a DevContainer?](#what-is-a-devcontainer)
- [Prerequisites](#prerequisites)
- [Option 1: GitHub Codespaces (Easiest)](#option-1-github-codespaces-easiest)
- [Option 2: Local Docker with VS Code](#option-2-local-docker-with-vs-code)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)

---

## What is a DevContainer?

A Development Container (DevContainer) is a fully configured development environment running in a Docker container. It includes:

- ✅ Python 3.11 runtime
- ✅ Redis 8.0.3 database
- ✅ All Python dependencies pre-installed with `uv`
- ✅ VS Code extensions for Python development
- ✅ Consistent environment across all machines

---

## Prerequisites

### For GitHub Codespaces

- GitHub account (free tier includes 60 hours/month of Codespaces)
- Required API keys (see [Configuration](#configuration))

### For Local Development

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- [Visual Studio Code](https://code.visualstudio.com/) installed
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed
- Required API keys (see [Configuration](#configuration))

---

## Option 1: GitHub Codespaces (Easiest)

GitHub Codespaces provides a cloud-based development environment with zero local setup.

### Steps

1. **Open in Codespaces**
   - Navigate to the repository on GitHub
   - Click the green **Code** button
   - Select the **Codespaces** tab
   - Click **Create codespace on main**

2. **Wait for Setup**
   - Codespaces will automatically:
     - Build the DevContainer
     - Install all dependencies
     - Start Redis
     - Create `.env` from `.env.example`
   - This takes 2-3 minutes on first run

3. **Configure API Keys**
   - Open the `.env` file in the editor
   - Add your required API keys:

     ```bash
     OPENAI_API_KEY=sk-your-actual-key-here
     TAVILY_API_KEY=your-actual-key-here
     ```

4. **Run the Application**

   ```bash
   make start
   ```

5. **Access the App**
   - VS Code will show a notification: "Your application running on port 7860 is available"
   - Click **Open in Browser** or go to the **Ports** tab and click the forwarded URL

---

## Option 2: Local Docker with VS Code

Run the DevContainer on your local machine using Docker Desktop.

### Steps

1. **Start Docker Desktop**
   - Ensure Docker Desktop is running
   - Verify with: `docker --version`

2. **Clone the Repository**

   ```bash
   git clone https://github.com/elbruno/agent-framework-travel-assistant.git
   cd agent-framework-travel-assistant
   ```

3. **Open in VS Code**

   ```bash
   code .
   ```

4. **Reopen in Container**
   - VS Code will detect the `.devcontainer` folder
   - Click **Reopen in Container** when prompted
   - Or press `F1` → type **Dev Containers: Reopen in Container**

5. **Wait for Setup**
   - First build takes 3-5 minutes
   - Subsequent starts are much faster (cached)
   - Watch the build progress in the VS Code terminal

6. **Configure API Keys**
   - Open the `.env` file
   - Add your actual API keys:

     ```bash
     OPENAI_API_KEY=sk-your-actual-key-here
     TAVILY_API_KEY=your-actual-key-here
     ```

7. **Run the Application**

   ```bash
   make start
   ```

8. **Access the App**
   - Open your browser to: `http://localhost:7860`
   - The app will also be accessible via the **Ports** tab in VS Code

---

## Configuration

### Required Environment Variables

Edit the `.env` file and set these required values:

```bash
# REQUIRED: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# REQUIRED: Get from https://tavily.com
TAVILY_API_KEY=your-tavily-api-key-here
```

### Optional Configuration

The following have sensible defaults but can be customized:

```bash
# Memory Configuration
MEM0_CLOUD=false                              # Use local Mem0 (default) or Mem0 Cloud
# MEM0_API_KEY=your-mem0-key                  # Only needed if MEM0_CLOUD=true

# Model Selection
TRAVEL_AGENT_MODEL=gpt-4o-mini                # Main agent model
MEM0_MODEL=gpt-4o-mini                        # Memory model
MEM0_EMBEDDING_MODEL=text-embedding-3-small   # Embeddings model

# Redis (auto-configured in DevContainer)
REDIS_URL=redis://localhost:6379

# Server Settings
SERVER_NAME=0.0.0.0
SERVER_PORT=7860
SHARE=false                                   # Set to 'true' for public Gradio link

# Application Limits
MAX_CHAT_HISTORY_SIZE=40
MAX_SEARCH_RESULTS=5
```

### Using Azure Managed Redis

If you want to use Azure Managed Redis instead of the local Redis container:

```bash
REDIS_URL=redis://<your-endpoint>:6379?ssl=true&password=<your-password>
```

---

## Running the Application

### Start the App

```bash
make start
```

Or manually:

```bash
uv run python gradio_app.py
```

### Access the UI

- **Local Docker**: <http://localhost:7860>
- **Codespaces**: Use the forwarded port URL (VS Code will show a notification)

### Clear Redis Data

To reset all chat history and stored data:

```bash
make redis-clear
```

### Stop the App

Press `Ctrl+C` in the terminal where the app is running.

---

## What's Included in the DevContainer?

### Services

- **Python App Container**
  - Python 3.11
  - `uv` package manager (fast dependency resolution)
  - All dependencies from `pyproject.toml`
  - Development tools and VS Code extensions

- **Redis Container**
  - Redis 8.0.3 Alpine
  - Persistent data volume
  - Accessible at `redis://localhost:6379`

### VS Code Extensions

Pre-installed for enhanced Python development:

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast type checking
- `charliermarsh.ruff` - Fast Python linter
- `rangav.vscode-thunder-client` - API testing
- `redhat.vscode-yaml` - YAML editing
- `github.copilot` - AI pair programming

### Port Forwarding

| Port | Service | Auto-Forward |
|------|---------|--------------|
| 6379 | Redis   | Silent       |
| 7860 | Gradio  | Notify       |

---

## Troubleshooting

### Issue: Container won't start

**Solution:**

- Ensure Docker Desktop is running
- Check Docker logs: `docker ps -a`
- Rebuild the container: `F1` → **Dev Containers: Rebuild Container**

### Issue: Redis connection failed

**Solution:**

- Verify Redis is running: `redis-cli -u redis://localhost:6379 ping`
- Should return: `PONG`
- Check the REDIS_URL in `.env` matches the container network

### Issue: Port 7860 already in use

**Solution:**

```bash
# Find what's using the port
lsof -i :7860   # macOS/Linux
netstat -ano | findstr :7860   # Windows

# Kill the process or change SERVER_PORT in .env
```

### Issue: Dependencies not installed

**Solution:**

```bash
# Manually sync dependencies
uv sync

# Or rebuild the container
# F1 → Dev Containers: Rebuild Container
```

### Issue: API keys not working

**Solution:**

- Verify keys are correct in `.env`
- Ensure no extra spaces or quotes
- OpenAI key must start with `sk-`
- Restart the application after changing `.env`

### Issue: Gradio UI not accessible

**Solution:**

- Check the terminal for the actual URL (sometimes differs from localhost)
- In Codespaces, use the **Ports** tab to get the forwarded URL
- Verify `SERVER_NAME=0.0.0.0` in `.env`

### Issue: Changes to code not reflected

**Solution:**

- Stop the app (`Ctrl+C`)
- Restart with `make start`
- For dependency changes, run `uv sync` first

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         DevContainer Environment         │
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────┐   ┌──────────────┐  │
│  │   Python App   │   │    Redis     │  │
│  │   Container    │──▶│  Container   │  │
│  │                │   │              │  │
│  │  • agent.py    │   │  • Port 6379 │  │
│  │  • gradio_app  │   │  • Vector DB │  │
│  │  • Port 7860   │   │  • Chat hist │  │
│  └────────────────┘   └──────────────┘  │
│                                          │
└─────────────────────────────────────────┘
            │
            ▼
    Your Browser / VS Code
```

---

## Additional Resources

- [Original README](README.md) - Application features and usage
- [Main Documentation](how-it-works.md) - Architecture details
- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)

---

## Quick Reference

### Essential Commands

```bash
# Start the app
make start

# Clear all Redis data
make redis-clear

# Clean Python cache
make clean

# Test Redis connection
redis-cli -u redis://localhost:6379 ping

# View Redis keys
redis-cli -u redis://localhost:6379 keys '*'

# Install/sync dependencies
uv sync

# Run with custom environment
uv run python gradio_app.py
```

### File Locations

| Path | Purpose |
|------|---------|
| `.devcontainer/` | DevContainer configuration |
| `.env` | Your API keys (git-ignored) |
| `.env.example` | Environment template |
| `assets/calendars/` | Generated .ics files |
| `context/seed.json` | Seed users and memories |

---

**Ready to travel? 🌍✈️**

Start the app and begin planning your next adventure with AI assistance!
