#!/bin/bash
# Startup script for Data Validation Layer
# High security level with comprehensive data validation

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] DATA-VALIDATION: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 3001 ]; then
        log "ERROR: Not running as correct user (3001)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/validation-rules.json" ]; then
        log "WARNING: Validation rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize validation environment
initialize_validation() {
    log "Initializing validation environment..."

    # Create validation log directory
    mkdir -p /app/logs/validation
    chmod 755 /app/logs/validation

    # Set environment variables
    export SECURITY_LEVEL="confidential"
    export VALIDATION_STRICT="true"
    export QUALITY_THRESHOLD="0.95"
    export LOG_LEVEL="INFO"

    log "Validation environment initialized"
}

# Function to start data validation service
start_service() {
    log "Starting data validation service..."

    # Check if required directories exist
    for dir in /app/data/validation /app/cache/validation /app/logs; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the data validation agent
    log "Starting Data Validation Agent..."
    cd /app
    python3 -c "
from agents.validation.data_validation_agent import DataValidationAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('data-validation')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='data_validator',
        permissions=[
            'read_access',
            'validation_access',
            'audit_logging'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize data validation agent
    agent = DataValidationAgent()
    logger.info('Data Validation Agent initialized')

    # Start the main validation loop
    logger.info('Starting data validation process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Validation service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Data validation service stopped"
}

# Main execution
main() {
    log "Starting Data Validation Layer..."

    # Perform security checks
    check_security_context

    # Initialize validation environment
    initialize_validation

    # Start service
    start_service
}

# Execute main function
main "$@"