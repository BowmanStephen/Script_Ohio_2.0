#!/bin/bash
# Universal health check script for all agent containers
# Performs comprehensive health monitoring and security validation

set -e

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] HEALTH-CHECK: $1"
}

# Function to perform basic health checks
basic_health_check() {
    log "Performing basic health checks..."

    # Check if Python is accessible
    if ! command -v python3 &> /dev/null; then
        log "ERROR: Python3 not found"
        exit 1
    fi

    # Check if required directories exist
    for dir in /app/logs; do
        if [ ! -d "$dir" ]; then
            log "ERROR: Required directory $dir not found"
            exit 1
        fi
    done

    # Check memory usage
    local mem_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        log "WARNING: High memory usage: ${mem_usage}%"
    fi

    # Check disk usage
    local disk_usage=$(df /app | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        log "WARNING: High disk usage: ${disk_usage}%"
    fi

    log "Basic health checks passed"
}

# Function to perform security validation
security_validation() {
    log "Performing security validation..."

    # Check if running as non-root user
    if [ "$(id -u)" -eq 0 ]; then
        log "ERROR: Running as root user (security violation)"
        exit 1
    fi

    # Check if security policies file is readable
    if [ ! -f "/etc/agent-security/security-policies.json" ]; then
        log "WARNING: Security policies file not accessible"
    fi

    # Check for suspicious processes
    local suspicious_procs=$(ps aux | grep -E "(nc|netcat|bash|sh)" | grep -v grep | wc -l)
    if [ "$suspicious_procs" -gt 0 ]; then
        log "WARNING: Suspicious processes detected: $suspicious_procs"
    fi

    log "Security validation completed"
}

# Function to check service-specific health
service_health_check() {
    local service_type=${1:-"unknown"}
    log "Checking $service_type service health..."

    # Check if service-specific Python modules are accessible
    case "$service_type" in
        "meta-orchestration")
            python3 -c "from agents.orchestration.chief_architect_agent import ChiefArchitectAgent; print('Meta orchestration OK')" 2>/dev/null || {
                log "ERROR: Meta orchestration modules not accessible"
                exit 1
            }
            ;;
        "planning-coordination")
            python3 -c "from agents.planning.planning_coordinator_agent import PlanningCoordinatorAgent; print('Planning coordination OK')" 2>/dev/null || {
                log "WARNING: Planning coordination modules not accessible"
            }
            ;;
        "workflow-coordination")
            python3 -c "from agents.workflow.workflow_coordinator_agent import WorkflowCoordinatorAgent; print('Workflow coordination OK')" 2>/dev/null || {
                log "WARNING: Workflow coordination modules not accessible"
            }
            ;;
        "cfbd-data-ingestion")
            python3 -c "from agents.data.cfbd_integration_agent import CFBDIntegrationAgent; print('CFBD integration OK')" 2>/dev/null || {
                log "WARNING: CFBD integration modules not accessible"
            }
            ;;
        "data-validation")
            python3 -c "from agents.validation.data_validation_agent import DataValidationAgent; print('Data validation OK')" 2>/dev/null || {
                log "WARNING: Data validation modules not accessible"
            }
            ;;
        "feature-engineering")
            python3 -c "from agents.features.feature_engineering_agent import FeatureEngineeringAgent; print('Feature engineering OK')" 2>/dev/null || {
                log "WARNING: Feature engineering modules not accessible"
            }
            ;;
        "model-execution")
            python3 -c "from agents.analytics.model_execution_agent import ModelExecutionAgent; print('Model execution OK')" 2>/dev/null || {
                log "WARNING: Model execution modules not accessible"
            }
            ;;
        "advanced-analytics")
            python3 -c "from agents.analytics.advanced_analytics_agent import AdvancedAnalyticsAgent; print('Advanced analytics OK')" 2>/dev/null || {
                log "WARNING: Advanced analytics modules not accessible"
            }
            ;;
        "bowl-games-specialist")
            python3 -c "from agents.bowl.bowl_games_specialist_agent import BowlGamesSpecialistAgent; print('Bowl games specialist OK')" 2>/dev/null || {
                log "WARNING: Bowl games specialist modules not accessible"
            }
            ;;
        "data-quality-assurance")
            python3 -c "from agents.qa.quality_assurance_agent import QualityAssuranceAgent; print('Quality assurance OK')" 2>/dev/null || {
                log "WARNING: Quality assurance modules not accessible"
            }
            ;;
        "human-review-coordinator")
            python3 -c "from agents.human.human_review_coordinator_agent import HumanReviewCoordinatorAgent; print('Human review coordinator OK')" 2>/dev/null || {
                log "WARNING: Human review coordinator modules not accessible"
            }
            ;;
        "risk-assessment")
            python3 -c "from agents.risk.risk_assessment_agent import RiskAssessmentAgent; print('Risk assessment OK')" 2>/dev/null || {
                log "WARNING: Risk assessment modules not accessible"
            }
            ;;
        "weather-integration")
            python3 -c "from agents.weather.weather_integration_agent import WeatherIntegrationAgent; print('Weather integration OK')" 2>/dev/null || {
                log "WARNING: Weather integration modules not accessible"
            }
            ;;
        *)
            log "INFO: Unknown service type $service_type, skipping module check"
            ;;
    esac

    log "$service_type service health check completed"
}

# Function to check network connectivity (if applicable)
network_connectivity_check() {
    local service_type=${1:-"unknown"}

    # Only check network for services that require it
    case "$service_type" in
        "cfbd-data-ingestion"|"weather-integration")
            log "Checking network connectivity..."

            # Check DNS resolution
            if ! nslookup google.com &>/dev/null; then
                log "WARNING: DNS resolution failed"
            fi

            # Check external connectivity (with timeout)
            if ! timeout 5 ping -c 1 8.8.8.8 &>/dev/null; then
                log "WARNING: External connectivity limited"
            fi

            log "Network connectivity check completed"
            ;;
    esac
}

# Function to check logging functionality
logging_check() {
    log "Checking logging functionality..."

    # Test write access to log directory
    local test_log_file="/app/logs/health_check_test.log"
    if echo "[$(date '+%Y-%m-%d %H:%M:%S')] HEALTH-CHECK: Logging test successful" > "$test_log_file" 2>/dev/null; then
        rm -f "$test_log_file"
        log "Logging functionality OK"
    else
        log "ERROR: Cannot write to log directory"
        exit 1
    fi
}

# Main health check function
main() {
    local service_type=${1:-"unknown"}

    log "Starting comprehensive health check for $service_type..."

    # Perform all health checks
    basic_health_check
    security_validation
    service_health_check "$service_type"
    network_connectivity_check "$service_type"
    logging_check

    log "Health check completed successfully for $service_type"
    exit 0
}

# Execute main function with service type
main "$@"