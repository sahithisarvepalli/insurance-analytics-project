FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get install -y postgresql-client

# Pre-install Python dependencies so CI jobs using this image skip reinstalling
# packages on every run.  The image is rebuilt automatically whenever
# requirements.txt or pyproject.toml changes (see build-devcontainer.yml).
COPY requirements.txt pyproject.toml ./
# Install runtime deps; editable install needs the source tree which is
# checked out at runtime, so we install deps only here.
RUN pip install --no-cache-dir -r requirements.txt
