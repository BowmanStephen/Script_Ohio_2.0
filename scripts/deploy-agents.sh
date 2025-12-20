#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-"development"}
COMPOSE_FILE="docker-compose.agents.${ENVIRONMENT}.yml"
PROJECT_NAME="script-ohio-agents"
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-"300"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# Array of core services to check
CORE_SERVICES=(
    "meta-agent:8000"
    "orchestration-agent:8001"
    "analytics-orchestrator:8002"
    "project-management-agent:8003"
    "documentation-agent:8004"
    "redis:6379"
    "postgres:5432"
)

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

log_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Function to display banner
display_banner() {
    echo -e "${CYAN}"
    echo "███████╗██████╗ ██████╗     ██████╗ ██╗   ██╗███████╗████████╗"
    echo "██╔════╝██╔══██╗██╔══██╗    ██╔══██╗██║   ██║██╔════╝╚══██╔══╝"
    echo "███████╗██████╔╝██║  ██║    ██████╔╝██║   ██║█████╗     ██║   "
    echo "╚════██║██╔═══╝ ██║  ██║    ██╔══██╗██║   ██║██╔══╝     ██║   "
    echo "███████║██║     ██████╔╝    ██████╔╝╚██████╔╝███████╗   ██║   "
    echo "╚══════╝╚═╝     ╚═════╝     ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   "
    echo -e "${NC}"
    log "Script Ohio 2.0 Agent Deployment"
    log "Environment: ${ENVIRONMENT}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to check Docker installation
check_docker() {
    if ! command_exists docker; then
        log_error "Docker is not installed"
        log "Please install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        log "Please start Docker daemon"
        exit 1
    fi

    if ! command_exists docker-compose; then
        if ! docker compose version &> /dev/null; then
            log_error "Docker Compose is not installed"
            log "Please install Docker Compose from https://docs.docker.com/compose/install/"
            exit 1
        fi
        # Use newer 'docker compose' syntax
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
}

# Function to check if Docker Compose file exists
check_compose_file() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        log "Available compose files:"
        ls -la docker-compose.agents.*.yml 2>/dev/null || log "  None found"
        exit 1
    fi
    log "Using compose file: $COMPOSE_FILE"
}

# Function to check secrets
check_secrets() {
    local secrets_dir=".secrets"
    local required_secrets=("db_password.txt")

    # Check additional secrets based on environment
    if [[ "$ENVIRONMENT" == "production" ]]; then
        required_secrets+=("grafana_password.txt")
    else
        required_secrets+=("cfbd_api_key.txt")
    fi

    if [[ ! -d "$secrets_dir" ]]; then
        log_error "Secrets directory not found: $secrets_dir"
        log "Creating secrets directory..."
        mkdir -p "$secrets_dir"

        for secret in "${required_secrets[@]}"; do
            log "Please create: $secrets_dir/$secret"
        done

        exit 1
    fi

    local missing_secrets=()
    for secret in "${required_secrets[@]}"; do
        if [[ ! -f "$secrets_dir/$secret" ]]; then
            missing_secrets+=("$secret")
        fi
    done

    if [[ ${#missing_secrets[@]} -gt 0 ]]; then
        log_error "Missing secret files:"
        for secret in "${missing_secrets[@]}"; do
            log_error "  - $secrets_dir/$secret"
        done
        exit 1
    fi

    log_info "All required secrets found"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    check_docker
    check_compose_file
    check_secrets
    log_success "Prerequisites check passed"
}

# Function to start services
start_services() {
    log "Starting agent services..."

    # Pull latest images
    log_info "Pulling latest images..."
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" pull; then
        log_error "Failed to pull images"
        exit 1
    fi

    # Start services
    log_info "Starting containers..."
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d; then
        log_error "Failed to start services"
        exit 1
    fi

    log_success "Services started successfully!"

    # Display service URLs
    display_service_urls
}

# Function to stop services
stop_services() {
    log "Stopping agent services..."

    if $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps -q | grep -q .; then
        if ! $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down; then
            log_error "Failed to stop services"
            exit 1
        fi
    else
        log_info "No services are running"
    fi

    log_success "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    log "Restarting agent services..."

    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart; then
        log_error "Failed to restart services"
        exit 1
    fi

    log_success "Services restarted successfully!"
}

# Function to check service health
check_health() {
    log "Checking service health..."

    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=10
    local elapsed=0
    local all_healthy=false

    while [[ $elapsed -lt $timeout ]]; do
        local healthy_count=0
        local total_count=${#CORE_SERVICES[@]}

        log_info "Health check attempt $((elapsed / interval + 1))/$((timeout / interval))"

        for service in "${CORE_SERVICES[@]}"; do
            local service_name=$(echo "$service" | cut -d':' -f1)
            local port=$(echo "$service" | cut -d':' -f2)

            # Check container status
            if $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps | grep -q "${service_name}.*Up"; then
                # For HTTP services, check health endpoint
                if [[ "$port" =~ ^8[0-9]{3}$ ]]; then
                    if curl -f -s "http://localhost:${port}/health" > /dev/null 2>&1; then
                        log_success "✓ $service_name is healthy"
                        ((healthy_count++))
                    else
                        log_warning "✗ $service_name is not responding on health endpoint"
                    fi
                else
                    # For non-HTTP services (Redis, PostgreSQL)
                    log_success "✓ $service_name is up"
                    ((healthy_count++))
                fi
            else
                log_warning "✗ $service_name is not running"
            fi
        done

        if [[ $healthy_count -eq $total_count ]]; then
            all_healthy=true
            break
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
    done

    if [[ "$all_healthy" == "true" ]]; then
        log_success "All core services are healthy!"
    else
        log_error "Health check timeout. Some services are not healthy."
        log "Check logs with: $0 logs"
        return 1
    fi
}

# Function to show logs
show_logs() {
    local service=${1:-""}

    if [[ -n "$service" ]]; then
        log "Showing logs for: $service"
        $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$service"
    else
        log "Showing logs for all services"
        $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
    fi
}

# Function to show status
show_status() {
    log "Service status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

    # Show resource usage
    log "\nResource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        | grep "$PROJECT_NAME" || log "  No containers running"

    # Try to get agent registry status
    if docker ps | grep -q "meta-agent"; then
        log "\nAgent registry status:"
        docker exec meta-agent python3 -c "
import sys
try:
    from agents.meta_agent import meta_agent
    result = meta_agent._get_registry({}, {})
    print(f'  Registered agents: {len(result.get(\"agents\", []))}')
    for agent in result.get('agents', [])[:5]:  # Show first 5
        print(f'  - {agent.get(\"agent_id\", \"unknown\")}')
    if len(result.get('agents', [])) > 5:
        print(f'  ... and {len(result.get(\"agents\", [])) - 5} more')
except Exception as e:
    print(f'  Error: {e}')
" 2>/dev/null || log "  Unable to fetch agent registry"
    fi
}

# Function to scale services
scale_service() {
    local service=$1
    local replicas=$2

    if [[ -z "$service" || -z "$replicas" ]]; then
        log_error "Usage: $0 scale <service> <replicas>"
        exit 1
    fi

    log "Scaling $service to $replicas replicas..."

    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --scale "$service=$replicas"; then
        log_error "Failed to scale $service"
        exit 1
    fi

    log_success "Scaling complete!"
}

# Function to backup data
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    local volumes=(
        "script-ohio-agents_agent-registry:/data/agent-registry"
        "script-ohio-agents_model-storage:/data/model-storage"
        "script-ohio-agents_data-storage:/data/data-storage"
        "script-ohio-agents_logs:/data/logs"
        "script-ohio-agents_redis-data:/data/redis"
        "script-ohio-agents_postgres-data:/data/postgres"
    )

    log "Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"

    # Backup each volume
    for volume_mapping in "${volumes[@]}"; do
        local volume=${volume_mapping%:*}
        local path=${volume_mapping#*:}

        log "Backing up $volume..."

        if docker run --rm \
            -v "$volume:$path" \
            -v "$(pwd)/$backup_dir":/backup \
            alpine tar czf "/backup/$(basename $volume).tar.gz" -C "$path" . 2>/dev/null; then
            log_success "Backed up $volume"
        else
            log_warning "Failed to backup $volume"
        fi
    done

    # Backup compose configuration
    cp "$COMPOSE_FILE" "$backup_dir/docker-compose.yml"

    log_success "Backup created at $backup_dir"
    log "Size: $(du -sh "$backup_dir" | cut -f1)"
}

# Function to restore data
restore_data() {
    local backup_dir=$1

    if [[ -z "$backup_dir" ]]; then
        log_error "Usage: $0 restore <backup_directory>"
        exit 1
    fi

    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory not found: $backup_dir"
        exit 1
    fi

    log "Restoring from backup: $backup_dir"

    # Stop services first
    stop_services

    # Restore each volume
    for backup_file in "$backup_dir"/*.tar.gz; do
        if [[ -f "$backup_file" ]]; then
            local volume_name=$(basename "$backup_file" .tar.gz)
            local volume="script-ohio-agents_$volume_name"

            log "Restoring $volume..."

            # Create volume if it doesn't exist
            docker volume create "$volume" 2>/dev/null || true

            if docker run --rm \
                -v "$volume":/data \
                -v "$backup_dir":/backup \
                alpine tar xzf "/backup/$volume_name.tar.gz" -C /data 2>/dev/null; then
                log_success "Restored $volume"
            else
                log_warning "Failed to restore $volume"
            fi
        fi
    done

    log_success "Restore completed!"
    log "Run '$0 start' to restart services"
}

# Function to display service URLs
display_service_urls() {
    log "\nService URLs:"
    log "  Meta Agent:         http://localhost:8000/health"
    log "  Orchestration:       http://localhost:8001/health"
    log "  Analytics:           http://localhost:8002/health"
    log "  Project Management:  http://localhost:8003/health"
    log "  Documentation:       http://localhost:8004/health"
    log "  CFBD Integration:    http://localhost:8010/health"
    log "  Model Execution:     http://localhost:8011/health"
    log "  Insight Generator:   http://localhost:8012/health"

    if [[ "$ENVIRONMENT" == "production" ]]; then
        log "  Prometheus:         http://localhost:9090"
        log "  Grafana:            http://localhost:3000"
    fi

    log "\nRedis:               localhost:6379"
    log "PostgreSQL:           localhost:5432"
}

# Function to cleanup
cleanup() {
    log "Cleaning up..."

    # Remove stopped containers
    local stopped_containers=$(docker ps -a --filter "name=$PROJECT_NAME" -q)
    if [[ -n "$stopped_containers" ]]; then
        docker rm $stopped_containers
        log "Removed stopped containers"
    fi

    # Remove unused images
    docker image prune -f
    log "Removed unused images"

    # Remove unused volumes (be careful with this!)
    read -p "Remove unused data volumes? This cannot be undone! [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
        log "Removed unused volumes"
    fi

    log_success "Cleanup completed!"
}

# Main execution
main() {
    display_banner

    case "$1" in
        start)
            check_prerequisites
            start_services
            if [[ "$2" != "--no-health-check" ]]; then
                check_health
            fi
            ;;
        stop)
            check_compose_file
            stop_services
            ;;
        restart)
            check_compose_file
            restart_services
            check_health
            ;;
        status)
            check_compose_file
            show_status
            ;;
        logs)
            check_compose_file
            show_logs "$2"
            ;;
        health)
            check_compose_file
            check_health
            ;;
        scale)
            check_compose_file
            scale_service "$2" "$3"
            ;;
        backup)
            check_compose_file
            backup_data
            ;;
        restore)
            restore_data "$2"
            ;;
        cleanup)
            cleanup
            ;;
        --help|-h)
            echo "Usage: $0 {start|stop|restart|status|logs|health|scale|backup|restore|cleanup}"
            echo ""
            echo "Commands:"
            echo "  start [--no-health-check]  - Start all agent services"
            echo "  stop                       - Stop all agent services"
            echo "  restart                    - Restart all agent services"
            echo "  status                     - Show service status and resource usage"
            echo "  logs [service]             - Show logs (optionally specify service name)"
            echo "  health                     - Check service health"
            echo "  scale <service> <count>    - Scale a service"
            echo "  backup                     - Backup all data volumes"
            echo "  restore <directory>        - Restore from backup directory"
            echo "  cleanup                    - Clean up unused containers, images, and volumes"
            echo ""
            echo "Environment variables:"
            echo "  ENVIRONMENT                - Deployment environment (default: development)"
            echo "  HEALTH_CHECK_TIMEOUT       - Health check timeout in seconds (default: 300)"
            echo "  LOG_LEVEL                  - Log level (default: info)"
            echo ""
            echo "Examples:"
            echo "  $0 start                    # Start development environment"
            echo "  ENVIRONMENT=production $0 start  # Start production environment"
            echo "  $0 scale cfbd-integration-agent 3   # Scale CFBD agent to 3 replicas"
            echo "  $0 logs meta-agent         # Show logs for meta agent only"
            echo "  $0 status                   # Show detailed status"
            exit 0
            ;;
        *)
            log_error "Unknown command: $1"
            log "Use '$0 --help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"