FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN rm -f /etc/apt/sources.list.d/yarn.list

RUN id -u vscode >/dev/null 2>&1 || useradd -m -s /bin/bash vscode

USER vscode
