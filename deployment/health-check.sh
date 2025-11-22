#!/bin/bash
# Health check script for Script Ohio 2.0 production container

set -e

# Health check endpoint
HEALTH_URL="http://localhost:8000/health"
METRICS_URL="http://localhost:9090/metrics"
TIMEOUT=10
MAX_RETRIES=3

echo "Starting health check for Script Ohio 2.0..."

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local timeout=$2
    local retries=$3

    for i in $(seq 1 $retries); do
        echo "Checking endpoint: $url (attempt $i/$retries)"

        if curl -f -s --max-time $timeout "$url" > /dev/null; then
            echo "✅ Health check passed for $url"
            return 0
        else
            echo "❌ Health check failed for $url (attempt $i/$retries)"
            if [ $i -eq $retries ]; then
                return 1
            fi
            sleep 2
        fi
    done
}

# Function to check disk space
check_disk_space() {
    echo "Checking disk space..."

    # Get available disk space in root
    available_space=$(df / | awk 'NR==2 {print $4}')
    min_space=1048576  # 1GB in KB

    if [ "$available_space" -lt "$min_space" ]; then
        echo "❌ Low disk space: ${available_space}KB available, minimum required: ${min_space}KB"
        return 1
    else
        echo "✅ Disk space check passed: ${available_space}KB available"
        return 0
    fi
}

# Function to check memory usage
check_memory() {
    echo "Checking memory usage..."

    # Get available memory
    available_memory=$(free | awk 'NR==2{printf "%.0f", $7/1024}')
    min_memory=512  # 512MB minimum

    if [ "$available_memory" -lt "$min_memory" ]; then
        echo "❌ Low memory: ${available_memory}MB available, minimum required: ${min_memory}MB"
        return 1
    else
        echo "✅ Memory check passed: ${available_memory}MB available"
        return 0
    fi
}

# Function to check Python process
check_python_process() {
    echo "Checking Python application process..."

    # Check if gunicorn/uvicorn process is running
    if pgrep -f "gunicorn\|uvicorn" > /dev/null; then
        echo "✅ Python process check passed"
        return 0
    else
        echo "❌ Python application process not found"
        return 1
    fi
}

# Function to check critical directories
check_directories() {
    echo "Checking critical directories..."

    local dirs=("/app/logs" "/app/models" "/app/data")

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            echo "❌ Directory not found: $dir"
            return 1
        else
            echo "✅ Directory check passed: $dir"
        fi
    done

    return 0
}

# Function to check configuration
check_configuration() {
    echo "Checking configuration..."

    # Check if required environment variables are set
    local required_vars=("DATABASE_HOST" "REDIS_HOST" "APP_ENV")

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Required environment variable not set: $var"
            return 1
        else
            echo "✅ Configuration check passed: $var=${!var}"
        fi
    done

    return 0
}

# Main health check logic
main() {
    local failed_checks=0

    echo "========================================="
    echo "Script Ohio 2.0 Health Check"
    echo "Timestamp: $(date)"
    echo "========================================="

    # Run all health checks
    if ! check_configuration; then
        ((failed_checks++))
    fi

    if ! check_directories; then
        ((failed_checks++))
    fi

    if ! check_disk_space; then
        ((failed_checks++))
    fi

    if ! check_memory; then
        ((failed_checks++))
    fi

    if ! check_python_process; then
        ((failed_checks++))
    fi

    # Check application endpoints
    if ! check_endpoint "$HEALTH_URL" "$TIMEOUT" "$MAX_RETRIES"; then
        ((failed_checks++))
    fi

    # Check metrics endpoint (optional)
    if curl -f -s --max-time 5 "$METRICS_URL" > /dev/null; then
        echo "✅ Metrics endpoint check passed"
    else
        echo "⚠️  Metrics endpoint check failed (non-critical)"
    fi

    echo "========================================="
    if [ $failed_checks -eq 0 ]; then
        echo "🎉 All health checks passed!"
        echo "Application is healthy and ready to serve traffic."
        exit 0
    else
        echo "💥 Health check failed with $failed_checks failed checks"
        echo "Application is not healthy."
        exit 1
    fi
}

# Run main function
main "$@"