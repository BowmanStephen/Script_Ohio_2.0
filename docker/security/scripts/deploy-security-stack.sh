#!/bin/bash
# Comprehensive deployment script for the Advanced Agentic Architecture Security Stack
# Deploys all 15+ containers across 6 security tiers with proper orchestration

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEPLOYMENT: $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log "ERROR: Docker not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log "ERROR: Docker daemon not running"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log "ERROR: Docker Compose not installed"
        exit 1
    fi

    # Check if required files exist
    local required_files=(
        "docker-compose.security.yml"
        "../security-policies.json"
        "health-check.sh"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log "ERROR: Required file $file not found"
            exit 1
        fi
    done

    log "Prerequisites check completed"
}

# Function to create necessary directories
create_directories() {
    log "Creating necessary directories..."

    local directories=(
        "../logs/meta"
        "../logs/planning"
        "../logs/workflow"
        "../logs/risk"
        "../logs/data"
        "../logs/validation"
        "../logs/features"
        "../logs/weather"
        "../logs/models"
        "../logs/analytics"
        "../logs/bowl"
        "../logs/qa"
        "../logs/human"
        "../data/raw"
        "../data/processed"
        "../data/validation"
        "../data/features"
        "../data/weather"
        "../data/bowl-games"
        "../data/predictions"
        "../data/human-reviews"
        "../data/workflows"
        "../data/communication"
        "../data/plans"
        "../data/risk-assessment"
        "../cache/cfbd"
        "../cache/validation"
        "../cache/features"
        "../cache/weather"
        "../cache/bowl"
        "../cache/models"
        "../cache/analytics"
        "../reports"
        "../reports/validation"
        "../reports/human"
        "../reports/bowl"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        chmod 755 "$dir"
        log "Created directory: $dir"
    done

    log "Directory structure created"
}

# Function to set proper permissions
set_permissions() {
    log "Setting proper permissions..."

    # Set ownership for logs directories
    find ../logs -type d -exec chmod 755 {} \;
    find ../logs -type f -exec chmod 644 {} \;

    # Set ownership for data directories
    find ../data -type d -exec chmod 755 {} \;
    find ../data -type f -exec chmod 644 {} \;

    # Set ownership for cache directories
    find ../cache -type d -exec chmod 755 {} \;
    find ../cache -type f -exec chmod 644 {} \;

    # Set ownership for reports directories
    find ../reports -type d -exec chmod 755 {} \;
    find ../reports -type f -exec chmod 644 {} \;

    log "Permissions set successfully"
}

# Function to create Docker networks
create_networks() {
    log "Creating Docker networks..."

    local networks=(
        "orchestration-network:172.20.0.0/16"
        "data-network:172.21.0.0/16"
        "analytics-network:172.22.0.0/16"
        "communication-network:172.23.0.0/16"
        "qa-network:172.24.0.0/16"
        "audit-network:172.25.0.0/16"
        "external-network"
        "human-interface"
        "cfbd-network"
    )

    for network_config in "${networks[@]}"; do
        local network_name=$(echo "$network_config" | cut -d':' -f1)
        local subnet=$(echo "$network_config" | cut -d':' -f2)

        if [ -n "$subnet" ]; then
            # Create internal network with subnet
            if ! docker network inspect "$network_name" &> /dev/null; then
                docker network create --driver bridge --internal --subnet="$subnet" "$network_name"
                log "Created internal network: $network_name ($subnet)"
            else
                log "Network already exists: $network_name"
            fi
        else
            # Create external network
            if ! docker network inspect "$network_name" &> /dev/null; then
                docker network create --driver bridge --external "$network_name" 2>/dev/null || {
                    docker network create --driver bridge "$network_name"
                    log "Created network: $network_name"
                }
            else
                log "Network already exists: $network_name"
            fi
        fi
    done

    log "Docker networks created"
}

# Function to deploy security stack
deploy_security_stack() {
    log "Deploying Advanced Agentic Architecture Security Stack..."

    # Change to the correct directory
    cd "$(dirname "$0")"

    # Deploy using Docker Compose
    docker-compose -f docker-compose.security.yml --project-name cfbd-security up -d

    if [ $? -eq 0 ]; then
        log "Security stack deployed successfully"
    else
        log "ERROR: Failed to deploy security stack"
        exit 1
    fi
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."

    # Wait for containers to start
    log "Waiting for containers to initialize..."
    sleep 30

    # Check container status
    local running_containers=$(docker-compose -f docker-compose.security.yml --project-name cfbd-security ps -q | wc -l)
    local total_containers=$(docker-compose -f docker-compose.security.yml --project-name cfbd-security config --services | wc -l)

    log "Running containers: $running_containers/$total_containers"

    if [ "$running_containers" -eq 0 ]; then
        log "ERROR: No containers are running"
        docker-compose -f docker-compose.security.yml --project-name cfbd-security logs
        exit 1
    fi

    # Check health status
    local healthy_containers=$(docker-compose -f docker-compose.security.yml --project-name cfbd-security ps --format "table {{.Service}}\t{{.Status}}" | grep "healthy" | wc -l)
    log "Healthy containers: $healthy_containers"

    # Show container status
    log "Container status:"
    docker-compose -f docker-compose.security.yml --project-name cfbd-security ps

    log "Deployment verification completed"
}

# Function to show deployment information
show_deployment_info() {
    log "Deployment Information"
    log "====================="
    log "Security Stack deployed with $total_containers containers across 6 security tiers"
    log ""
    log "Security Tiers:"
    log "  Tier 1 (Meta): meta-orchestration (Port 8000)"
    log "  Tier 2 (Planning): planning-coordinator, workflow-coordinator, risk-assessment-agent"
    log "  Tier 3 (Data): cfbd-data-ingestion, data-validation-agent, feature-engineering-agent, weather-integration-agent"
    log "  Tier 4 (Analytics): model-execution-agent, advanced-analytics-agent, bowl-games-specialist"
    log "  Tier 5 (QA): data-quality-assurance, prediction-validator-agent, human-review-coordinator"
    log ""
    log "Networks:"
    log "  orchestration-network: 172.20.0.0/16 (internal)"
    log "  data-network: 172.21.0.0/16 (internal)"
    log "  analytics-network: 172.22.0.0/16 (internal)"
    log "  communication-network: 172.23.0.0/16 (internal)"
    log "  qa-network: 172.24.0.0/16 (internal)"
    log "  audit-network: 172.25.0.0/16 (internal)"
    log "  external-network: External connectivity"
    log "  cfbd-network: CFBD API access"
    log ""
    log "Management Commands:"
    log "  View logs: docker-compose -f docker-compose.security.yml --project-name cfbd-security logs -f [service-name]"
    log "  Stop stack: docker-compose -f docker-compose.security.yml --project-name cfbd-security down"
    log "  Restart service: docker-compose -f docker-compose.security.yml --project-name cfbd-security restart [service-name]"
    log ""
    log "Health Monitoring:"
    log "  All containers include health checks running every 30 seconds"
    log "  Logs are stored in ../logs/[service-name]/ directories"
    log "  Security audit logs are stored in ../logs/audit/"
}

# Function to show next steps
show_next_steps() {
    log "Next Steps"
    log "=========="
    log "1. Verify all containers are healthy: watch docker-compose -f docker-compose.security.yml --project-name cfbd-security ps"
    log "2. Check logs for any issues: docker-compose -f docker-compose.security.yml --project-name cfbd-security logs -f"
    log "3. Access services via their respective ports (see deployment info above)"
    log "4. Configure API keys and secrets as needed"
    log "5. Begin Phase 2: Agent Development - 6-tier specialized agent system"
    log ""
    log "Security Considerations:"
    log "  - All containers run as non-root users"
    log "  - Capabilities are limited to minimum required"
    log "  - Security contexts are enforced via AppArmor and Seccomp"
    log "  - Network isolation is implemented with dedicated subnets"
    log "  - Comprehensive audit logging is enabled"
}

# Main deployment function
main() {
    local action=${1:-"deploy"}

    case "$action" in
        "deploy")
            log "Starting deployment of Advanced Agentic Architecture Security Stack..."
            check_prerequisites
            create_directories
            set_permissions
            create_networks
            deploy_security_stack
            verify_deployment
            show_deployment_info
            show_next_steps
            log "Deployment completed successfully!"
            ;;
        "verify")
            verify_deployment
            ;;
        "stop")
            log "Stopping security stack..."
            docker-compose -f docker-compose.security.yml --project-name cfbd-security down
            log "Security stack stopped"
            ;;
        "restart")
            log "Restarting security stack..."
            docker-compose -f docker-compose.security.yml --project-name cfbd-security restart
            verify_deployment
            ;;
        "logs")
            local service=${2:-""}
            if [ -n "$service" ]; then
                docker-compose -f docker-compose.security.yml --project-name cfbd-security logs -f "$service"
            else
                docker-compose -f docker-compose.security.yml --project-name cfbd-security logs -f
            fi
            ;;
        "status")
            docker-compose -f docker-compose.security.yml --project-name cfbd-security ps
            ;;
        *)
            echo "Usage: $0 {deploy|verify|stop|restart|logs [service]|status}"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"