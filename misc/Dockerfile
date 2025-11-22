# Production-ready Dockerfile for Script Ohio 2.0
# Multi-stage build for security and optimization
FROM python:3.13-slim-bullseye as base

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels for container metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="script-ohio-2.0" \
      org.label-schema.description="Intelligent College Football Analytics Platform" \
      org.label-schema.url="https://github.com/college-football/script-ohio-2.0" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/college-football/script-ohio-2.0.git" \
      org.label-schema.vendor="Script Ohio Analytics" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Security: Create non-root user
RUN groupadd -r scriptuser && useradd -r -g scriptuser scriptuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
COPY requirements-prod.txt .

# Install Python dependencies
# NOTE: FastAPI/uvicorn/gunicorn removed - not currently used in codebase
# If web API is needed in future, add to requirements-prod.txt and uncomment below
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Security stage: Remove build dependencies
FROM base as security
RUN apt-get remove --purge -y build-essential curl git gcc g++ && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Production stage
FROM security as production

# Copy application code
COPY --chown=scriptuser:scriptuser . /app

# Set proper permissions
RUN chmod -R 755 /app && \
    chmod -R 644 /app/*.py && \
    mkdir -p /app/logs /app/data /app/models && \
    chown -R scriptuser:scriptuser /app/logs /app/data /app/models

# Security: Copy health check script
COPY --chown=scriptuser:scriptuser deployment/health-check.sh /app/health-check.sh
RUN chmod +x /app/health-check.sh

# Switch to non-root user
USER scriptuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD /app/health-check.sh

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# NOTE: Web API not currently implemented - agents.main:app does not exist
# If web API is needed, create agents/main.py or agents/api.py with FastAPI app
# Then uncomment and update CMD below, and add FastAPI to requirements-prod.txt
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "100", "--access-logfile", "-", "--error-logfile", "-", "agents.main:app"]

# Default command: Run Python interpreter (can be overridden)
# For now, this is a library/application package, not a web service
CMD ["python", "-c", "from agents import AnalyticsOrchestrator; print('Script Ohio 2.0 Agent System loaded successfully')"]

# Development stage (for local development)
FROM base as development
COPY --chown=scriptuser:scriptuser . /app
RUN chmod -R 755 /app
USER scriptuser
# NOTE: Web API not currently implemented - update when FastAPI is added
# CMD ["uvicorn", "agents.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD ["python", "-c", "from agents import AnalyticsOrchestrator; print('Script Ohio 2.0 Development Environment')"]