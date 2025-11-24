# GitHub MCP Server Setup

This guide documents the installation and configuration of the official GitHub MCP Server for Cursor IDE.

## Installation Complete ✅

The GitHub MCP Server has been installed and configured:
- **Binary Location**: `.cursor/bin/github-mcp-server`
- **Version**: 0.21.0
- **Configuration**: `.cursor/mcp.json`

## Setup Steps

### 1. Set GitHub Personal Access Token

You need to set up your GitHub Personal Access Token (PAT) to use the GitHub MCP server.

#### Create a GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Direct link: https://github.com/settings/tokens

2. Click "Generate new token" → "Generate new token (classic)"

3. Give your token a descriptive name (e.g., "Cursor MCP Server")

4. Select the following scopes (permissions):
   - `repo` - Full control of private repositories
   - `read:org` - Read org and team membership, read org projects
   - `read:user` - Read user profile data
   - `read:project` - Read project data
   - `workflow` - Update GitHub Action workflows (if needed)
   - `gist` - Create gists (optional)

5. Click "Generate token" and **copy the token immediately** (you won't be able to see it again)

#### Set the Token as Environment Variable

Add the token to your shell profile (e.g., `~/.zshrc` or `~/.bash_profile`):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bash_profile
```

**Note**: The configuration in `.cursor/mcp.json` uses `${GITHUB_PERSONAL_ACCESS_TOKEN}` which will read from your environment variables.

### 2. Restart Cursor IDE

After setting the environment variable, restart Cursor IDE for the changes to take effect.

### 3. Verify Installation

The GitHub MCP server should now be available in Cursor IDE. You can verify by:
- Opening Cursor Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
- Looking for MCP-related commands
- Checking that GitHub tools are available in the MCP panel

## Available Tools

The GitHub MCP Server provides access to:

- **Repositories**: List, search, get repository information
- **Issues**: Create, read, update, list issues and comments
- **Pull Requests**: Create, read, update, merge PRs and reviews
- **Branches**: Create, list, delete branches
- **Commits**: Get commit information and history
- **Files**: Read, create, update, delete files
- **Code Search**: Search repositories and code
- **Organizations**: List orgs, repositories, members
- **Users**: Search users, get user information
- **Copilot**: Create PRs with Copilot assistance
- **Copilot Spaces**: Access Copilot Spaces
- **Security Advisories**: List and manage security advisories

## Configuration Details

The GitHub MCP server is configured in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/.cursor/bin/github-mcp-server",
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      },
      "description": "GitHub MCP Server - Official GitHub integration"
    }
  }
}
```

## Troubleshooting

### Server Not Starting

1. **Check binary permissions**:
   ```bash
   ls -l .cursor/bin/github-mcp-server
   # Should show: -rwxr-xr-x
   ```

2. **Test binary directly**:
   ```bash
   .cursor/bin/github-mcp-server --version
   # Should output version information
   ```

3. **Check environment variable**:
   ```bash
   echo $GITHUB_PERSONAL_ACCESS_TOKEN
   # Should output your token (or empty if not set)
   ```

### Token Issues

- **Invalid token**: Make sure the token has the correct scopes/permissions
- **Token expired**: GitHub tokens can expire - generate a new one
- **Rate limiting**: GitHub API has rate limits - check your usage

### Update the Server

To update to the latest version:

1. Check latest release: https://github.com/github/github-mcp-server/releases
2. Download the new binary:
   ```bash
   cd .cursor/bin
   curl -L -o github-mcp-server_Darwin_arm64.tar.gz \
     "https://github.com/github/github-mcp-server/releases/download/v<VERSION>/github-mcp-server_Darwin_arm64.tar.gz"
   tar -xzf github-mcp-server_Darwin_arm64.tar.gz
   chmod +x github-mcp-server
   rm github-mcp-server_Darwin_arm64.tar.gz
   ```

## Security Notes

- ⚠️ **Never commit your GitHub token** to version control
- ✅ Use environment variables for token storage
- ✅ Rotate tokens regularly
- ✅ Use fine-grained tokens with minimal permissions when possible
- ✅ The `.cursor/bin/` directory should be in `.gitignore` (or just the token)

## Additional Resources

- [GitHub MCP Server Repository](https://github.com/github/github-mcp-server)
- [GitHub Personal Access Tokens Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Model Context Protocol (MCP) Documentation](https://modelcontextprotocol.io/)

## MCP Server Options

The GitHub MCP server supports additional options:

- `--read-only`: Only enable read-only operations
- `--dynamic-toolsets`: Enable dynamic tool discovery
- `--lockdown-mode`: Limit content from public repositories

To use these options, modify the command in `.cursor/mcp.json`:

```json
{
  "command": "/path/to/github-mcp-server",
  "args": ["--read-only"]  // Add options here
}
```







