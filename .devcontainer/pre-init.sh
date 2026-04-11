#!/bin/bash
# Runs on the HOST (via devcontainer.json initializeCommand) before the container starts.
# Ensures $HOME/.gitconfig is a regular file, not a directory.
# VS Code Dev Containers streams ~/.gitconfig into the container; if it is a
# directory the RPC stream fails with "unexpected end of parent stream".

set -euo pipefail

gcfg="$HOME/.gitconfig"
if [ -d "$gcfg" ]; then
    rm -rf "$gcfg"
    touch "$gcfg"
fi
