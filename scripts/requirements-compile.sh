#!/bin/bash
set -e

# Install pip-tools if not present
python3 -m pip install pip-tools

# Compile requirements
echo "Compiling requirements.in..."
python3 -m piptools compile requirements.in

echo "Compiling requirements-dev.in..."
python3 -m piptools compile requirements-dev.in

echo "Done."
