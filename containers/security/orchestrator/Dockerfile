# Security Orchestrator - High security container
FROM python:3.13-slim

# Security user setup
RUN addgroup --system --gid 1001 securitygroup && \
    adduser --system --uid 1001 --gid 1001 securityuser

# Install security tools
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        openssl \
        curl \
        netcat-openbsd \
        iproute2 \
        iptables \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Security requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy security orchestrator code
COPY agents/security_orchestrator.py .
COPY containers/security/orchestrator/entrypoint.sh .

# Set permissions
RUN chown -R securityuser:securitygroup /app && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER securityuser

# Security health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/entrypoint.sh --health-check || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["orchestrate"]