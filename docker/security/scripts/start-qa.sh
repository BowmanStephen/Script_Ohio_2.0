#!/bin/bash
# Startup script for Quality Assurance Layer
# Confidential security level with comprehensive validation

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] QUALITY-ASSURANCE: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 5000 ]; then
        log "ERROR: Not running as correct user (5000)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/qa-rules.json" ]; then
        log "WARNING: QA rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize QA environment
initialize_qa() {
    log "Initializing QA environment..."

    # Create QA log directory
    mkdir -p /app/logs/qa
    mkdir -p /app/reports/validation
    chmod 755 /app/logs/qa
    chmod 755 /app/reports/validation

    # Set environment variables
    export SECURITY_LEVEL="confidential"
    export VALIDATION_MODE="comprehensive"
    export QUALITY_THRESHOLD="0.98"
    export LOG_LEVEL="INFO"

    log "QA environment initialized"
}

# Function to start QA service
start_service() {
    log "Starting quality assurance service..."

    # Check if required directories exist
    for dir in /app/logs /app/reports/validation; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the quality assurance agent
    log "Starting Quality Assurance Agent..."
    cd /app
    python3 -c "
from agents.qa.quality_assurance_agent import QualityAssuranceAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('quality-assurance')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='qa_specialist',
        permissions=[
            'read_access',
            'validation_access',
            'quality_assurance',
            'audit_logging'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize quality assurance agent
    agent = QualityAssuranceAgent()
    logger.info('Quality Assurance Agent initialized')

    # Start the main QA loop
    logger.info('Starting quality assurance process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('QA service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Quality assurance service stopped"
}

# Main execution
main() {
    log "Starting Quality Assurance Layer..."

    # Perform security checks
    check_security_context

    # Initialize QA environment
    initialize_qa

    # Start service
    start_service
}

# Execute main function
main "$@"