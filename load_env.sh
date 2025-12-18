#!/bin/bash

# Auto-load environment variables for Script Ohio 2.0
# This script loads the .env file when you're in the project directory

SCRIPT_OHIO_DIR="/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"
ENV_FILE="$SCRIPT_OHIO_DIR/.env"

if [[ "$PWD" == "$SCRIPT_OHIO_DIR"* ]] && [[ -f "$ENV_FILE" ]]; then
    # Load .env file if not already loaded
    if [[ -z "$CFBD_API_KEY_LOADED" ]]; then
        set -a
        source "$ENV_FILE"
        set +a
        export CFBD_API_KEY_LOADED=1
        echo "🏈 Script Ohio 2.0 environment loaded"
    fi
fi