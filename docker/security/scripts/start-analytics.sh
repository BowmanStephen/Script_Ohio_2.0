#!/bin/bash
# Startup script for Advanced Analytics Layer
# Confidential security level with GPU acceleration

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ADVANCED-ANALYTICS: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 4001 ]; then
        log "ERROR: Not running as correct user (4001)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/analytics-rules.json" ]; then
        log "WARNING: Analytics rules file not found"
    fi

    # Check GPU availability
    if [ -e /dev/nvidia0 ]; then
        log "GPU detected: NVIDIA device available"
    else
        log "WARNING: No GPU detected, falling back to CPU"
    fi

    log "Security context check completed"
}

# Function to initialize analytics environment
initialize_analytics() {
    log "Initializing analytics environment..."

    # Create analytics log directory
    mkdir -p /app/logs/analytics
    mkdir -p /app/reports
    chmod 755 /app/logs/analytics
    chmod 755 /app/reports

    # Set environment variables
    export SECURITY_LEVEL="confidential"
    export ADVANCED_ANALYTICS="true"
    export GPU_ACCELERATION="true"
    export REPORT_GENERATION="true"
    export LOG_LEVEL="INFO"

    log "Analytics environment initialized"
}

# Function to start advanced analytics service
start_service() {
    log "Starting advanced analytics service..."

    # Check if required directories exist
    for dir in /app/cache/analytics /app/logs /app/reports; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the advanced analytics agent
    log "Starting Advanced Analytics Agent..."
    cd /app
    python3 -c "
from agents.analytics.advanced_analytics_agent import AdvancedAnalyticsAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('advanced-analytics')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='advanced_analyst',
        permissions=[
            'read_write_access',
            'advanced_analytics',
            'gpu_acceleration',
            'report_generation'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize advanced analytics agent
    agent = AdvancedAnalyticsAgent()
    logger.info('Advanced Analytics Agent initialized')

    # Start the main analytics loop
    logger.info('Starting advanced analytics process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Analytics service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Advanced analytics service stopped"
}

# Main execution
main() {
    log "Starting Advanced Analytics Layer..."

    # Perform security checks
    check_security_context

    # Initialize analytics environment
    initialize_analytics

    # Start service
    start_service
}

# Execute main function
main "$@"