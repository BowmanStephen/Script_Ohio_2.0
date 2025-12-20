#!/bin/bash

set -euo pipefail

# Security orchestrator entrypoint script
# Provides hardened security environment and validation

# Security checks
security_pre_check() {
    echo "🔒 Running security pre-checks..."

    # Check if running as non-root
    if [[ $EUID -eq 0 ]]; then
        echo "❌ ERROR: Container running as root - this is not allowed"
        exit 1
    fi

    # Check if secrets are mounted
    if [[ ! -f "/run/secrets/cfbd_api_key" ]]; then
        echo "❌ ERROR: CFBD API key secret not found"
        exit 1
    fi

    # Validate API key format
    if ! grep -q '^[A-Za-z0-9/+=]*$' /run/secrets/cfbd_api_key; then
        echo "❌ ERROR: Invalid API key format"
        exit 1
    fi

    echo "✅ Security pre-checks passed"
}

# Initialize security orchestrator
init_security_orchestrator() {
    echo "🚀 Initializing Security Orchestrator..."

    # Set security environment
    export AGENT_TYPE="security_orchestrator"
    export SECURITY_LEVEL="high"
    export LOG_LEVEL="info"
    export CONTAINER_ID=$(hostname)
    export STARTUP_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

    # Initialize secure directory structure
    mkdir -p /app/security/audit
    mkdir -p /app/security/certs
    mkdir -p /app/security/policies

    echo "✅ Security Orchestrator initialized"
}

# Health check for container
health_check() {
    echo "🏥 Security Orchestrator health check..."

    # Check if main process is running
    if pgrep -f "security_orchestrator.py" > /dev/null; then
        echo "✅ Security orchestrator process is running"
        exit 0
    else
        echo "❌ Security orchestrator process is not running"
        exit 1
    fi
}

# Main orchestration function
orchestrate() {
    echo "🎯 Starting Security Orchestrator main process..."

    # Start security monitoring
    python3 -c "
import sys
import os
import logging
import json
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('security_orchestrator')

def main():
    logger.info('🔒 Security Orchestrator starting...')

    # Import and initialize the security orchestrator
    try:
        from agents.security_orchestrator import security_orchestrator

        # Run continuous security monitoring
        while True:
            try:
                # Monitor system security
                status = security_orchestrator._monitor_security({}, {})
                logger.info(f'Security status: {status}')

                # Sleep for monitoring interval
                time.sleep(30)

            except Exception as e:
                logger.error(f'Security monitoring error: {e}')
                time.sleep(60)  # Wait longer on error

    except ImportError as e:
        logger.error(f'Failed to import security orchestrator: {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info('Security Orchestrator shutting down...')
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
" &

    # Monitor the main process
    wait
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up Security Orchestrator..."

    # Archive security logs
    if [[ -d "/app/security/audit" ]]; then
        tar -czf "/app/security/audit/archive_$(date +%Y%m%d_%H%M%S).tar.gz" /app/security/audit/*.log 2>/dev/null || true
    fi

    echo "✅ Cleanup completed"
}

# Signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
case "${1:-orchestrate}" in
    "health-check")
        health_check
        ;;
    "init")
        security_pre_check
        init_security_orchestrator
        ;;
    "orchestrate")
        security_pre_check
        init_security_orchestrator
        orchestrate
        ;;
    *)
        echo "Usage: $0 {health-check|init|orchestrate}"
        exit 1
        ;;
esac