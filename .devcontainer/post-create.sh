#!/bin/bash
set -e

echo "🔧 Running post-create setup..."

# Ensure we're in the workspace directory
cd /workspace

# Install/sync dependencies with uv
echo "📦 Installing Python dependencies with uv..."
if [ -f "pyproject.toml" ]; then
    uv sync --prerelease=allow
    echo "✅ Dependencies installed"
else
    echo "⚠️  pyproject.toml not found, skipping dependency installation"
fi

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️  Please update .env with your API keys!"
    else
        echo "⚠️  No .env.example found. You'll need to create a .env file manually."
    fi
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p assets/calendars
mkdir -p context

# Test Redis connection
echo "🔄 Testing Redis connection..."
if redis-cli -u "${REDIS_URL:-redis://localhost:6379}" ping > /dev/null 2>&1; then
    echo "✅ Redis is accessible"
else
    echo "⚠️  Redis not accessible yet (it may still be starting up)"
fi

echo "✨ Post-create setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Update .env with your API keys (OPENAI_API_KEY, TAVILY_API_KEY)"
echo "   2. Run 'make start' to launch the application"
echo "   3. Open http://localhost:7860 in your browser"
