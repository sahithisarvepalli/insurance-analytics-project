FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN rm -f /etc/apt/sources.list.d/yarn.list

RUN if ! id -u vscode >/dev/null 2>&1; then \
        existing_group="$(getent group 1000 | cut -d: -f1)"; \
        if [ -z "$existing_group" ]; then \
            groupadd --gid 1000 vscode; \
            existing_group="vscode"; \
        fi; \
        useradd -m --uid 1000 --gid "$existing_group" --shell /bin/bash vscode; \
    fi

USER vscode
