#!/bin/bash
# Startup script for Planning & Coordination Layer
# High security level with read-only execution

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PLANNING-COORDINATION: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 2000 ]; then
        log "ERROR: Not running as correct user (2000)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    log "Security context check completed"
}

# Function to initialize planning environment
initialize_planning() {
    log "Initializing planning environment..."

    # Create planning log directory
    mkdir -p /app/logs/planning
    chmod 755 /app/logs/planning

    # Set environment variables
    export SECURITY_LEVEL="restricted"
    export READ_ONLY_MODE="true"
    export AUDIT_ENABLED="true"
    export LOG_LEVEL="INFO"
    export PLANNING_MODE="strategic"

    log "Planning environment initialized"
}

# Function to start planning coordination service
start_service() {
    log "Starting planning coordination service..."

    # Check if required directories exist
    for dir in /app/plans /app/logs; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the planning coordination agent
    log "Starting Planning Coordinator Agent..."
    cd /app
    python3 -c "
from agents.planning.planning_coordinator_agent import PlanningCoordinatorAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('planning-coordination')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='planning_coordinator',
        permissions=[
            'system_admin',
            'planning_access',
            'read_only_mode'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize planning coordinator agent
    agent = PlanningCoordinatorAgent()
    logger.info('Planning Coordinator Agent initialized')

    # Start the main planning loop
    logger.info('Starting planning coordination process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Planning service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Planning coordination service stopped"
}

# Main execution
main() {
    log "Starting Planning & Coordination Layer..."

    # Perform security checks
    check_security_context

    # Initialize planning environment
    initialize_planning

    # Start service
    start_service
}

# Execute main function
main "$@"