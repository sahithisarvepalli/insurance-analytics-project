#!/usr/bin/env bash

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
    exit 0
fi

if docker image inspect mcp/sonarqube:1.10.21 >/dev/null 2>&1; then
    exit 0
fi

docker build -t mcp/sonarqube:1.10.21 -f .devcontainer/sonarqube-mcp.Dockerfile .
