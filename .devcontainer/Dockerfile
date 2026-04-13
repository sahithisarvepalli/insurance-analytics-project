FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN getent passwd vscode >/dev/null || { echo "Error: vscode user not found"; exit 1; }

RUN rm -f /etc/apt/sources.list.d/yarn.list

USER vscode
