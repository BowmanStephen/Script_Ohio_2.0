# MCP Server Setup Guide

This comprehensive guide walks you through installing and configuring Model Context Protocol (MCP) servers for the College Football Analytics Platform.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Phase-by-Phase Installation](#phase-by-phase-installation)
4. [Configuration](#configuration)
5. [Testing and Validation](#testing-and-validation)
6. [Integration with Agent System](#integration-with-agent-system)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

## 🔧 Prerequisites

### Required Software

1. **Node.js** (v16.0 or higher)
   ```bash
   # Check version
   node --version
   npm --version

   # Install if needed (macOS)
   brew install node

   # Install if needed (Windows)
   # Download from https://nodejs.org/
   ```

2. **Python** (v3.8 or higher)
   ```bash
   # Check version
   python --version
   pip --version

   # Install if needed (macOS)
   brew install python

   # Install if needed (Windows)
   # Download from https://python.org/
   ```

3. **uvx** (for Python package management)
   ```bash
   # Install uvx
   pip install uvx
   ```

4. **Git** (version control)
   ```bash
   # Check version
   git --version

   # Install if needed (macOS)
   brew install git

   # Install if needed (Windows)
   # Download from https://git-scm.com/
   ```

### Optional Software

1. **PostgreSQL** (for database server)
   ```bash
   # Install on macOS
   brew install postgresql
   brew services start postgresql

   # Install on Windows
   # Download from https://postgresql.org/download/windows/
   ```

2. **Docker** (for containerized deployment)
   ```bash
   # Install Docker Desktop
   # Download from https://www.docker.com/products/docker-desktop
   ```

## 🚀 Quick Start

Get MCP servers running in 5 minutes with these commands:

```bash
# Navigate to MCP directory
cd mcp_servers

# Install all MCP servers
python scripts/install_mcp_servers.py --phase all

# Set up environment variables
cp .env.example .env
# Edit .env file with your API keys and credentials

# Start MCP servers
python start_mcp_servers.py
```

## 📅 Phase-by-Phase Installation

### Phase 1: Critical Infrastructure (Weeks 1-2)

These servers provide essential functionality for data operations and management.

#### Database Servers

```bash
# Install database MCP servers
python scripts/install_mcp_servers.py --phase phase1

# Setup PostgreSQL database
createdb college_football

# Import existing data (optional)
python scripts/migrate_to_database.py
```

**Files Created:**
- `data/football_analysis.db` - SQLite database for local operations
- PostgreSQL database for production operations
- Database schemas and indexes

#### Data Processing Servers

```bash
# Install pandas and CSV processing capabilities
pip install pandas numpy scipy
uvx mcp-server-pandas
npx -y @modelcontextprotocol/server-csv-editor
```

**Capabilities Added:**
- Advanced data manipulation for 86 opponent-adjusted features
- Automated CSV processing and cleaning
- Real-time data validation

### Phase 2: High Value Additions (Weeks 3-4)

These servers significantly enhance user experience and capabilities.

#### Visualization Servers

```bash
# Install visualization capabilities
npx -y @modelcontextprotocol/server-echarts
npx -y @modelcontextprotocol/server-datawrapper
npx -y @modelcontextprotocol/server-quickchart
```

**Features Added:**
- Dynamic football visualizations and dashboards
- Professional chart creation for reports
- Real-time chart generation API integration

#### Web Data Acquisition

```bash
# Install web scraping and data acquisition
npx -y @modelcontextprotocol/server-fetch
# Firecrawl requires API key - see configuration section
```

**Capabilities Added:**
- Enhanced web content retrieval
- Sports data beyond CFBD API
- Automated data pipeline updates

### Phase 3: Integration & Optimization (Weeks 5-6)

Complete the setup with external API integrations and performance optimization.

#### External API Integration

```bash
# Install GitHub integration
npx -y @modelcontextprotocol/server-github

# Install Google Sheets integration
uvx mcp-server-google-sheets
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `mcp_servers/` directory:

```bash
# Database Configuration
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_USER=postgres
POSTGRES_DB=college_football

# API Keys (Optional)
FIRECRAWL_API_KEY=your_firecrawl_api_key
GITHUB_TOKEN=your_github_personal_access_token
GOOGLE_CREDS_FILE=path/to/google_credentials.json

# Server Configuration
MCP_LOG_LEVEL=info
MCP_TIMEOUT=30000
MCP_CACHE_DURATION=3600
```

### Database Configuration

#### PostgreSQL Setup

1. **Create Database:**
   ```bash
   createdb college_football
   ```

2. **Create User (optional):**
   ```sql
   CREATE USER football_analyst WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE college_football TO football_analyst;
   ```

3. **Update Configuration:**
   Edit `config/databases.json` with your connection details:
   ```json
   {
     "connection_string": "postgresql://football_analyst:your_password@localhost/college_football"
   }
   ```

#### SQLite Setup

SQLite is configured automatically. The database file is created at:
```
data/football_analysis.db
```

### Server Configuration

Individual server configurations are located in `config/`:

- `databases.json` - Database server configurations
- `data_processing.json` - Data processing server settings
- `visualization.json` - Visualization server parameters
- `api_integration.json` - External API configurations

## 🧪 Testing and Validation

### Basic Connectivity Test

```bash
# Test all MCP server connections
python scripts/test_mcp_integration.py

# Test specific server category
python scripts/test_mcp_integration.py --category database

# Test with verbose output
python scripts/test_mcp_integration.py --verbose
```

### Performance Benchmarking

```bash
# Run performance benchmarks
python scripts/benchmark_mcp_servers.py

# Generate performance report
python scripts/generate_performance_report.py
```

### Integration Testing

```python
# Test enhanced orchestrator
from mcp_servers.agents.mcp_enhanced_orchestrator import MCPEnhancedOrchestrator
import asyncio

async def test_integration():
    orchestrator = MCPEnhancedOrchestrator()
    await orchestrator.initialize_mcp_servers()

    # Create test request
    request = create_enhanced_request(
        user_id="test_user",
        request_text="Show team performance",
        require_database=True
    )

    # Process request
    result = await orchestrator.process_enhanced_analytics_request(request)
    print(f"Success: {result['success']}")

    await orchestrator.shutdown()

asyncio.run(test_integration())
```

## 🔗 Integration with Agent System

### Enhanced Orchestrator

The MCP-enhanced orchestrator seamlessly integrates with your existing agent system:

```python
# Import the enhanced orchestrator
from mcp_servers.agents.mcp_enhanced_orchestrator import MCPEnhancedOrchestrator

# Initialize
orchestrator = MCPEnhancedOrchestrator()
await orchestrator.initialize_mcp_servers()

# Use in place of traditional orchestrator
result = await orchestrator.process_enhanced_analytics_request(request)
```

### Jupyter Notebook Integration

Add MCP capabilities to your notebooks:

```python
# In your notebook
import sys
sys.path.append('../mcp_servers')
from agents.mcp_enhanced_orchestrator import create_enhanced_request, add_mcp_database_operation

# Create enhanced request
request = create_enhanced_request(
    user_id="notebook_user",
    request_text="Analyze 2025 season data",
    require_visualization=True
)

# Add database query
add_mcp_database_operation(request, """
    SELECT team_name, AVG(points_scored) as avg_points
    FROM games WHERE season = 2025
    GROUP BY team_name ORDER BY avg_points DESC
""")
```

### Agent System Updates

Update your existing agents to use MCP capabilities:

```python
# In your agent files
from mcp_servers.agents.mcp_enhanced_orchestrator import MCPEnhancedOrchestrator

class EnhancedAnalyticsAgent:
    def __init__(self):
        self.orchestrator = MCPEnhancedOrchestrator()

    async def process_request(self, user_request):
        enhanced_request = self._convert_to_mcp_request(user_request)
        return await self.orchestrator.process_enhanced_analytics_request(enhanced_request)
```

## 🔧 Troubleshooting

### Common Issues

#### Installation Failures

**Problem:** `npm` command not found
**Solution:**
```bash
# Install Node.js
brew install node  # macOS
# or download from https://nodejs.org/

# Verify installation
node --version
npm --version
```

**Problem:** Permission denied errors
**Solution:**
```bash
# Use npm with sudo (not recommended for production)
sudo npm install -g package_name

# Or fix npm permissions
npm config set prefix ~/.npm-global
export PATH=~/.npm-global/bin:$PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
```

#### Connection Issues

**Problem:** Database connection failed
**Solution:**
1. Check PostgreSQL is running: `brew services list | grep postgresql`
2. Verify database exists: `psql -l`
3. Test connection: `psql -d college_football`

**Problem:** MCP server not responding
**Solution:**
```bash
# Check server status
python scripts/test_mcp_integration.py --category all

# Restart servers
python start_mcp_servers.py --restart

# Check logs
tail -f logs/orchestrator.log
```

#### Performance Issues

**Problem:** Slow response times
**Solutions:**
1. Enable caching in configuration
2. Optimize database queries
3. Increase server timeouts
4. Use data processing chunks for large datasets

```json
{
  "global_settings": {
    "cache_enabled": true,
    "cache_duration": 7200,
    "timeout": 60000
  }
}
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export MCP_LOG_LEVEL=debug
```

### Getting Help

1. Check logs: `tail -f logs/*.log`
2. Run diagnostic: `python scripts/diagnose_mcp_issues.py`
3. Review configuration: Validate JSON syntax
4. Check network connectivity for external APIs

## 🚀 Advanced Configuration

### Production Deployment

For production use, modify `config/mcp_config.json`:

```json
{
  "deployment": {
    "production": {
      "essential_servers_only": true,
      "security_mode": true,
      "monitoring_enabled": true,
      "load_balancing": true
    }
  }
}
```

### Security Configuration

1. **Environment Variables:** Use `.env` file for sensitive data
2. **API Rate Limiting:** Configure in `mcp_config.json`
3. **Access Control:** Implement user authentication
4. **Data Encryption:** Enable SSL/TLS for database connections

### Performance Optimization

1. **Database Optimization:**
   ```sql
   CREATE INDEX CONCURRENTLY idx_games_season ON games(season);
   CREATE INDEX CONCURRENTLY idx_games_teams ON games(home_team, away_team);
   ```

2. **Caching Strategy:**
   ```json
   {
     "cache": {
       "frequent_queries": true,
       "visualization_cache": true,
       "model_predictions": true
     }
   }
   ```

3. **Resource Allocation:**
   ```json
   {
     "resources": {
       "max_memory": "4GB",
       "max_cpu": "2 cores",
       "concurrent_requests": 50
     }
   }
   ```

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [College Football Analytics Platform Documentation](../CLAUDE.md)
- [Agent System Architecture Guide](../project_management/PROJECT_DOCUMENTATION/AGENT_ARCHITECTURE_GUIDE.md)

## 🆘 Support

If you encounter issues not covered in this guide:

1. Check the log files in `logs/`
2. Run the diagnostic script
3. Review the troubleshooting section
4. Create an issue with details about your environment and error messages

---

*Last updated: November 2025*
*Version: 1.0.0*