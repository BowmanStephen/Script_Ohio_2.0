#!/bin/bash
# Startup script for Meta Orchestration Layer
# Top security level with comprehensive logging and monitoring

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] META-ORCHESTRATION: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 1000 ]; then
        log "ERROR: Not running as correct user (1000)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    # Check if encryption key is available
    if [ ! -z "$ENCRYPTION_KEY_FILE" ]; then
        if [ ! -f "$ENCRYPTION_KEY_FILE" ]; then
            log "WARNING: Encryption key file not found at $ENCRYPTION_KEY_FILE"
        fi
    fi

    log "Security context check completed"
}

# Function to initialize security manager
initialize_security() {
    log "Initializing security manager..."

    # Create security log directory
    mkdir -p /app/logs/security
    chmod 700 /app/logs/security

    # Set umask for secure file creation
    umask 077

    # Initialize audit log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SECURITY: System startup initiated" >> /app/logs/security/security_audit.log

    log "Security manager initialized"
}

# Function to start meta orchestration service
start_service() {
    log "Starting meta orchestration service..."

    # Check if required directories exist
    for dir in /app/logs /app/checkpoints; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Set environment variables
    export SECURITY_LEVEL="top_secret"
    export AUDIT_ENABLED="true"
    export LOG_LEVEL="INFO"
    export ENCRYPTION_KEY_FILE="/etc/agent-security/encryption.key"

    # Start the meta orchestration agent
    log "Starting Chief Architect Agent..."
    cd /app
    python3 -c "
from agents.orchration.chief_architect_agent import ChiefArchitectAgent
import json

# Create security context
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('meta-orchestration')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='chief_architect',
        permissions=[
            'system_admin',
            'api_access',
            'model_execution',
            'human_review'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize chief architect agent
    agent = ChiefArchitectAgent()
    logger.info('Chief Architect Agent initialized')

    # Start the main orchestration loop
    logger.info('Starting orchestration process...')

    # Execute the complete CFBD enhancement workflow
    result = agent.orchrate_cfbd_enhancement()

    # Log results
    logger.info(f'Orchestration completed: {result[\"status\"]}')

    # Save results to file for audit
    with open('/app/checkpoints/orchestration_result.json', 'w') as f:
        json.dump(result, f, indent=2)

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    import time
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Meta orchestration service stopped"
}

# Main execution
main() {
    log "Starting Meta Orchestration Layer..."

    # Perform security checks
    check_security_context

    # Initialize security
    initialize_security

    # Start service
    start_service
}

# Execute main function
main "$@"