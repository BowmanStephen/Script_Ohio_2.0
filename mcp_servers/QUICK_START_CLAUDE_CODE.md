# Quick Start: Claude Code with MCP Servers

Get your enhanced college football analytics platform running with Claude Code in just a few minutes!

## 🚀 Quick Setup (5 Minutes)

```bash
# Navigate to MCP directory
cd mcp_servers

# Run the automated setup
python scripts/setup_claude_code_mcp.py --install

# Configure your credentials
cp .env.example .env
# Edit .env with your actual API keys and passwords

# Validate everything is working
python scripts/setup_claude_code_mcp.py --validate
```

## 📋 Prerequisites

Make sure you have these installed:
- **Node.js** (v16+) - `node --version`
- **Python** (v3.8+) - `python --version`
- **Claude Code CLI** - `claude --version`

## 🎯 What You Get

With MCP servers enabled, Claude Code gains powerful analytics capabilities:

### Database Operations
- **Query historical game data** (1869-present)
- **Real-time 2025 season data** access
- **Advanced statistical analysis** with SQL

### Data Processing
- **Pandas integration** for data manipulation
- **CSV processing** for game statistics
- **Feature engineering** for ML models

### Visualization
- **Dynamic chart generation** (ECharts, Datawrapper)
- **Professional dashboards** creation
- **Export capabilities** (PNG, SVG, PDF)

### File Management
- **Project file access** for notebooks and models
- **Version control integration** with GitHub
- **Memory persistence** for insights

## 💬 Usage Examples

Start Claude Code and try these commands:

### Database Queries
```
Show me the top 10 teams by points scored in the 2025 season.
```

### Advanced Analytics
```
Process the game data to calculate EPA for each team's offense this season.
```

### Visualizations
```
Create a bar chart showing scoring averages for the Big Ten conference.
```

### Predictions
```
Using the ML models, predict this week's games and show confidence levels.
```

## 🔧 Configuration

Your MCP configuration is automatically installed to:
```
~/.claude/claude_desktop_config.json
```

The setup creates these enabled servers:
- **Database servers** (PostgreSQL, SQLite)
- **Data processing** (Pandas, CSV Editor)
- **Visualization** (ECharts, Datawrapper, QuickChart)
- **File system** access for project files
- **Memory** for storing insights
- **Web fetching** for additional data
- **GitHub** integration

## 🧪 Testing

Validate your setup:

```bash
# Test all MCP servers
python scripts/test_mcp_integration.py

# Test specific categories
python scripts/test_mcp_integration.py --category database
python scripts/test_mcp_integration.py --category visualization

# Performance testing
python scripts/test_mcp_integration.py --performance
```

## 📊 Example Workflow

```bash
# Start Claude Code
claude

# Example session:
You: "Using the database tools, show me Ohio State's performance over the last 5 seasons."

Claude: [Analyzes data from database, creates visualizations, stores insights]

You: "Now create a prediction model for their next game against Michigan."

Claude: [Uses ML models, processes data, generates predictions with confidence scores]
```

## 🛠️ Troubleshooting

### MCP Servers Not Responding
```bash
# Check configuration
python scripts/setup_claude_code_mcp.py --validate

# Restart Claude Code
# Configuration reloads automatically
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Verify database exists
psql -l | grep college_football
```

### Missing API Keys
```bash
# Edit environment file
nano mcp_servers/.env

# Add your actual credentials:
GITHUB_TOKEN=your_real_token_here
```

## 📚 Documentation

- **Complete Setup Guide**: `docs/SETUP_GUIDE.md`
- **Usage Examples**: `docs/CLAUDE_CODE_USAGE_EXAMPLES.md`
- **Server Configuration**: `config/`
- **Integration Tests**: `scripts/test_mcp_integration.py`

## 🎉 Success!

When setup is complete, you'll see:
```
🎉 SETUP COMPLETE! Your MCP servers are ready for Claude Code.
```

Now you can:
- ✅ Query databases with natural language
- ✅ Process data with pandas integration
- ✅ Create dynamic visualizations
- ✅ Access all project files
- ✅ Store and retrieve insights
- ✅ Use advanced analytics capabilities

## 🆘 Need Help?

1. Check the validation output
2. Review the logs: `logs/claude_setup.log`
3. Run the diagnostic tests
4. Check the troubleshooting section in the full setup guide

---

*Ready to supercharge your college football analytics with Claude Code + MCP!* ⚡