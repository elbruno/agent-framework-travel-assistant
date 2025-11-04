#!/bin/bash
set -e

echo "🔧 Running post-create setup..."

# Ensure we're in the workspace directory
cd /workspace

# Install Homebrew if needed
BREW_PREFIX="/home/linuxbrew/.linuxbrew"
BREW_BIN="$BREW_PREFIX/bin/brew"

if ! command -v brew >/dev/null 2>&1; then
    echo "🍺 Homebrew not found, installing..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Ensure shell environments initialize brew
    BREW_INIT='eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"'
    for profile in /home/vscode/.bashrc /home/vscode/.zshrc /home/vscode/.profile; do
        touch "$profile"
        if ! grep -qs "$BREW_INIT" "$profile"; then
            echo "$BREW_INIT" >> "$profile"
        fi
    done
else
    echo "🍺 Homebrew already installed"
fi

if [ -x "$BREW_BIN" ]; then
    eval "$("$BREW_BIN" shellenv)"
else
    echo "⚠️  Homebrew binary not found at $BREW_BIN"
fi

echo "🍺 Installing Homebrew dependencies..."
brew_deps=(uv redis)
for pkg in "${brew_deps[@]}"; do
    if brew list "$pkg" >/dev/null 2>&1; then
        echo "   • $pkg already installed"
    else
        brew install "$pkg"
    fi
done

# Install/sync dependencies with uv
echo "📦 Installing Python dependencies with uv..."
if [ -f "pyproject.toml" ]; then
    # Use copy mode to avoid hardlinking issues with Docker volumes
    export UV_LINK_MODE=copy
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
