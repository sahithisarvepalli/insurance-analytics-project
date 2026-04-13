FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN rm -f /etc/apt/sources.list.d/yarn.list

RUN if ! id -u vscode >/dev/null 2>&1; then \
        getent group 1000 >/dev/null 2>&1 || groupadd --gid 1000 vscode; \
        if getent passwd 1000 >/dev/null 2>&1; then \
            useradd -m --gid 1000 --shell /bin/bash vscode; \
        else \
            useradd -m --uid 1000 --gid 1000 --shell /bin/bash vscode; \
        fi; \
    fi

USER vscode
