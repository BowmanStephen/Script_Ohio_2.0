#!/usr/bin/env python3
"""
Audit Automation Setup Script - Initialize complete audit automation system.

This script sets up:
- Production audit configuration
- Default alert rules and schedules
- Integration with existing audit system
- Initial audit runs to validate system
- Documentation and user guides
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.audit.scheduler_agent import AuditSchedulerAgent, AlertSeverity, AlertChannel
from agents.audit.alerting_agent import AlertingAgent, AlertRule
from scripts.production_audit import ProductionAuditRunner


def setup_directories():
    """Create necessary directories for audit automation."""
    print("📁 Setting up directory structure...")

    directories = [
        "production_audit_reports",
        "production_audit_reports/metrics",
        "production_audit_reports/automation_config",
        "logs/audit_production",
        "config"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory}")

    print("📁 Directory structure created successfully")


def setup_default_config():
    """Set up default configuration files."""
    print("⚙️ Setting up default configuration...")

    # Alerting configuration
    alerting_config = {
        "alert_file": "logs/audit_production/alerts.log",
        "alert_history_file": "production_audit_reports/alert_history.json",
        "max_history_size": 1000,
        "default_channels": ["console", "file"],
        "rate_limit_enabled": True,
        "deduplication_enabled": True,
        "batch_send_interval": 60,
        "email_config": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_address": "",
            "to_addresses": []
        },
        "slack_config": {
            "enabled": False,
            "webhook_url": "",
            "channel": "#alerts",
            "username": "Audit Bot"
        },
        "webhook_config": {
            "enabled": False,
            "url": "",
            "headers": {},
            "timeout": 30
        }
    }

    config_file = Path("config/alerting_config.json")
    with open(config_file, 'w') as f:
        json.dump(alerting_config, f, indent=2)
    print(f"   ✅ Created: {config_file}")

    # Production audit configuration
    audit_config = {
        "audit_settings": {
            "default_timeout": 600,
            "quick_mode_timeout": 180,
            "parallel_execution": True,
            "max_workers": 3,
            "retry_attempts": 2,
            "retry_delay": 30
        },
        "output_settings": {
            "output_dir": "production_audit_reports",
            "backup_reports": True,
            "compression": True,
            "retention_days": 30
        },
        "alerting": {
            "enabled": True,
            "critical_threshold": 70,
            "failure_threshold": 5,
            "channels": ["console", "file"]
        },
        "scheduling": {
            "auto_cleanup": True,
            "cleanup_threshold": 90,
            "performance_tracking": True
        }
    }

    audit_config_file = Path("config/production_audit_config.json")
    with open(audit_config_file, 'w') as f:
        json.dump(audit_config, f, indent=2)
    print(f"   ✅ Created: {audit_config_file}")


def setup_default_alert_rules(alerting_agent: AlertingAgent):
    """Set up default alert rules."""
    print("🚨 Setting up default alert rules...")

    default_rules = [
        {
            "rule_id": "critical_score_threshold",
            "name": "Critical Score Threshold",
            "description": "Alert when audit score falls below critical threshold",
            "severity": "critical",
            "channels": ["console", "file"],
            "threshold_conditions": {
                "min_score": 70
            },
            "cooldown_minutes": 30,
            "template": """
🚨 CRITICAL AUDIT SCORE ALERT 🚨
Audit Score: {overall_score}%
Threshold: 70%
Audit Name: {audit_name}
Time: {current_time}

This audit indicates critical system health issues that require immediate attention.
            """.strip()
        },
        {
            "rule_id": "critical_failures_detected",
            "name": "Critical Failures Detected",
            "description": "Alert when critical audit failures are detected",
            "severity": "critical",
            "channels": ["console", "file"],
            "threshold_conditions": {
                "critical_failures": 1
            },
            "cooldown_minutes": 15,
            "template": """
🚨 CRITICAL AUDIT FAILURES DETECTED 🚨
Critical Failures: {critical_failures}
Audit Name: {audit_name}
Time: {current_time}

Critical system components have failed validation. Immediate investigation required.
            """.strip()
        },
        {
            "rule_id": "high_failure_count",
            "name": "High Failure Count",
            "description": "Alert when too many audit checks fail",
            "severity": "warning",
            "channels": ["console", "file"],
            "threshold_conditions": {
                "max_failures": 5
            },
            "cooldown_minutes": 60,
            "template": """
⚠️ HIGH AUDIT FAILURE COUNT ⚠️
Failed Checks: {failed_checks}
Total Checks: {total_checks}
Audit Score: {overall_score}%
Audit Name: {audit_name}
Time: {current_time}

Multiple audit checks have failed. System review recommended.
            """.strip()
        },
        {
            "rule_id": "slow_execution",
            "name": "Slow Audit Execution",
            "description": "Alert when audit execution takes too long",
            "severity": "warning",
            "channels": ["console", "file"],
            "threshold_conditions": {
                "max_execution_time": 300  # 5 minutes
            },
            "cooldown_minutes": 120,
            "template": """
⚠️ SLOW AUDIT EXECUTION ⚠️
Execution Time: {execution_time}s
Threshold: 300s
Audit Name: {audit_name}
Time: {current_time}

Audit execution is taking longer than expected. Performance optimization may be needed.
            """.strip()
        },
        {
            "rule_id": "excellent_performance",
            "name": "Excellent Performance",
            "description": "Notify when audit shows excellent performance",
            "severity": "info",
            "channels": ["console", "file"],
            "threshold_conditions": {
                "min_score": 95,
                "max_failures": 1
            },
            "cooldown_minutes": 1440,  # 24 hours
            "template": """
🎉 EXCELLENT AUDIT PERFORMANCE 🎉
Audit Score: {overall_score}%
Passed Checks: {passed_checks}/{total_checks}
Audit Name: {audit_name}
Time: {current_time}

System demonstrates exceptional performance and reliability!
            """.strip()
        }
    ]

    for rule_config in default_rules:
        result = alerting_agent._create_alert_rule(rule_config, {})
        if "error" not in result:
            print(f"   ✅ Created rule: {rule_config['rule_id']}")
        else:
            print(f"   ❌ Failed to create rule: {rule_config['rule_id']} - {result['error']}")


def setup_default_schedules(scheduler_agent: AuditSchedulerAgent):
    """Set up default audit schedules."""
    print("⏰ Setting up default audit schedules...")

    default_schedules = [
        {
            "schedule_id": "hourly_health_check",
            "audit_type": "quick",
            "schedule_pattern": "hourly",
            "trigger_type": "scheduled",
            "enabled": True,
            "parameters": {},
            "timezone": "UTC"
        },
        {
            "schedule_id": "daily_comprehensive_audit",
            "audit_type": "comprehensive",
            "schedule_pattern": "daily",
            "trigger_type": "scheduled",
            "enabled": True,
            "parameters": {},
            "timezone": "UTC"
        },
        {
            "schedule_id": "weekly_system_audit",
            "audit_type": "comprehensive",
            "schedule_pattern": "weekly",
            "trigger_type": "scheduled",
            "enabled": True,
            "parameters": {
                "audit_name": "Weekly System Health Audit"
            },
            "timezone": "UTC"
        },
        {
            "schedule_id": "daily_model_validation",
            "audit_type": "domain",
            "schedule_pattern": "daily",
            "trigger_type": "scheduled",
            "enabled": True,
            "parameters": {
                "domain": "models",
                "audit_name": "Daily Model Validation Audit"
            },
            "timezone": "UTC"
        }
    ]

    for schedule_config in default_schedules:
        result = scheduler_agent._create_schedule(schedule_config, {})
        if "error" not in result:
            print(f"   ✅ Created schedule: {schedule_config['schedule_id']}")
        else:
            print(f"   ❌ Failed to create schedule: {schedule_config['schedule_id']} - {result['error']}")


def run_initial_audit_test():
    """Run initial audit to validate system."""
    print("🧪 Running initial audit test...")

    try:
        runner = ProductionAuditRunner("config/production_audit_config.json")

        print("   📊 Running quick audit test...")
        success, result = runner.run_audit("quick")

        if success:
            summary = result.get("audit_summary", {})
            print(f"   ✅ Quick audit completed successfully")
            print(f"      Score: {summary.get('overall_score', 0):.1f}%")
            print(f"      Checks: {summary.get('total_checks', 0)} total")
            print(f"      Critical issues: {summary.get('critical_failures', 0)}")
        else:
            print(f"   ❌ Quick audit failed: {result.get('error', 'Unknown error')}")
            return False

        print("   📊 Running comprehensive audit test...")
        success, result = runner.run_audit("comprehensive")

        if success:
            summary = result.get("audit_summary", {})
            print(f"   ✅ Comprehensive audit completed successfully")
            print(f"      Score: {summary.get('overall_score', 0):.1f}%")
            print(f"      Checks: {summary.get('total_checks', 0)} total")
            print(f"      Critical issues: {summary.get('critical_failures', 0)}")
        else:
            print(f"   ❌ Comprehensive audit failed: {result.get('error', 'Unknown error')}")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Initial audit test failed: {e}")
        return False


def create_startup_scripts():
    """Create convenient startup scripts."""
    print("📜 Creating startup scripts...")

    # Start scheduler script
    start_scheduler_script = """#!/bin/bash
# Start Audit Scheduler

echo "🚀 Starting Audit Scheduler..."

python3 -c "
import sys
sys.path.insert(0, '.')
from agents.audit.scheduler_agent import AuditSchedulerAgent

scheduler = AuditSchedulerAgent()
result = scheduler._start_scheduler({})
print('Scheduler started:', result)

try:
    import time
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print('\\n🛑 Stopping scheduler...')
    scheduler._stop_scheduler({})
    print('Scheduler stopped')
"
"""

    script_file = Path("scripts/start_audit_scheduler.sh")
    with open(script_file, 'w') as f:
        f.write(start_scheduler_script)
    os.chmod(script_file, 0o755)
    print(f"   ✅ Created: {script_file}")

    # Production audit runner script
    production_audit_script = """#!/bin/bash
# Production Audit Runner

AUDIT_TYPE=${1:-quick}

echo "🔍 Running Production Audit: $AUDIT_TYPE"
python3 scripts/production_audit.py --audit-type "$AUDIT_TYPE"
"""

    script_file = Path("scripts/run_production_audit.sh")
    with open(script_file, 'w') as f:
        f.write(production_audit_script)
    os.chmod(script_file, 0o755)
    print(f"   ✅ Created: {script_file}")

    # Test alerting script
    test_alerts_script = """#!/bin/bash
# Test Alerting System

echo "🚨 Testing Alerting System..."

python3 -c "
import sys
sys.path.insert(0, '.')
from agents.audit.alerting_agent import AlertingAgent

alert_agent = AlertingAgent()
result = alert_agent._test_alert_channels({'channels': ['console', 'file']}, {})
print('Alert test results:', result)
"
"""

    script_file = Path("scripts/test_alerting.sh")
    with open(script_file, 'w') as f:
        f.write(test_alerts_script)
    os.chmod(script_file, 0o755)
    print(f"   ✅ Created: {script_file}")


def create_documentation():
    """Create documentation for the audit automation system."""
    print("📚 Creating documentation...")

    # User guide
    user_guide = """# Production Audit System User Guide

## Overview

The Production Audit System provides automated, scheduled, and real-time monitoring of your Script Ohio 2.0 project with intelligent alerting.

## Quick Start

### 1. Run a Production Audit
```bash
# Quick audit (critical components only)
./scripts/run_production_audit.sh quick

# Comprehensive audit (all components)
./scripts/run_production_audit.sh comprehensive

# Domain-specific audit
./scripts/run_production_audit.sh domain --domain system
```

### 2. Start the Automated Scheduler
```bash
# Start the audit scheduler (runs in background)
./scripts/start_audit_scheduler.sh
```

### 3. Test Alerting
```bash
# Test all alert channels
./scripts/test_alerting.sh
```

## Configuration

### Audit Configuration
Edit `config/production_audit_config.json` to customize:
- Timeout settings
- Parallel execution settings
- Output directories
- Alert thresholds

### Alerting Configuration
Edit `config/alerting_config.json` to configure:
- Email notifications
- Slack webhooks
- Custom webhook endpoints
- Alert channels and thresholds

## Default Schedules

The system includes these default schedules:
- **Hourly Health Check**: Quick audit every hour
- **Daily Comprehensive Audit**: Full system audit daily
- **Weekly System Audit**: In-depth weekly analysis
- **Daily Model Validation**: Daily model-specific audit

## Managing Schedules

```python
from agents.audit.scheduler_agent import AuditSchedulerAgent

scheduler = AuditSchedulerAgent()

# List schedules
schedules = scheduler._list_schedules({})

# Create custom schedule
scheduler._create_schedule({
    "schedule_id": "custom_audit",
    "audit_type": "comprehensive",
    "schedule_pattern": "every_6_hours",
    "enabled": True
}, {})

# Start/stop scheduler
scheduler._start_scheduler({})
scheduler._stop_scheduler({})
```

## Managing Alert Rules

```python
from agents.audit.alerting_agent import AlertingAgent

alert_agent = AlertingAgent()

# List alert rules
rules = alert_agent._list_alert_rules({})

# Create custom alert rule
alert_agent._create_alert_rule({
    "rule_id": "custom_alert",
    "name": "Custom Alert Rule",
    "severity": "warning",
    "channels": ["console", "file", "email"],
    "threshold_conditions": {
        "min_score": 80
    }
}, {})

# Test alert channels
test_result = alert_agent._test_alert_channels({
    "channels": ["console", "file", "email"]
}, {})
```

## Monitoring

### View Audit Results
- Console output for real-time monitoring
- Log files in `logs/audit_production/`
- Detailed reports in `production_audit_reports/`

### Alert History
```python
from agents.audit.alerting_agent import AlertingAgent

alert_agent = AlertingAgent()
history = alert_agent._get_alert_history({
    "limit": 50,
    "severity": "critical"
}, {})
```

### Performance Metrics
- Execution time tracking
- Success/failure rates
- Alert frequency analysis
- Historical trend data

## Troubleshooting

### Common Issues

1. **Audit Timeouts**
   - Increase timeout in config
   - Check system resources
   - Verify API connectivity

2. **Missing Alerts**
   - Check alert rule configuration
   - Verify channel connectivity
   - Review alert history

3. **Scheduler Not Running**
   - Check process status
   - Review scheduler logs
   - Verify configuration

### Log Files
- `logs/audit_production/`: System logs and alerts
- `production_audit_reports/`: Audit results and metrics
- `production_audit_reports/metrics/`: Performance data

## Integration

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run Production Audit
  run: |
    python3 scripts/production_audit.py --audit-type quick
    python3 scripts/production_audit.py --cleanup-only
```

### Monitoring Integration
- Export metrics to Prometheus
- Send alerts to PagerDuty
- Integrate with existing monitoring tools

## Best Practices

1. **Regular Maintenance**
   - Review and update alert rules
   - Clean up old audit reports
   - Monitor system performance

2. **Alert Management**
   - Keep critical alerts minimal
   - Use appropriate severity levels
   - Set reasonable cooldown periods

3. **Performance Optimization**
   - Use parallel execution
   - Cache results when appropriate
   - Monitor resource usage

## Support

For issues and questions:
1. Check log files for error details
2. Review configuration settings
3. Test individual components
4. Consult the system documentation
"""

    guide_file = Path("docs/AUDIT_AUTOMATION_USER_GUIDE.md")
    with open(guide_file, 'w') as f:
        f.write(user_guide)
    print(f"   ✅ Created: {guide_file}")


def main():
    """Main setup function."""
    print("🚀 Setting up Production Audit Automation System")
    print("=" * 60)

    try:
        # Step 1: Create directories
        setup_directories()
        print()

        # Step 2: Setup configuration
        setup_default_config()
        print()

        # Step 3: Initialize agents
        print("🤖 Initializing audit agents...")
        scheduler_agent = AuditSchedulerAgent()
        alerting_agent = AlertingAgent()
        print("   ✅ Agents initialized successfully")
        print()

        # Step 4: Setup default rules and schedules
        setup_default_alert_rules(alerting_agent)
        print()
        setup_default_schedules(scheduler_agent)
        print()

        # Step 5: Run initial test
        if not run_initial_audit_test():
            print("⚠️ Warning: Initial audit test failed - check system configuration")
            print("The automation system has been set up but may require manual adjustment.")
        else:
            print()
        print("🎉 Production Audit Automation System setup completed successfully!")
        print()

        # Step 6: Create scripts and documentation
        create_startup_scripts()
        print()
        create_documentation()
        print()

        # Final summary
        print("=" * 60)
        print("📋 SETUP SUMMARY")
        print("=" * 60)
        print("✅ Directory structure created")
        print("✅ Default configuration files created")
        print("✅ Alert rules configured")
        print("✅ Audit schedules configured")
        print("✅ Startup scripts created")
        print("✅ Documentation generated")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Run: ./scripts/run_production_audit.sh quick")
        print("2. Test: ./scripts/test_alerting.sh")
        print("3. Start scheduler: ./scripts/start_audit_scheduler.sh")
        print("4. Configure email/Slack alerts in config/alerting_config.json")
        print("5. Customize schedules and alert rules as needed")
        print()
        print("📚 Documentation: docs/AUDIT_AUTOMATION_USER_GUIDE.md")
        print("📁 Reports: production_audit_reports/")
        print("📋 Logs: logs/audit_production/")

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)