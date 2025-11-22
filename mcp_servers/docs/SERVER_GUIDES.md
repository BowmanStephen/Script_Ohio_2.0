# MCP Server Guides for Script Ohio 2.0

## Overview

This guide provides detailed information about each MCP server integrated into the Script Ohio 2.0 college football analytics platform.

## Available MCP Servers

### Database Servers

#### 1. PostgreSQL Server (`@modelcontextprotocol/server-postgres`)
**Purpose**: Production-grade database operations
**Status**: ✅ Installed (deprecated but functional)
**Configuration**:
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/college_football"],
  "env": {
    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:postgres}"
  }
}
```

**Usage**:
- Complex analytical queries
- Production deployments
- Multi-user concurrent access
- Advanced indexing and performance optimization

**Setup**:
```bash
# Install PostgreSQL
brew install postgresql  # macOS
# Start PostgreSQL service
brew services start postgresql
# Create database
createdb college_football
```

#### 2. SQLite Server (`mcp-server-sqlite`)
**Purpose**: Local development and lightweight analytics
**Status**: ✅ Installed and Working
**Configuration**:
```json
{
  "command": "uvx",
  "args": ["mcp-server-sqlite", "--database-path", "data/databases/football_analysis.db"]
}
```

**Usage**:
- Local development
- Single-user analytics
- Rapid prototyping
- Embedded analytics

**Features**:
- Zero configuration
- File-based persistence
- ACID compliance
- Cross-platform compatibility

### Data Processing Servers

#### 3. Pandas Server (Local Implementation)
**Purpose**: Advanced data processing and analytics
**Status**: ⚠️ Local implementation (MCP package not available)
**Alternative**: Use Python pandas directly through agents

**Capabilities**:
- CSV/Excel file processing
- Data cleaning and transformation
- Statistical analysis
- Feature engineering
- Time series analysis

**Usage Example**:
```python
from agents.database_agent import DatabaseAgent
agent = DatabaseAgent()
# Pandas operations integrated into agent methods
```

### Visualization Servers

#### 4. ECharts Server (Local Implementation)
**Purpose**: Interactive data visualization
**Status**: ⚠️ Local implementation (MCP package not available)
**Alternative**: Matplotlib/Seaborn through visualization agent

**Chart Types**:
- Bar charts and histograms
- Line charts and time series
- Scatter plots and bubble charts
- Heatmaps and correlation matrices
- Interactive dashboards

#### 5. Datawrapper Server (Not Available)
**Purpose**: Professional chart publishing
**Status**: ❌ Package not found
**Alternative**: Export PNG/SVG from local charts

### System Servers

#### 6. Filesystem Server (`@modelcontextprotocol/server-filesystem`)
**Purpose**: File operations and management
**Status**: ✅ Installed and Working
**Capabilities**:
- Read/write files
- Directory operations
- File metadata access
- Path manipulation

**Usage**:
- Export analytics results
- Configuration management
- Data import/export
- Log file management

#### 7. Memory Server (`@modelcontextprotocol/server-memory`)
**Purpose**: Caching and session management
**Status**: ✅ Installed and Working
**Features**:
- Key-value storage
- Session persistence
- Query result caching
- Context management

### Web Data Servers

#### 8. Fetch Server (`fetch-mcp`)
**Purpose**: Web data acquisition
**Status**: ✅ Installed and Working
**Capabilities**:
- HTTP/HTTPS requests
- API integration
- Web scraping
- Data streaming

**Usage**:
- Live game data
- Statistics updates
- News and analysis
- Social media data

## Server Configuration

### Environment Setup

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Configure database credentials**:
```bash
# .env file
POSTGRES_PASSWORD=your_secure_password
SQLITE_PATH=data/databases/football_analysis.db
```

3. **Verify installations**:
```bash
npm list -g | grep mcp
```

### Server Startup

#### Automatic Startup (Recommended)
```bash
# Start all servers
python start_mcp_servers.py --servers all

# Start specific categories
python start_mcp_servers.py --servers database
python start_mcp_servers.py --servers processing
python start_mcp_servers.py --servers visualization
```

#### Manual Startup
```bash
# Start SQLite server
npx mcp-server-sqlite --database-path data/databases/football_analysis.db

# Start PostgreSQL server
npx @modelcontextprotocol/server-postgres postgresql://localhost/college_football

# Start filesystem server
npx @modelcontextprotocol/server-filesystem
```

### Server Monitoring

#### Health Checks
```bash
# Check server status
python start_mcp_servers.py --status

# Monitor servers (auto-restart)
python start_mcp_servers.py --monitor
```

#### Performance Monitoring
- Database query performance
- Memory usage tracking
- Request/response times
- Error rate monitoring

## Integration with Agents

### Database Agent Integration

```python
from agents.database_agent import DatabaseAgent

# Initialize with MCP tools
agent = DatabaseAgent()

# Execute queries through MCP
results = agent.execute_query("SELECT * FROM games WHERE season = 2024")
```

### Visualization Agent Integration

```python
from agents.visualization_agent import VisualizationAgent

# Create charts through MCP tools
agent = VisualizationAgent()
chart_path = agent.create_team_rankings_chart(data)
```

### Enhanced Orchestrator Integration

```python
from agents.mcp_enhanced_orchestrator import MCPEnhancedOrchestrator

# Initialize with MCP server management
orchestrator = MCPEnhancedOrchestrator()
orchestrator.initialize_mcp_servers()
```

## Troubleshooting

### Common Issues

#### 1. Server Won't Start
**Symptoms**: Error messages about missing packages or ports
**Solutions**:
```bash
# Reinstall packages
npm install -g @modelcontextprotocol/server-postgres mcp-server-sqlite

# Check port availability
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Common MCP port
```

#### 2. Database Connection Errors
**Symptoms**: Connection timeout or authentication errors
**Solutions**:
```bash
# Check PostgreSQL status
brew services list | grep postgres

# Test connection
psql -h localhost -U postgres -d college_football

# Reset password
ALTER USER postgres PASSWORD 'new_password';
```

#### 3. Performance Issues
**Symptoms**: Slow queries or high memory usage
**Solutions**:
- Add database indexes
- Optimize queries
- Increase memory limits
- Use query caching

### Debug Mode

Enable debug logging:
```bash
python start_mcp_servers.py --debug
```

Check log files:
```bash
tail -f logs/mcp_servers_*.log
```

## Best Practices

### 1. Development Environment
- Use SQLite for local development
- Enable debug logging
- Use test databases
- Regular backups

### 2. Production Environment
- Use PostgreSQL for production
- Monitor performance metrics
- Implement backup strategies
- Use SSL connections
- Set up connection pooling

### 3. Security
- Use environment variables for credentials
- Implement access controls
- Regular security updates
- Audit logging

### 4. Performance Optimization
- Create appropriate indexes
- Use query result caching
- Monitor slow queries
- Optimize database schema

## Future Enhancements

### Planned MCP Servers
1. **Redis Integration**: Advanced caching and session management
2. **ClickHouse Integration**: Analytics-optimized database
3. **Apache Arrow**: High-performance data processing
4. **Apache Superset**: Business intelligence dashboard
5. **Grafana Integration**: Monitoring and alerting

### Feature Roadmap
- Real-time data streaming
- Machine learning model serving
- Advanced visualization capabilities
- Multi-tenant architecture
- API gateway integration

## Support

### Documentation
- [Main documentation](../README.md)
- [Quick start guide](../QUICK_START_CLAUDE_CODE.md)
- [Setup guide](SETUP_GUIDE.md)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Community support and questions
- Wiki: Additional documentation and examples

### Getting Help
1. Check this guide first
2. Review log files for error messages
3. Search existing GitHub issues
4. Create new issue with detailed information
5. Join community discussions

---

**Last Updated**: November 12, 2025
**Version**: 1.0.0
**Platform**: Script Ohio 2.0 College Football Analytics