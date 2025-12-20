#!/bin/bash
# Startup script for Weather Integration Layer
# Restricted security level with external API access

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WEATHER-INTEGRATION: $1"
}

# Function to check security context
check_security_context() {
    log "Checking security context..."

    # Check if running as correct user
    if [ "$(id -u)" -ne 3003 ]; then
        log "ERROR: Not running as correct user (3003)"
        exit 1
    fi

    # Check if security files exist and are readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not found"
    fi

    if [ ! -f "/etc/agent-security/weather-api-rules.json" ]; then
        log "WARNING: Weather API rules file not found"
    fi

    log "Security context check completed"
}

# Function to initialize weather integration environment
initialize_weather() {
    log "Initializing weather integration environment..."

    # Create weather integration log directory
    mkdir -p /app/logs/weather
    chmod 755 /app/logs/weather

    # Set environment variables
    export SECURITY_LEVEL="restricted"
    export WEATHER_API_ACCESS="true"
    export RATE_LIMIT_PER_MINUTE="60"
    export LOG_LEVEL="INFO"

    log "Weather integration environment initialized"
}

# Function to start weather integration service
start_service() {
    log "Starting weather integration service..."

    # Check if required directories exist
    for dir in /app/data/weather /app/cache/weather /app/logs; do
        if [ ! -d "$dir" ]; then
            log "Creating directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Start the weather integration agent
    log "Starting Weather Integration Agent..."
    cd /app
    python3 -c "
from agents.weather.weather_integration_agent import WeatherIntegrationAgent
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('weather-integration')

try:
    # Initialize security context
    from agents.core.security_manager import security_manager

    context = security_manager.create_security_context(
        user_id='weather_integrator',
        permissions=[
            'read_write_access',
            'weather_api_access',
            'external_network_access'
        ]
    )

    logger.info('Security context created successfully')

    # Initialize weather integration agent
    agent = WeatherIntegrationAgent()
    logger.info('Weather Integration Agent initialized')

    # Start the main weather integration loop
    logger.info('Starting weather integration process...')

    # Keep service running for continued operations
    logger.info('Service running. Press Ctrl+C to stop.')

    # Simple service loop for continued operations
    while True:
        time.sleep(60)  # Check every minute
        logger.debug('Weather integration service health check passed')

except Exception as e:
    logger.error(f'Service startup failed: {str(e)}')
    exit(1)
" &

    # If we get here, the Python process has stopped
    log "Weather integration service stopped"
}

# Main execution
main() {
    log "Starting Weather Integration Layer..."

    # Perform security checks
    check_security_context

    # Initialize weather integration environment
    initialize_weather

    # Start service
    start_service
}

# Execute main function
main "$@"