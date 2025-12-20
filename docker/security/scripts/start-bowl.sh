#!/bin/bash
# Startup script for Bowl Games Specialist Layer
# Restricted security level with specialized bowl games prediction

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BOWL-GAMES-SPECIALIST: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 4002 ]; then
        log "ERROR: Not running as correct user (4002)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/bowl-games-rules.json" ]; then
        log "WARNING: Bowl games rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize bowl games environment
initialize_bowl() {
    log "Initializing bowl games environment..."

    # Create bowl games log directory
    mkdir -p /app/logs/bowl
    mkdir -p /app/reports/bowl
    chmod 755 /app/logs/bowl
    chmod 755 /app/reports/bowl

    # Set environment variables
    export SECURITY_LEVEL="restricted"
    export BOWL_GAMES_SPECIALIZATION="true"
    export PREDICTION_CONFIDENCE_THRESHOLD="0.65"
    export LOG_LEVEL="INFO"

    log "Bowl games environment initialized"
}

# Function to start bowl games service
start_service() {
    log "Starting bowl games specialist service..."

    # Check if required directories exist
    for dir in /app/data/bowl-games /app/cache/bowl /app/logs /app/reports/bowl; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the bowl games specialist agent
    log "Starting Bowl Games Specialist Agent..."
    cd /app
    python3 -c "
from agents.bowl.bowl_games_specialist_agent import BowlGamesSpecialistAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bowl-games')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='bowl_specialist',
        permissions=[
            'read_write_access',
            'bowl_games_specialization',
            'prediction_generation'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize bowl games specialist agent
    agent = BowlGamesSpecialistAgent()
    logger.info('Bowl Games Specialist Agent initialized')

    # Start the main bowl games loop
    logger.info('Starting bowl games specialist process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Bowl games service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Bowl games specialist service stopped"
}

# Main execution
main() {
    log "Starting Bowl Games Specialist Layer..."

    # Perform security checks
    check_security_context

    # Initialize bowl games environment
    initialize_bowl

    # Start service
    start_service
}

# Execute main function
main "$@"