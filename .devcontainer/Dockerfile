FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get install -y postgresql-client

# Pre-install Python dependencies so CI jobs using this image skip reinstalling
# packages on every run.  The image is rebuilt automatically whenever
# requirements.txt or pyproject.toml changes (see build-devcontainer.yml).
COPY requirements.txt pyproject.toml ./
# Install runtime deps; editable install needs the source tree which is
# checked out at runtime, so we install deps only here.
# --force-reinstall ensures our pinned versions overwrite any tools that the
# base devcontainer image pre-installs (e.g. black, pylint, flake8), so the
# CI environment exactly matches the original local dev container.
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt
