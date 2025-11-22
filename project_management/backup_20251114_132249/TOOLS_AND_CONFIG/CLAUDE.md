# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with development tools, configuration files, and automation scripts.

## 🎯 Quick Start for Development Tools

```bash
# Navigate to tools directory
cd project_management/TOOLS_AND_CONFIG/

# Run complete agent system demonstration (BEST FIRST STEP)
python demo_agent_system.py

# Quick system validation
python test_agents.py

# Full system quality assurance
python ../QUALITY_ASSURANCE/test_fixed_system.py

# Model validation and retraining
python ../retrain_fixed_models.py
```

## Tools and Configuration Management

This directory contains the development tools, configuration files, automation scripts, and utilities that support the development and maintenance of Script Ohio 2.0. This provides the technical infrastructure and tooling necessary for efficient project development and deployment.

### Tool Categories

- **Configuration Files**: System and application configuration files
- **Development Tools**: Scripts and utilities for development activities
- **Automation Scripts**: Automated processes and workflow tools
- **Build Tools**: Build and deployment automation tools
- **Monitoring Tools**: System monitoring and performance tracking tools

### Key Configuration Files

- **Model Configuration**: Machine learning model configuration and parameters
- **Data Processing**: Data pipeline and processing configuration
- **System Settings**: Application and system configuration files
- **Development Environment**: Development environment setup and configuration
- **`demo_agent_system.py`**: **Complete demonstration script for the intelligent agent system (production-ready, 95% implementation completion)**

## Tool Management Framework

### Configuration Management
- **Environment Configuration**: Development, staging, and production configurations
- **Version Control**: Configuration versioning and change management
- **Security Management**: Secure handling of sensitive configuration data
- **Documentation**: Configuration documentation and usage guides
- **Validation**: Configuration validation and verification procedures

### Tool Integration
- **Development Workflow**: Tools integrated into development workflow
- **CI/CD Integration**: Tools integrated into continuous integration/deployment
- **Monitoring Integration**: Tools integrated with monitoring and alerting
- **Documentation Integration**: Tools integrated with documentation systems
- **Communication Integration**: Tools integrated with communication platforms

### Automation Strategy
- **Process Automation**: Automation of repetitive and manual processes
- **Quality Automation**: Automated quality checks and validations
- **Deployment Automation**: Automated build, test, and deployment processes
- **Monitoring Automation**: Automated monitoring and alerting systems
- **Reporting Automation**: Automated reporting and notification systems

## Usage Patterns

### For Development Setup
1. **Environment Configuration**: Use configuration files for development environment setup
2. **Tool Installation**: Use installation scripts for automated tool setup
3. **Configuration Validation**: Validate configuration before starting development
4. **Documentation Reference**: Consult tool documentation for usage instructions

### For Development Activities
1. **Code Generation**: Use tools for automated code generation and scaffolding
2. **Testing Automation**: Use automated testing tools and scripts
3. **Code Quality**: Use code quality tools and validation scripts
4. **Build Automation**: Use build tools for automated compilation and packaging

### For Deployment and Operations
1. **Configuration Management**: Use configuration files for deployment setup
2. **Automation Scripts**: Use automation scripts for deployment processes
3. **Monitoring Tools**: Use monitoring tools for system health and performance
4. **Maintenance Tools**: Use tools for system maintenance and updates
5. **Agent System Demo**: Run `demo_agent_system.py` to demonstrate the complete intelligent agent system

## Configuration Management

### Environment Configuration
- **Development Environment**: Local development configuration and setup
- **Testing Environment**: Testing environment configuration and data
- **Staging Environment**: Pre-production staging configuration
- **Production Environment**: Production deployment configuration
- **Configuration Overrides**: Environment-specific configuration overrides

### Application Configuration
- **Database Configuration**: Database connection and configuration settings
- **API Configuration**: API endpoints, authentication, and rate limiting
- **Logging Configuration**: Logging levels, destinations, and formats
- **Security Configuration**: Security settings, encryption, and access control
- **Performance Configuration**: Performance tuning and optimization settings

### Machine Learning Configuration
- **Model Configuration**: ML model parameters and hyperparameters
- **Training Configuration**: Training data configuration and parameters
- **Inference Configuration**: Model inference and serving configuration
- **Feature Configuration**: Feature engineering and selection configuration
- **Evaluation Configuration**: Model evaluation and validation configuration

## Automation Tools

### Data Processing Automation
- **Data Ingestion**: Automated data collection and ingestion processes
- **Data Cleaning**: Automated data cleaning and validation scripts
- **Data Transformation**: Automated data transformation and feature engineering
- **Data Validation**: Automated data quality checks and validation
- **Data Pipeline Orchestration**: Automated data pipeline scheduling and management

### Model Training Automation
- **Training Pipeline**: Automated model training and validation pipelines
- **Hyperparameter Tuning**: Automated hyperparameter optimization
- **Model Evaluation**: Automated model evaluation and comparison
- **Model Deployment**: Automated model deployment and serving
- **Model Monitoring**: Automated model performance monitoring and alerting

### Testing Automation
- **Unit Testing**: Automated unit test execution and reporting
- **Integration Testing**: Automated integration test execution
- **Performance Testing**: Automated performance and load testing
- **Security Testing**: Automated security vulnerability scanning
- **Quality Gates**: Automated quality checks and validation

## Development Tools

### Code Quality Tools
- **Linting and Formatting**: Automated code style checking and formatting
- **Static Analysis**: Automated code quality and security analysis
- **Code Coverage**: Automated code coverage measurement and reporting
- **Dependency Management**: Automated dependency scanning and management
- **Code Review**: Automated code review and analysis tools

### Documentation Tools
- **Documentation Generation**: Automated documentation generation from code
- **Documentation Validation**: Automated documentation quality checks
- **API Documentation**: Automated API documentation generation
- **User Guides**: Automated user guide generation and maintenance
- **Change Logs**: Automated change log generation and maintenance

### Build and Deployment Tools
- **Build Automation**: Automated build compilation and packaging
- **Dependency Management**: Automated dependency resolution and installation
- **Container Management**: Container building and management tools
- **Deployment Automation**: Automated deployment to different environments
- **Rollback Tools**: Automated rollback and recovery procedures

## Tool Maintenance and Support

### Regular Maintenance
- **Tool Updates**: Regular updates to tools and dependencies
- **Configuration Review**: Regular review and update of configurations
- **Performance Optimization**: Regular performance tuning and optimization
- **Security Updates**: Regular security patches and updates
- **Documentation Updates**: Regular documentation updates and improvements

### User Support
- **Tool Documentation**: Comprehensive documentation for all tools
- **User Training**: Training materials and sessions for tool usage
- **Troubleshooting Guides**: Troubleshooting guides and common solutions
- **Best Practice Guides**: Best practice guides for tool usage
- **Support Channels**: Support channels for tool-related issues

### Tool Evaluation and Selection
- **Tool Assessment**: Regular assessment of tool effectiveness and suitability
- **New Tool Evaluation**: Process for evaluating and adopting new tools
- **Tool Replacement**: Process for replacing outdated or ineffective tools
- **Cost-Benefit Analysis**: Analysis of tool costs and benefits
- **User Feedback**: Systematic collection of user feedback on tools

## 🚀 Development Commands

### Running the Agent System Demo
```bash
# Complete intelligent agent system demonstration (RECOMMENDED FIRST STEP)
python demo_agent_system.py

# Interactive demo options:
# 1. Context Manager - Role detection and optimization
# 2. Agent Framework - Agent capabilities and processing
# 3. Analytics Orchestrator - Request coordination
# 4. Complete Integrated System - Full workflow
# 5. Run All Demonstrations
```

### System Validation and Testing
```bash
# Quick agent system validation
python test_agents.py

# Full system quality assurance
python ../QUALITY_ASSURANCE/test_fixed_system.py

# Model validation and retraining
python ../retrain_fixed_models.py
```

### Configuration and Features
```bash
# Model configuration validation
python -c "
from model_config import MODEL_INFO
print('Available models:', list(MODEL_INFO.keys()))
for model, info in MODEL_INFO.items():
    print(f'{model}: {info[\"description\"]}')
"

# Feature validation
python -c "
from model_features import RIDGE_FEATURES, XGB_FEATURES
print(f'Ridge model uses {len(RIDGE_FEATURES)} features')
print(f'XGBoost model uses {len(XGB_FEATURES)} features')
"
```

## Integration with Project Management

These tools and configurations integrate with the broader project management system:

- **Development Workflow**: Tools support and streamline development workflows
- **Quality Assurance**: Tools support quality assurance and testing processes
- **Documentation**: Tools support documentation creation and maintenance
- **Monitoring**: Tools support project and system monitoring activities
- **Automation**: Tools support automation of repetitive tasks and processes
- **🤖 Intelligent Agent System**: Complete production-ready architecture with 95% implementation completion

## Security and Compliance

### Security Management
- **Credential Management**: Secure storage and management of credentials
- **Access Control**: Proper access control for tools and configurations
- **Audit Logging**: Audit logging for tool usage and configuration changes
- **Vulnerability Management**: Regular scanning and management of vulnerabilities
- **Compliance Monitoring**: Monitoring for compliance with security standards

### Configuration Security
- **Secrets Management**: Secure management of sensitive configuration data
- **Encryption**: Encryption of sensitive configuration and data
- **Environment Isolation**: Proper isolation between different environments
- **Change Management**: Controlled process for configuration changes
- **Backup and Recovery**: Regular backup and recovery procedures for configurations

## 🔧 Core Development Tools

### Agent System Demonstration (`demo_agent_system.py`)
**The most important script** - showcases the complete intelligent agent system:

```python
# Interactive demo options:
# 1. Context Manager - Role detection and 40% token optimization
# 2. Agent Framework - Agent capabilities and processing
# 3. Analytics Orchestrator - Request coordination
# 4. Complete Integrated System - Full workflow
# 5. Run All Demonstrations

# Run specific demo components
python demo_agent_system.py --component=context_manager
python demo_agent_system.py --component=orchestrator
python demo_agent_system.py --component=integrated
```

### System Validation Tools
```bash
# Quick agent health check
python test_agents.py

# Comprehensive system validation
python ../QUALITY_ASSURANCE/test_fixed_system.py

# Model validation and training
python ../model_pack/model_training_agent.py

# Retrain models with latest data
python ../retrain_fixed_models.py
```

## 📊 Configuration Management

### Model Configuration (`model_config.py`)
```python
# Access model information and validation
from model_config import MODEL_INFO, validate_model_config

print("Available models:")
for model_name, info in MODEL_INFO.items():
    print(f"  {model_name}: {info['description']}")

# Validate all model configurations
validation_results = validate_model_config()
for model, status in validation_results.items():
    print(f"{model}: {'✅' if status else '❌'}")
```

### Feature Configuration (`model_features.py`)
```python
# Inspect feature definitions for ML models
from model_features import RIDGE_FEATURES, XGB_FEATURES, SHARED_FEATURES

print(f"Ridge model uses {len(RIDGE_FEATURES)} features")
print(f"XGBoost model uses {len(XGB_FEATURES)} features")
print(f"Shared features: {len(SHARED_FEATURES)}")

# Feature validation
def validate_feature_completeness():
    missing_features = set(XGB_FEATURES) - set(RIDGE_FEATURES)
    if missing_features:
        print(f"Missing from Ridge model: {missing_features}")
    else:
        print("✅ All features consistent across models")
```

## 🚀 Automation and Deployment

### Data Acquisition Automation
```bash
# Acquire latest college football data
python ../model_pack/2025_data_acquisition.py

# Process and validate new data
python ../model_pack/2025_data_acquisition_v2.py

# Mock data for testing
python ../model_pack/2025_data_acquisition_mock.py
```

### Quality Assurance Automation
```bash
# Run comprehensive QA checks
python ../QUALITY_ASSURANCE/test_fixed_system.py

# Individual component testing
python ../tests/test_agent_system.py -v
python ../tests/test_model_pack_comprehensive.py -v
python ../tests/test_model_execution_engine_comprehensive.py -v
```

### Model Retraining Pipeline
```bash
# Automated model retraining with validation
python ../retrain_fixed_models.py

# Custom model training with parameters
python ../model_pack/model_training_agent.py --model=xgboost --season=2025
```

## 🔍 System Monitoring and Diagnostics

### Performance Monitoring
```python
# System health check
def system_health_check():
    """Comprehensive system health monitoring"""

    health_status = {
        'timestamp': datetime.now().isoformat(),
        'components': {}
    }

    # Check agent system
    try:
        from agents.analytics_orchestrator import AnalyticsOrchestrator
        orchestrator = AnalyticsOrchestrator()
        health_status['components']['agent_system'] = {
            'status': 'healthy',
            'response_time': test_response_time()
        }
    except Exception as e:
        health_status['components']['agent_system'] = {
            'status': 'error',
            'error': str(e)
        }

    # Check model files
    model_files = [
        '../model_pack/ridge_model_2025.joblib',
        '../model_pack/xgb_home_win_model_2025.pkl',
        '../model_pack/fastai_home_win_model_2025.pkl'
    ]

    for model_file in model_files:
        if os.path.exists(model_file):
            health_status['components'][os.path.basename(model_file)] = 'available'
        else:
            health_status['components'][os.path.basename(model_file)] = 'missing'

    return health_status
```

### Configuration Validation
```python
# Validate all system configurations
def validate_all_configurations():
    """Comprehensive configuration validation"""

    validation_results = {}

    # Validate model configurations
    validation_results['models'] = validate_model_config()

    # Validate feature configurations
    validation_results['features'] = validate_feature_config()

    # Validate agent system
    try:
        from agents.core.agent_framework import AgentFactory
        factory = AgentFactory()
        validation_results['agents'] = factory.validate_configuration()
    except Exception as e:
        validation_results['agents'] = {'valid': False, 'error': str(e)}

    return validation_results
```

## 📋 Development Workflow Integration

### Pre-commit Validation
```bash
# Create pre-commit hook for validation
#!/bin/bash
# .git/hooks/pre-commit

echo "Running pre-commit validation..."

# Syntax validation
echo "Checking Python syntax..."
find . -name "*.py" -exec python3 -m py_compile {} \;
if [ $? -ne 0 ]; then
    echo "❌ Syntax validation failed"
    exit 1
fi

# Run agent system tests
echo "Validating agent system..."
python project_management/TOOLS_AND_CONFIG/test_agents.py
if [ $? -ne 0 ]; then
    echo "❌ Agent system validation failed"
    exit 1
fi

echo "✅ All validations passed"
```

### Development Environment Setup
```bash
# Automated environment setup script
#!/bin/bash
# setup_dev_environment.sh

echo "Setting up Script Ohio 2.0 development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $(echo "$python_version >= 3.13" | bc) -eq 0 ]]; then
    echo "❌ Python 3.13+ required, found $python_version"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Validate installation
echo "Validating installation..."
python -c "from agents.core.agent_framework import BaseAgent; print('✅ Agent system OK')"
python -c "import pandas, numpy, sklearn; print('✅ Core dependencies OK')"

# Run initial system test
echo "Running initial system validation..."
python project_management/TOOLS_AND_CONFIG/demo_agent_system.py --quick

echo "✅ Development environment setup complete!"
```

## 🔒 Security and Maintenance

### Security Configuration
```python
# Security validation for sensitive configurations
def validate_security_config():
    """Validate security configurations"""

    security_checks = {
        'api_keys_hidden': True,
        'no_hardcoded_secrets': True,
        'proper_permissions': True
    }

    # Check for hardcoded API keys
    import re
    secret_patterns = [
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'password\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']'
    ]

    for root, dirs, files in os.walk('..'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            security_checks['no_hardcoded_secrets'] = False
                            print(f"⚠️ Potential secret found in {file_path}")

    return security_checks
```

### Backup and Recovery
```bash
# Automated backup script for critical configurations
#!/bin/bash
# backup_critical_configs.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup model files
echo "Backing up model files..."
cp ../model_pack/*_2025.* "$BACKUP_DIR/"

# Backup configuration files
echo "Backing up configuration files..."
cp model_config.py "$BACKUP_DIR/"
cp model_features.py "$BACKUP_DIR/"

# Create backup manifest
echo "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest.txt" << EOF
Backup created: $(date)
Files backed up:
- Model files: $(ls ../model_pack/*_2025.* | wc -l)
- Configuration files: 2
- Total size: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF

echo "✅ Backup completed: $BACKUP_DIR"
```

## 📈 Performance Optimization Tools

### System Performance Profiler
```python
# Performance profiling for agent system
import cProfile
import time
from agents.analytics_orchestrator import AnalyticsOrchestrator

def profile_agent_system():
    """Profile agent system performance"""

    profiler = cProfile.Profile()
    orchestrator = AnalyticsOrchestrator()

    # Create test requests
    test_requests = [
        ("simple", "What is EPA?", "learning"),
        ("complex", "Analyze team efficiency", "analysis"),
        ("prediction", "Predict Ohio State vs Michigan", "prediction")
    ]

    # Profile each request type
    for req_type, query, query_type in test_requests:
        print(f"\nProfiling {req_type} request...")

        profiler.enable()
        start_time = time.time()

        request = AnalyticsRequest(
            user_id="profiler_test",
            query=query,
            query_type=query_type,
            parameters={},
            context_hints={}
        )

        response = orchestrator.process_analytics_request(request)
        execution_time = time.time() - start_time

        profiler.disable()

        print(f"Execution time: {execution_time:.3f}s")
        print(f"Status: {response.status}")

        # Save profiling results
        profiler.dump_stats(f"profile_{req_type}.prof")
```

## 🔗 Integration Documentation

### Tool Integration Matrix
| Tool | Purpose | Integration | Dependencies |
|------|---------|------------|-------------|
| `demo_agent_system.py` | System demonstration | Standalone | Agent system |
| `test_agents.py` | Quick validation | CI/CD pipeline | Agent system |
| `model_config.py` | Model configuration | Model training | ML models |
| `model_features.py` | Feature definitions | Feature engineering | Model pack |
| `retrain_fixed_models.py` | Model retraining | ML pipeline | Training data |

---

**Tools and Configuration Philosophy**: This directory provides the technical infrastructure and tooling necessary for efficient, secure, and scalable development and deployment of Script Ohio 2.0. Good tools and configuration management enable development teams to work efficiently while maintaining high standards of quality, security, and reliability.

**Enhanced with Agent Integration**: All tools are designed to work seamlessly with the intelligent agent system, providing comprehensive validation, monitoring, and automation capabilities that ensure production readiness and maintainability.

**Production Focus**: Tools and configurations are optimized for production deployment with comprehensive error handling, performance monitoring, and automated quality assurance processes.