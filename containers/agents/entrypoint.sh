#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${AGENT_NAME:-agent}] $1"
}

# Function to check required environment
check_env() {
    local required_vars=("$@")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log "ERROR: Required environment variable $var is not set"
            exit 1
        fi
    done
}

# Function to wait for dependencies
wait_for_dependencies() {
    if [[ -n "${DEPENDENCIES}" ]]; then
        IFS=',' read -ra DEPS <<< "$DEPENDENCIES"
        for dep in "${DEPS[@]}"; do
            log "Waiting for dependency: $dep"
            # Extract host and port
            local host=$(echo "$dep" | cut -d':' -f1)
            local port=$(echo "$dep" | cut -d':' -f2)

            # Wait for service to be available
            until nc -z "$host" "$port"; do
                log "Waiting for $host:$port..."
                sleep 2
            done
            log "Dependency $host:$port is ready"
        done
    fi
}

# Function to initialize agent
initialize_agent() {
    log "Initializing ${AGENT_TYPE} agent..."

    # Initialize agent-specific resources
    case "${AGENT_TYPE}" in
        "governance")
            log "Initializing governance agent..."
            # Try to initialize registry, but don't fail if it doesn't exist
            python3 -c "
import sys
try:
    from agents.meta_agent import meta_agent
    result = meta_agent._initialize_registry({}, {})
    log('Registry initialized: ' + str(result))
except AttributeError:
    log('Registry initialization method not found, continuing...')
except Exception as e:
    log(f'Registry initialization failed: {e}')
    sys.exit(0)
" || log "Registry initialization completed with warnings"
            ;;
        "orchestrator")
            log "Initializing orchestrator agent..."
            # Try to initialize connections
            python3 -c "
import sys
try:
    from agents.${AGENT_CLASS} import ${AGENT_INSTANCE}
    agent = ${AGENT_INSTANCE}()
    if hasattr(agent, '_initialize_connections'):
        agent._initialize_connections({}, {})
        log('Connections initialized')
    else:
        log('Connection initialization method not found, continuing...')
except Exception as e:
    log(f'Connection initialization failed: {e}')
    sys.exit(0)
" || log "Connection initialization completed with warnings"
            ;;
        "specialist")
            log "Initializing specialist agent..."
            # Try to load dependencies
            python3 -c "
import sys
try:
    from agents.${AGENT_CLASS} import ${AGENT_INSTANCE}
    agent = ${AGENT_INSTANCE}()
    if hasattr(agent, '_load_dependencies'):
        agent._load_dependencies({}, {})
        log('Dependencies loaded')
    else:
        log('Dependency loading method not found, continuing...')
except Exception as e:
    log(f'Dependency loading failed: {e}')
    sys.exit(0)
" || log "Dependency loading completed with warnings"
            ;;
    esac

    log "Agent initialization complete"
}

# Function to run agent
run_agent() {
    log "Starting ${AGENT_NAME} agent on port ${AGENT_PORT}..."

    # Set up signal handlers
    trap 'log "Received shutdown signal"; exit 0' SIGTERM SIGINT

    # Start agent
    case "$1" in
        "run")
            log "Starting agent in API mode..."
            python3 -c "
import os
import sys
from agents.${AGENT_CLASS} import ${AGENT_INSTANCE}
import asyncio
from datetime import datetime

# Create a simple health check server
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'agent': '${AGENT_NAME}',
                'timestamp': datetime.utcnow().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass

# Start health check server
import threading
def start_health_server():
    server = HTTPServer(('0.0.0.0', ${AGENT_PORT}), HealthHandler)
    log(f'Health server started on port ${AGENT_PORT}')
    server.serve_forever()

# Start health server in background
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# Initialize and run the agent
try:
    agent = ${AGENT_INSTANCE}()

    # Start message bus if available
    if hasattr(agent, 'message_bus') and '${REDIS_URL}':
        import asyncio
        log('Starting message bus...')
        try:
            asyncio.get_event_loop().run_until_complete(agent.message_bus.connect())
            log('Message bus connected')
        except Exception as e:
            log(f'Message bus connection failed: {e}')

    # Run agent main loop
    if hasattr(agent, '_run_worker_mode'):
        log('Running agent in worker mode...')
        asyncio.get_event_loop().run_until_complete(agent._run_worker_mode())
    else:
        log('Agent running, health endpoint available on port ${AGENT_PORT}')
        # Keep container alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            log('Shutting down...')

except Exception as e:
    log(f'Agent startup failed: {e}')
    sys.exit(1)
"
            ;;
        "worker")
            log "Starting agent in worker mode..."
            python3 -c "
from agents.${AGENT_CLASS} import ${AGENT_INSTANCE}
import asyncio

agent = ${AGENT_INSTANCE}()
try:
    asyncio.run(agent._run_worker_mode())
except Exception as e:
    log(f'Worker mode failed: {e}')
"
            ;;
        "test")
            log "Running agent test..."
            python3 -c "
from agents.${AGENT_CLASS} import ${AGENT_INSTANCE}
try:
    agent = ${AGENT_INSTANCE}()
    log(f'Agent {agent.__class__.__name__} created successfully')

    # Test basic functionality
    if hasattr(agent, '_define_capabilities'):
        caps = agent._define_capabilities()
        log(f'Agent capabilities: {len(caps)} defined')

    log('Agent test completed successfully')
except Exception as e:
    log(f'Agent test failed: {e}')
    import traceback
    traceback.print_exc()
"
            ;;
        *)
            log "Unknown command: $1"
            log "Available commands: run, worker, test"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    log "Container starting for ${AGENT_NAME}..."
    log "Agent Class: ${AGENT_CLASS}"
    log "Agent Type: ${AGENT_TYPE}"
    log "Port: ${AGENT_PORT}"
    log "Environment: ${ENVIRONMENT:-development}"

    # Check required environment variables
    check_env "AGENT_CLASS" "AGENT_INSTANCE" "AGENT_PORT" "AGENT_TYPE"

    # Wait for dependencies
    wait_for_dependencies

    # Initialize agent
    initialize_agent

    # Run agent
    run_agent "$@"
}

# Execute main function
main "$@"