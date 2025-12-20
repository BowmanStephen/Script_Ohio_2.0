# Workflow Coordination Layer Dockerfile
# High Security - Workflow management with communication capabilities
# User: 2001:2001 (Workflow operations user)
# Capabilities: NET_BIND_SERVICE (for communication interfaces)
# Security: no-new-privileges, apparmor, seccomp
# Networks: orchestration-network, data-network, communication-network, audit-network

FROM python:3.13-slim

# Create system user
RUN groupadd -r -g 2001 workflow_user && \
    useradd -r -u 2001 -g workflow_user workflow_user

# Install system packages for workflow operations
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        jq \
        wget \
        htop \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install workflow management dependencies
RUN pip install --no-cache-dir \
    celery \
    redis \
    rabbitmq \
    pydantic \
    fastapi \
    uvicorn \
    websockets \
    asyncio \
    aiofiles

# Copy application code
COPY agents/workflow/ ./agents/workflow/
COPY agents/core/ ./agents/core/
COPY docker/security/scripts/start-workflow.sh ./
COPY docker/security/scripts/health-check.sh ./

# Create workflow and communication directories
RUN mkdir -p /app/workflows /app/communication /app/logs && \
    chown -R workflow_user:workflow_user /app && \
    chmod -R 755 /app

# Copy security configuration
COPY docker/security/security-policies.json /etc/agent-security/
COPY docker/security/communication-rules.json /etc/agent-security/
RUN chmod 600 /etc/agent-security/security-policies.json && \
    chmod 600 /etc/agent-security/communication-rules.json

# Set ownership
RUN chown -R workflow_user:workflow_user /app

# Switch to non-root user
USER workflow_user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["./health-check.sh"]

# Expose port for workflow coordination interface
EXPOSE 8400

# Start command
CMD ["./start-workflow.sh"]