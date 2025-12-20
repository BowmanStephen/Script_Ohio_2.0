# Advanced Agentic Architecture - Docker Security Stack

This directory contains the complete Docker security configuration for the 6-tier advanced agentic architecture implementing comprehensive sandboxing and security best practices.

## Architecture Overview

The security stack implements a **6-tier specialized agent system** with multi-layer sandboxing:

### Tier 1: Meta Orchestration Layer (Admin Level Security)
- **Container**: `meta-orchestration` (Port 8000)
- **User**: 1000:1000 (Non-root with limited privileges)
- **Capabilities**: CHOWN, SETGID, SETUID
- **Security**: Top Secret level, comprehensive audit logging

### Tier 2: Planning & Coordination Layer (High Security)
- **Containers**:
  - `planning-coordinator` (Port 8300) - Read-only execution
  - `workflow-coordinator` (Port 8400) - Communication management
  - `risk-assessment-agent` (Port 9100) - Threat detection
- **Users**: 2000:2002 (Planning operations users)
- **Capabilities**: Minimal, NET_BIND_SERVICE for communication
- **Security**: Restricted/Confidential levels

### Tier 3: Data Operations Layer (API Access Required)
- **Containers**:
  - `cfbd-data-ingestion` (Port 8100) - CFBD API access
  - `data-validation-agent` (Port 8500) - Data quality validation
  - `feature-engineering-agent` (Port 8600) - Feature processing
  - `weather-integration-agent` (Port 9200) - External weather API
- **Users**: 3000:3003 (Data operations users)
- **Capabilities**: NET_RAW for external API access
- **Security**: Restricted/Confidential levels

### Tier 4: Analytics & Prediction Layer (Model Execution)
- **Containers**:
  - `model-execution-agent` (Port 8200) - ML model execution
  - `advanced-analytics-agent` (Port 8700) - Advanced analytics
  - `bowl-games-specialist` (Port 8800) - Bowl games predictions
- **Users**: 4000:4002 (Analytics operations users)
- **Capabilities**: IPC_OWNER, GPU access (/dev/dri, /dev/nvidia0)
- **Security**: Confidential/Restricted levels

### Tier 5: Quality Assurance Layer (Validation Only)
- **Containers**:
  - `data-quality-assurance` (Port 8900) - Comprehensive validation
  - `prediction-validator-agent` (Port 8910) - Prediction accuracy
  - `human-review-coordinator` (Port 9000) - Human-in-the-loop
- **Users**: 5000:5002 (QA operations users)
- **Capabilities**: CHOWN, SETGID for review management
- **Security**: Confidential/Restricted levels

## Security Features

### Multi-Layer Sandboxing
- **User Isolation**: Each container runs as dedicated non-root user
- **Capability Restrictions**: Minimum required capabilities only
- **Network Isolation**: Separate Docker networks for each tier
- **Filesystem Protection**: Read-only filesystems where possible
- **Resource Limits**: CPU, memory, and disk constraints

### Security Profiles
- **AppArmor**: Docker-default profile for all containers
- **Seccomp**: Default seccomp profiles for system call filtering
- **No-New-Privileges**: Prevent privilege escalation
- **Tmpfs**: Temporary filesystems for /tmp and /var/run

### Network Security
- **Internal Networks**: Isolated subnets for internal communication
- **External Networks**: Controlled access for external APIs
- **Port Exposure**: Minimal exposed ports only
- **Firewall Rules**: Egress and ingress filtering

### Comprehensive Monitoring
- **Health Checks**: Every container includes health monitoring
- **Audit Logging**: Comprehensive security event logging
- **Resource Monitoring**: CPU, memory, and disk usage tracking
- **Threat Detection**: Automated anomaly detection

## Quick Start

### Prerequisites
- Docker 20.10+ with Docker Compose
- At least 16GB RAM available
- GPU support for analytics containers (optional but recommended)

### Deployment
```bash
# Deploy the complete security stack
./scripts/deploy-security-stack.sh deploy

# Verify deployment
./scripts/deploy-security-stack.sh verify

# View container status
./scripts/deploy-security-stack.sh status

# View logs
./scripts/deploy-security-stack.sh logs
./scripts/deploy-security-stack.sh logs meta-orchestration
```

### Management Commands
```bash
# Stop the security stack
./scripts/deploy-security-stack.sh stop

# Restart the stack
./scripts/deploy-security-stack.sh restart

# View logs for specific service
./scripts/deploy-security-stack.sh logs [service-name]
```

## Directory Structure

```
docker/security/
├── docker-compose.security.yml    # Main orchestration configuration
├── Dockerfile.*                   # Specialized Dockerfiles for each tier
├── scripts/                       # Startup and management scripts
│   ├── deploy-security-stack.sh   # Main deployment script
│   ├── start-*.sh                 # Container startup scripts
│   └── health-check.sh            # Universal health check
├── security-policies.json         # Global security configuration
├── cfbd-api-rules.json           # CFBD API security rules
└── README.md                     # This file
```

## Container Details

### Meta Orchestration (Tier 1)
- **Purpose**: Master coordination and system orchestration
- **Security**: Highest security level with admin privileges
- **Resources**: 2GB RAM, 2 CPU cores
- **Network**: orchestration-network, audit-network

### Planning & Coordination (Tier 2)
- **Purpose**: Strategic planning and workflow management
- **Security**: High security with read-only execution
- **Resources**: 1-2GB RAM, 0.5-1.5 CPU cores
- **Network**: orchestration-network, data-network, audit-network

### Data Operations (Tier 3)
- **Purpose**: CFBD API integration and data processing
- **Security**: Restricted with external API access
- **Resources**: 2-4GB RAM, 1-2 CPU cores
- **Network**: data-network, cfbd-network, external-network

### Analytics & Prediction (Tier 4)
- **Purpose**: ML model execution and analytics
- **Security**: Confidential with GPU acceleration
- **Resources**: 4-8GB RAM, 2-4 CPU cores
- **Network**: analytics-network, audit-network

### Quality Assurance (Tier 5)
- **Purpose**: Validation and human review coordination
- **Security**: Confidential with comprehensive validation
- **Resources**: 1-2GB RAM, 0.5-2 CPU cores
- **Network**: qa-network, audit-network

## Security Configuration

### Security Policies
Configuration defined in `security-policies.json`:
- Authentication and authorization rules
- Encryption requirements (AES-256-GCM at rest, TLS 1.3 in transit)
- Audit logging with 365-day retention
- Rate limiting by service type
- Threat detection and automated responses

### Network Configuration
- **orchestration-network**: 172.20.0.0/16 (internal)
- **data-network**: 172.21.0.0/16 (internal)
- **analytics-network**: 172.22.0.0/16 (internal)
- **communication-network**: 172.23.0.0/16 (internal)
- **qa-network**: 172.24.0.0/16 (internal)
- **audit-network**: 172.25.0.0/16 (internal)
- **external-network**: External connectivity
- **cfbd-network**: CFBD API access

## Monitoring and Logging

### Health Monitoring
- **Health Checks**: Every 30 seconds for all containers
- **Resource Monitoring**: CPU, memory, disk usage thresholds
- **Service Discovery**: Automatic service registration and discovery
- **Failure Recovery**: Automatic restart and escalation

### Logging Strategy
- **Structured Logs**: JSON format with consistent fields
- **Log Aggregation**: Centralized logging across all containers
- **Security Events**: Comprehensive audit trail
- **Performance Metrics**: Detailed performance and usage metrics

## Development Workflow

### Adding New Containers
1. Create specialized Dockerfile following naming convention
2. Add container to docker-compose.security.yml
3. Create startup script in scripts/ directory
4. Update deployment script with new service
5. Test deployment and verify security posture

### Security Updates
1. Update base images and security patches
2. Review and update security policies
3. Validate container configurations
4. Test deployment in staging environment
5. Deploy to production with monitoring

## Troubleshooting

### Common Issues
- **Container Won't Start**: Check security context and user permissions
- **Network Issues**: Verify Docker networks and firewall rules
- **Resource Constraints**: Monitor CPU, memory, and disk usage
- **Security Violations**: Review audit logs and security policies

### Debug Commands
```bash
# Check container logs
docker logs [container-name]

# Inspect container configuration
docker inspect [container-name]

# Check network connectivity
docker exec [container-name] ping [target]

# Monitor resource usage
docker stats [container-name]
```

## Production Considerations

### Scaling
- **Horizontal Scaling**: Deploy multiple instances of stateless services
- **Load Balancing**: Configure load balancers for external services
- **Resource Management**: Adjust limits based on workload patterns
- **High Availability**: Configure failover and redundancy

### Performance Optimization
- **Resource Tuning**: Adjust CPU and memory limits
- **Network Optimization**: Optimize Docker network configuration
- **Storage Optimization**: Use appropriate storage drivers
- **Monitoring**: Comprehensive performance monitoring

## Security Best Practices

1. **Least Privilege**: Each container has minimum required capabilities
2. **Defense in Depth**: Multiple layers of security controls
3. **Zero Trust**: Assume no inherent trust between containers
4. **Comprehensive Auditing**: Log all security-relevant events
5. **Regular Updates**: Keep base images and dependencies updated
6. **Security Testing**: Regular security assessments and penetration testing

## Support and Maintenance

- **Documentation**: Regular updates to security configurations
- **Monitoring**: 24/7 monitoring of security events
- **Incident Response**: Automated threat detection and response
- **Compliance**: Regular security audits and compliance checks
- **Training**: Security awareness and best practices training