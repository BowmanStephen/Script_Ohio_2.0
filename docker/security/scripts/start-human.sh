#!/bin/bash
# Startup script for Human Interface Layer
# Restricted security level with human review management

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] HUMAN-INTERFACE: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 5002 ]; then
        log "ERROR: Not running as correct user (5002)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/human-interface-rules.json" ]; then
        log "WARNING: Human interface rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize human interface environment
initialize_human() {
    log "Initializing human interface environment..."

    # Create human interface log directory
    mkdir -p /app/logs/human
    mkdir -p /app/reports/human
    chmod 755 /app/logs/human
    chmod 755 /app/reports/human

    # Set environment variables
    export SECURITY_LEVEL="restricted"
    export HUMAN_REVIEW_ENABLED="true"
    export ESCALATION_TIMEOUT="3600"
    export LOG_LEVEL="INFO"

    log "Human interface environment initialized"
}

# Function to start human interface service
start_service() {
    log "Starting human interface service..."

    # Check if required directories exist
    for dir in /app/reviews /app/logs /app/reports/human; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the human review coordinator agent
    log "Starting Human Review Coordinator Agent..."
    cd /app
    python3 -c "
from agents.human.human_review_coordinator_agent import HumanReviewCoordinatorAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('human-interface')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='human_review_coordinator',
        permissions=[
            'read_write_access',
            'human_review_management',
            'escalation_handling'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize human review coordinator agent
    agent = HumanReviewCoordinatorAgent()
    logger.info('Human Review Coordinator Agent initialized')

    # Start the main human interface loop
    logger.info('Starting human review coordination process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Human interface service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Human interface service stopped"
}

# Main execution
main() {
    log "Starting Human Interface Layer..."

    # Perform security checks
    check_security_context

    # Initialize human interface environment
    initialize_human

    # Start service
    start_service
}

# Execute main function
main "$@"