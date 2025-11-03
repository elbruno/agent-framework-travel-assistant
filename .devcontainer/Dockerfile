FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    redis-tools \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management system-wide
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.cargo/bin/uv /usr/local/bin/uv \
    && mv /root/.cargo/bin/uvx /usr/local/bin/uvx

# Set working directory
WORKDIR /workspace

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Create virtual environment and install dependencies
# This layer will be cached if pyproject.toml doesn't change
RUN uv venv .venv \
    && . .venv/bin/activate \
    && uv pip install --prerelease=allow -e .

# Default to bash shell
SHELL ["/bin/bash", "-c"]
