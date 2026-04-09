FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get install -y postgresql-client

# Install Node.js 20 (provides node, npm, npx — required for MCP servers)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs
