#!/bin/bash

# CFBD API Key Setup Script for Script Ohio 2.0
# This script sets up your CFBD API key in multiple locations for persistence

echo "🏈 CFBD API Key Setup for Script Ohio 2.0"
echo "=========================================="
echo ""
echo "This script will set up your CFBD API key in multiple places:"
echo "  1. Shell environment (.zshrc)"
echo "  2. Project-specific .env file"
echo "  3. Claude project settings"
echo ""

# Prompt for API key
read -s -p "Enter your CFBD API Key (from https://collegefootballdata.com/dashboard): " API_KEY
echo ""

if [ -z "$API_KEY" ]; then
    echo "❌ No API key provided. Setup cancelled."
    exit 1
fi

# Validate API key format (basic check)
if [[ ! "$API_KEY" =~ ^[a-zA-Z0-9]+$ ]]; then
    echo "⚠️  Warning: API key should be alphanumeric. Please double-check your key."
    read -p "Continue anyway? (y/N): " continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ API key received. Setting up in multiple locations..."
echo ""

# 1. Update .zshrc (replace placeholder or add new)
echo "1. Setting up in ~/.zshrc..."
ZSHRC_FILE="$HOME/.zshrc"

if grep -q "CFBD_API_KEY" "$ZSHRC_FILE"; then
    # Replace existing line
    sed -i '' "s/export CFBD_API_KEY=.*/export CFBD_API_KEY='$API_KEY'/" "$ZSHRC_FILE"
    echo "   ✅ Updated existing CFBD_API_KEY in .zshrc"
else
    # Add new line
    echo "export CFBD_API_KEY='$API_KEY'" >> "$ZSHRC_FILE"
    echo "   ✅ Added new CFBD_API_KEY to .zshrc"
fi

# 2. Create project-specific .env file
echo "2. Creating project .env file..."
PROJECT_DIR="/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"
ENV_FILE="$PROJECT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    # Update existing .env file
    if grep -q "CFBD_API_KEY" "$ENV_FILE"; then
        sed -i '' "s/CFBD_API_KEY=.*/CFBD_API_KEY=$API_KEY/" "$ENV_FILE"
        echo "   ✅ Updated existing CFBD_API_KEY in .env"
    else
        echo "CFBD_API_KEY=$API_KEY" >> "$ENV_FILE"
        echo "   ✅ Added new CFBD_API_KEY to .env"
    fi
else
    # Create new .env file
    cat > "$ENV_FILE" << EOF
# CFBD API Configuration
CFBD_API_KEY=$API_KEY

# Python path for Script Ohio 2.0
PYTHONPATH=$PROJECT_DIR

# Additional environment variables
EOF
    echo "   ✅ Created new .env file with CFBD_API_KEY"
fi

# 3. Create/update Claude project settings (LOCAL-ONLY, gitignored)
echo "3. Setting up Claude project settings (local-only, gitignored)..."
CLAUDE_DIR="/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/.claude"
CLAUDE_SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Ensure .claude directory exists
mkdir -p "$CLAUDE_DIR"

if [ -f "$CLAUDE_SETTINGS_FILE" ]; then
    # Update existing settings.json
    python3 -c "
import json
import sys

with open('$CLAUDE_SETTINGS_FILE', 'r') as f:
    settings = json.load(f)

if 'environment' not in settings:
    settings['environment'] = {}

settings['environment']['CFBD_API_KEY'] = '$API_KEY'

with open('$CLAUDE_SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)

print('   ✅ Updated Claude project settings with CFBD_API_KEY')
"
else
    # Create new settings.json
    cat > "$CLAUDE_SETTINGS_FILE" << EOF
{
  "environment": {
    "CFBD_API_KEY": "$API_KEY"
  }
}
EOF
    echo "   ✅ Created new Claude settings with CFBD_API_KEY"
fi

echo "   ⚠️  SECURITY: .claude/settings.json is gitignored - DO NOT commit this file!"

# 4. Set PYTHONPATH if not already set
echo "4. Ensuring PYTHONPATH is set..."
PROJECT_PATH="/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"
if ! grep -q "PYTHONPATH.*$PROJECT_PATH" "$ZSHRC_FILE"; then
    sed -i '' "s|export PYTHONPATH=.*|export PYTHONPATH='$PROJECT_PATH:\$PYTHONPATH'|" "$ZSHRC_FILE"
    echo "   ✅ Updated PYTHONPATH in .zshrc"
else
    echo "   ✅ PYTHONPATH already set correctly"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your CFBD API key has been set up in:"
echo "  ✅ ~/.zshrc (shell environment)"
echo "  ✅ ./.env (project environment, gitignored)"
echo "  ✅ ./.claude/settings.json (Claude project settings, gitignored)"
echo ""
echo "⚠️  SECURITY REMINDER:"
echo "   - .env and .claude/settings.json are gitignored for security"
echo "   - NEVER commit these files to version control"
echo "   - These files contain your real API key and are local-only"
echo ""
echo "Next steps:"
echo "  1. Reload your shell: source ~/.zshrc"
echo "  2. Or open a new terminal window"
echo "  3. Test with: echo \$CFBD_API_KEY"
echo ""
echo "Your API key will now persist across sessions!"