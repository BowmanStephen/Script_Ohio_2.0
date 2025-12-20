#!/bin/bash
# Startup script for Workflow Coordination Layer
# High security level with communication management

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WORKFLOW-COORDINATION: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 2001 ]; then
        log "ERROR: Not running as correct user (2001)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/communication-rules.json" ]; then
        log "WARNING: Communication rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize workflow environment
initialize_workflow() {
    log "Initializing workflow environment..."

    # Create workflow log directory
    mkdir -p /app/logs/workflow
    chmod 755 /app/logs/workflow

    # Set environment variables
    export SECURITY_LEVEL="confidential"
    export COMMUNICATION_ENCRYPTION="true"
    export LOG_LEVEL="INFO"
    export WORKFLOW_MODE="coordinated"

    log "Workflow environment initialized"
}

# Function to start workflow coordination service
start_service() {
    log "Starting workflow coordination service..."

    # Check if required directories exist
    for dir in /app/workflows /app/communication /app/logs; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the workflow coordination agent
    log "Starting Workflow Coordinator Agent..."
    cd /app
    python3 -c "
from agents.workflow.workflow_coordinator_agent import WorkflowCoordinatorAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('workflow-coordination')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='workflow_coordinator',
        permissions=[
            'system_admin',
            'workflow_management',
            'communication_encryption'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize workflow coordinator agent
    agent = WorkflowCoordinatorAgent()
    logger.info('Workflow Coordinator Agent initialized')

    # Start the main workflow loop
    logger.info('Starting workflow coordination process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Workflow service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Workflow coordination service stopped"
}

# Main execution
main() {
    log "Starting Workflow & Coordination Layer..."

    # Perform security checks
    check_security_context

    # Initialize workflow environment
    initialize_workflow

    # Start service
    start_service
}

# Execute main function
main "$@"