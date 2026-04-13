FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN getent passwd vscode >/dev/null

RUN rm -f /etc/apt/sources.list.d/yarn.list

USER vscode
