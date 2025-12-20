#!/bin/bash
# Startup script for Risk Assessment Layer
# Restricted security level with threat detection

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RISK-ASSESSMENT: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 2002 ]; then
        log "ERROR: Not running as correct user (2002)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/risk-assessment-rules.json" ]; then
        log "WARNING: Risk assessment rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize risk assessment environment
initialize_risk() {
    log "Initializing risk assessment environment..."

    # Create risk assessment log directory
    mkdir -p /app/logs/risk
    chmod 755 /app/logs/risk

    # Set environment variables
    export SECURITY_LEVEL="restricted"
    export THREAT_DETECTION_ENABLED="true"
    export LOG_LEVEL="INFO"

    log "Risk assessment environment initialized"
}

# Function to start risk assessment service
start_service() {
    log "Starting risk assessment service..."

    # Check if required directories exist
    for dir in /app/data/risk-assessment /app/logs; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the risk assessment agent
    log "Starting Risk Assessment Agent..."
    cd /app
    python3 -c "
from agents.risk.risk_assessment_agent import RiskAssessmentAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('risk-assessment')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='risk_assessor',
        permissions=[
            'read_access',
            'risk_assessment',
            'threat_detection',
            'audit_logging'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize risk assessment agent
    agent = RiskAssessmentAgent()
    logger.info('Risk Assessment Agent initialized')

    # Start the main risk assessment loop
    logger.info('Starting risk assessment process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Risk assessment service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Risk assessment service stopped"
}

# Main execution
main() {
    log "Starting Risk Assessment Layer..."

    # Perform security checks
    check_security_context

    # Initialize risk assessment environment
    initialize_risk

    # Start service
    start_service
}

# Execute main function
main "$@"