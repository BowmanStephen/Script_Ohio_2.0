#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}
VERSION=${VERSION:-"latest"}
AGENT_LIST_FILE="containers/agents/agent-list.txt"
PUSH_IMAGES=${PUSH_IMAGES:-"false"}

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to build agent image
build_agent_image() {
    local agent_name=$1
    local agent_class=$2
    local dockerfile=$3

    log "Building image for agent: ${agent_name}"

    # Build arguments
    build_args=(
        "--build-arg" "AGENT_NAME=${agent_name}"
        "--build-arg" "AGENT_CLASS=${agent_class}"
        "--build-arg" "AGENT_INSTANCE=${agent_class}"
    )

    # Build image
    if docker build "${build_args[@]}" \
        -f "${dockerfile}" \
        -t "${REGISTRY}/script-ohio/${agent_name}:${VERSION}" \
        -t "${REGISTRY}/script-ohio/${agent_name}:dev" \
        .; then
        log "Successfully built ${agent_name}:${VERSION}"

        # Push to registry if specified
        if [[ "$PUSH_IMAGES" == "true" ]]; then
            log "Pushing ${agent_name}:${VERSION} to registry..."
            if docker push "${REGISTRY}/script-ohio/${agent_name}:${VERSION}" && \
               docker push "${REGISTRY}/script-ohio/${agent_name}:dev"; then
                log "Successfully pushed ${agent_name}"
            else
                log_error "Failed to push ${agent_name}"
                return 1
            fi
        fi
    else
        log_error "Failed to build ${agent_name}"
        return 1
    fi
}

# Function to create agent list
create_agent_list() {
    log "Creating agent list file..."
    cat > "$AGENT_LIST_FILE" << 'EOF'
# Agent configuration file
# Format: agent_name:agent_class:dockerfile_path
# Tier 1: Meta Layer
meta-agent:meta_agent:containers/agents/Dockerfile.meta

# Tier 2: Orchestrator Layer
orchestration-agent:orchestration_agent:containers/agents/Dockerfile.agent
analytics-orchestrator:analytics_orchestrator:containers/agents/Dockerfile.agent
project-management-agent:project_management_agent:containers/agents/Dockerfile.agent
documentation-agent:documentation_agent:containers/agents/Dockerfile.agent

# Tier 3: Specialist Agents
cfbd-integration-agent:cfbd_integration_agent:containers/agents/Dockerfile.agent
model-execution-engine:model_execution_engine:containers/agents/Dockerfile.agent
insight-generator-agent:insight_generator_agent:containers/agents/Dockerfile.agent
weekly-matchup-analysis:weekly_matchup_analysis_agent:containers/agents/Dockerfile.agent
weekly-prediction-generation:weekly_prediction_generation_agent:containers/agents/Dockerfile.agent
performance-monitor-agent:performance_monitor_agent:containers/agents/Dockerfile.agent
validation-agent:validation_agent:containers/agents/Dockerfile.agent
learning-navigator-agent:learning_navigator_agent:containers/agents/Dockerfile.agent
ai-assistant-agent:ai_assistant_agent:containers/agents/Dockerfile.agent
weekly-validation-agent:weekly_model_validation_agent:containers/agents/Dockerfile.agent
EOF
    log "Agent list file created at $AGENT_LIST_FILE"
}

# Function to check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi

    # Check if agent files exist
    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt not found"
        exit 1
    fi

    # Check if containers directory exists
    if [[ ! -d "containers/agents" ]]; then
        log_error "containers/agents directory not found"
        exit 1
    fi

    # Check if Dockerfiles exist
    if [[ ! -f "containers/agents/Dockerfile.agent" ]]; then
        log_error "Dockerfile.agent not found"
        exit 1
    fi

    if [[ ! -f "containers/agents/Dockerfile.meta" ]]; then
        log_error "Dockerfile.meta not found"
        exit 1
    fi

    log_info "All dependencies found"
}

# Function to build specific agent
build_specific_agent() {
    local agent_pattern=$1

    log "Searching for agent matching pattern: $agent_pattern"

    # Find matching agents in the list
    local found=false
    while IFS=':' read -r agent_name agent_class dockerfile_path; do
        # Skip comments and empty lines
        [[ "$agent_name" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$agent_name" ]] && continue

        # Check if agent matches pattern
        if [[ "$agent_name" == *"$agent_pattern"* ]]; then
            found=true

            # Check if agent file exists
            if [[ ! -f "agents/${agent_class}.py" ]]; then
                log_warning "Agent file not found: agents/${agent_class}.py, skipping..."
                continue
            fi

            log_info "Found matching agent: $agent_name"
            build_agent_image "$agent_name" "$agent_class" "$dockerfile_path"
        fi
    done < "$AGENT_LIST_FILE"

    if [[ "$found" == "false" ]]; then
        log_error "No agents found matching pattern: $agent_pattern"
        return 1
    fi
}

# Function to display built images
display_images() {
    log "\nBuilt images:"
    docker images | grep "script-ohio" | grep -E "(dev|$VERSION)" | while read -r line; do
        echo "  - $line"
    done
}

# Function to cleanup old images
cleanup_old_images() {
    log "Cleaning up old images..."

    # Remove old dev images (keep latest 5)
    local old_images=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "script-ohio" | grep ":dev" | sort -r | tail -n +6)

    if [[ -n "$old_images" ]]; then
        echo "$old_images" | xargs -r docker rmi -f
        log "Cleaned up old dev images"
    fi

    # Remove dangling images
    docker image prune -f
}

# Main build process
main() {
    log "Script Ohio 2.0 Agent Image Build Process"
    log "========================================="
    log "Registry: ${REGISTRY}"
    log "Version: ${VERSION}"
    log "Push Images: ${PUSH_IMAGES}"

    # Check dependencies
    check_dependencies

    # Parse command line arguments
    case "${1:-"all"}" in
        "all")
            # Create agent list file if it doesn't exist
            if [[ ! -f "$AGENT_LIST_FILE" ]]; then
                create_agent_list
            fi

            # Count total agents to build
            local total_agents=$(grep -v "^#" "$AGENT_LIST_FILE" | grep -v "^$" | wc -l)
            log "Building $total_agents agent images..."

            # Read agent list and build images
            local built=0
            local failed=0
            while IFS=':' read -r agent_name agent_class dockerfile_path; do
                # Skip comments and empty lines
                [[ "$agent_name" =~ ^[[:space:]]*# ]] && continue
                [[ -z "$agent_name" ]] && continue

                # Check if agent file exists
                if [[ ! -f "agents/${agent_class}.py" ]]; then
                    log_warning "Agent file not found: agents/${agent_class}.py, skipping..."
                    continue
                fi

                if build_agent_image "$agent_name" "$agent_class" "$dockerfile_path"; then
                    ((built++))
                else
                    ((failed++))
                fi

            done < "$AGENT_LIST_FILE"

            log "\nBuild Summary:"
            log "  Total: $total_agents"
            log "  Built: $built"
            log "  Failed: $failed"

            if [[ $failed -gt 0 ]]; then
                log_error "Some images failed to build"
                exit 1
            fi
            ;;
        "list")
            # List all available agents
            if [[ ! -f "$AGENT_LIST_FILE" ]]; then
                create_agent_list
            fi

            log "Available agents:"
            grep -v "^#" "$AGENT_LIST_FILE" | grep -v "^$" | while IFS=':' read -r agent_name agent_class dockerfile_path; do
                echo "  - $agent_name ($agent_class)"
            done
            ;;
        "agent")
            # Build specific agent
            if [[ -z "$2" ]]; then
                log_error "Please specify an agent name or pattern"
                log "Usage: $0 agent <agent_name_or_pattern>"
                exit 1
            fi

            # Create agent list if needed
            if [[ ! -f "$AGENT_LIST_FILE" ]]; then
                create_agent_list
            fi

            build_specific_agent "$2"
            ;;
        "cleanup")
            cleanup_old_images
            ;;
        "--help"|"-h")
            echo "Usage: $0 [COMMAND] [OPTIONS]"
            echo ""
            echo "Commands:"
            echo "  all [default]  Build all agent images"
            echo "  list           List all available agents"
            echo "  agent <name>   Build specific agent (supports pattern matching)"
            echo "  cleanup        Clean up old images"
            echo ""
            echo "Options:"
            echo "  --registry REGISTRY    Docker registry to use (default: localhost:5000)"
            echo "  --version VERSION      Version tag (default: latest)"
            echo "  --push                 Push images to registry after building"
            echo "  --help, -h             Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DOCKER_REGISTRY        Docker registry URL"
            echo "  VERSION                Image version tag"
            echo "  PUSH_IMAGES            Set to 'true' to push images"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Build all images"
            echo "  $0 --registry my-registry.com        # Build with custom registry"
            echo "  $0 --version v1.0.0 --push         # Build version 1.0.0 and push"
            echo "  $0 agent meta-agent                    # Build specific agent"
            echo "  $0 agent meta                          # Build agents matching pattern"
            echo "  $0 list                               # List all agents"
            exit 0
            ;;
        *)
            log_error "Unknown command: $1"
            log "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac

    # Display built images
    display_images

    log "Build process completed successfully!"
}

# Parse command line arguments for options
while [[ $# -gt 0 ]]; do
    case $1 in
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --push)
            PUSH_IMAGES="true"
            shift
            ;;
        --help|-h)
            main --help
            ;;
        -*)
            log_error "Unknown option: $1"
            exit 1
            ;;
        *)
            # Not an option, break to pass to main
            break
            ;;
    esac
done

# Execute main function with remaining arguments
main "$@"