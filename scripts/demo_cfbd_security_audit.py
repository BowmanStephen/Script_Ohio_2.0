#!/usr/bin/env python3
"""
CFBD API Security and Audit System Demonstration
Shows advanced API security, rate limiting, and comprehensive audit logging
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_cfbd_security_audit():
    """Demonstrate the CFBD API security and audit system"""

    print("🔐 CFBD API Security and Audit System Demonstration")
    print("=" * 60)

    try:
        # Import security components
        from agents.security.cfbd_api_security_manager import CFBDAPISecurityManager, SecurityLevel
        from agents.security.comprehensive_audit_system import ComprehensiveAuditSystem, AuditCategory, AuditSeverity
        from agents.core.streaming_integration_config import get_streaming_config

        # Initialize streaming system
        print("\n🚀 Initializing Security and Audit System...")
        streaming_config = get_streaming_config()

        # Initialize security manager
        security_manager = CFBDAPISecurityManager()
        security_config = {
            "security": {
                "encryption_enabled": True,
                "audit_level": "comprehensive",
                "max_failed_attempts": 3,
                "lockout_duration_minutes": 5
            },
            "event_stream": streaming_config.config.get("event_stream", {}),
            "rate_limiting": {
                "custom_limits": {
                    "premium": {
                        "requests_per_window": 5000,
                        "window_seconds": 3600,
                        "burst_capacity": 100,
                        "algorithm": "token_bucket"
                    }
                }
            }
        }

        security_result = await security_manager.initialize(security_config)

        if security_result["status"] != "success":
            print(f"❌ Failed to initialize security manager: {security_result['error']}")
            return

        print(f"✅ Security Manager initialized!")
        print(f"   - Credentials loaded: {security_result['credentials_loaded']}")
        print(f"   - Rate limiters: {security_result['rate_limiters_initialized']}")
        print(f"   - Security level: {security_result['security_level']}")

        # Initialize audit system
        audit_system = ComprehensiveAuditSystem()
        audit_config = {
            "audit": {
                "storage_directory": "audit_logs_demo",
                "encryption_enabled": True,
                "compression_enabled": True,
                "forensic_mode": True,
                "retention_policies": {
                    "gdpr": 2555,
                    "sox": 2555,
                    "hipaa": 2190
                }
            },
            "event_stream": streaming_config.config.get("event_stream", {})
        }

        audit_result = await audit_system.initialize(audit_config)

        if audit_result["status"] != "success":
            print(f"❌ Failed to initialize audit system: {audit_result['error']}")
            return

        print(f"✅ Audit System initialized!")
        print(f"   - Storage: {audit_result['storage_directory']}")
        print(f"   - Encryption: {audit_result['encryption_enabled']}")
        print(f"   - Forensic mode: {audit_result['forensic_mode']}")

        # Connect components via streaming config
        await streaming_config.initialize_components()

        print("\n🎯 Starting Security Demonstration Scenarios...")

        # Scenario 1: API Credential Management
        await demo_credential_management(security_manager, audit_system)

        # Scenario 2: Rate Limiting Enforcement
        await demo_rate_limiting(security_manager, audit_system)

        # Scenario 3: Security Threat Detection
        await demo_threat_detection(security_manager, audit_system)

        # Scenario 4: Comprehensive Audit Logging
        await demo_audit_logging(audit_system)

        # Scenario 5: Compliance Reporting
        await demo_compliance_reporting(audit_system)

        # Scenario 6: Forensic Analysis
        await demo_forensic_analysis(audit_system)

        print("\n📊 Final Security Status...")
        await show_security_status(security_manager, audit_system)

    except Exception as e:
        logger.error(f"Security demonstration failed: {e}")
        print(f"❌ Security demonstration failed: {e}")

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if 'security_manager' in locals():
            await security_manager.shutdown()
        if 'audit_system' in locals():
            await audit_system.shutdown()
        if 'streaming_config' in locals():
            await streaming_config.shutdown()
        print("✅ Cleanup complete")

async def demo_credential_management(security_manager, audit_system):
    """Demonstrate API credential management"""
    print("\n🔑 Scenario 1: API Credential Management")
    print("-" * 40)

    try:
        # Create different types of credentials
        credentials = [
            {
                "security_level": "authenticated",
                "purpose": "analytics_access",
                "description": "Access for analytics and reporting",
                "allowed_endpoints": ["/games", "/teams", "/stats"],
                "rate_limits": {
                    "games": {"requests_per_window": 1000, "window_seconds": 3600, "algorithm": "sliding_window"}
                }
            },
            {
                "security_level": "premium",
                "purpose": "high_volume_data",
                "description": "Premium high-volume data access",
                "allowed_endpoints": ["*"],
                "rate_limits": {
                    "all": {"requests_per_window": 10000, "window_seconds": 3600, "algorithm": "token_bucket", "burst_capacity": 500}
                }
            },
            {
                "security_level": "restricted",
                "purpose": "bowl_predictions",
                "description": "Access to bowl prediction APIs",
                "allowed_endpoints": ["/bowl_predictions", "/matchups"],
                "rate_limits": {
                    "predictions": {"requests_per_window": 500, "window_seconds": 3600, "algorithm": "fixed_window"}
                }
            }
        ]

        created_credentials = []

        for i, cred_data in enumerate(credentials):
            print(f"🔐 Creating credential {i+1}: {cred_data['purpose']}")

            result = await security_manager._manage_api_credentials({
                "action": "create",
                "credential_data": cred_data
            }, {})

            if result["status"] == "success":
                created_credentials.append({
                    "id": result["credential_id"],
                    "api_key": result["api_key"],
                    "level": cred_data["security_level"]
                })
                print(f"   ✅ Created: {result['credential_id']}")
                print(f"   📋 API Key: {result['api_key'][:20]}...")

                # Log credential creation to audit
                await audit_system._log_audit_event({
                    "audit_event_data": {
                        "category": "security_events",
                        "severity": "info",
                        "source_system": "cfbd_api_security_manager",
                        "actor_id": "system_admin",
                        "actor_type": "user",
                        "action": "credential_created",
                        "outcome": "success",
                        "description": f"Created {cred_data['security_level']} credential for {cred_data['purpose']}",
                        "resource_id": result["credential_id"],
                        "resource_type": "api_credential",
                        "sensitive_data": True,
                        "processing_time_ms": 150
                    },
                    "compliance_tags": ["gdpr", "sox"]
                }, {})
            else:
                print(f"   ❌ Failed: {result['error']}")

        # List all credentials
        print(f"\n📋 Total credentials created: {len(created_credentials)}")
        list_result = await security_manager._manage_api_credentials({
            "action": "list"
        }, {})

        if list_result["status"] == "success":
            print("🔐 Active Credentials:")
            for cred in list_result.get("credentials", []):
                print(f"   - {cred.get('credential_id', 'unknown')} ({cred.get('security_level', 'unknown')})")

        return created_credentials

    except Exception as e:
        logger.error(f"Credential management demo failed: {e}")
        print(f"❌ Credential management demo failed: {e}")

async def demo_rate_limiting(security_manager, audit_system):
    """Demonstrate rate limiting enforcement"""
    print("\n⏱️  Scenario 2: Rate Limiting Enforcement")
    print("-" * 40)

    try:
        print("🚦 Testing rate limiting with different scenarios...")

        # Create a test credential for rate limiting
        test_credential = await security_manager._manage_api_credentials({
            "action": "create",
            "credential_data": {
                "security_level": "authenticated",
                "purpose": "rate_limit_test",
                "description": "Credential for testing rate limits",
                "allowed_endpoints": ["/test"]
            }
        }, {})

        if test_credential["status"] != "success":
            print(f"❌ Failed to create test credential: {test_credential['error']}")
            return

        credential_id = test_credential["credential_id"]
        print(f"🔐 Using test credential: {credential_id}")

        # Test rate limiting scenarios
        scenarios = [
            {
                "name": "Normal usage",
                "requests": 5,
                "endpoint": "/games",
                "ip_address": "192.168.1.100",
                "expected_allowed": True
            },
            {
                "name": "Burst usage",
                "requests": 15,
                "endpoint": "/stats",
                "ip_address": "192.168.1.101",
                "expected_allowed": True
            },
            {
                "name": "Excessive usage",
                "requests": 50,
                "endpoint": "/teams",
                "ip_address": "192.168.1.102",
                "expected_allowed": False
            }
        ]

        for scenario in scenarios:
            print(f"\n📊 Testing: {scenario['name']}")
            allowed_count = 0
            blocked_count = 0

            for i in range(scenario["requests"]):
                request_context = {
                    "ip_address": scenario["ip_address"],
                    "user_agent": "CFBD-Demo-Client/1.0"
                }

                result = await security_manager._enforce_rate_limits({
                    "credential_id": credential_id,
                    "endpoint": scenario["endpoint"],
                    "request_context": request_context
                }, {})

                if result.get("allowed", False):
                    allowed_count += 1
                else:
                    blocked_count += 1
                    print(f"   🚫 Request {i+1} blocked: {result.get('reason', 'Rate limit exceeded')}")
                    if "retry_after" in result:
                        print(f"   ⏰ Retry after: {result['retry_after']} seconds")

                # Small delay to simulate real requests
                await asyncio.sleep(0.01)

            print(f"   📈 Results: {allowed_count} allowed, {blocked_count} blocked")

            # Log rate limiting activity
            await audit_system._log_audit_event({
                "audit_event_data": {
                    "category": "security_events",
                    "severity": "warning" if blocked_count > 0 else "info",
                    "source_system": "cfbd_api_security_manager",
                    "actor_id": credential_id,
                    "actor_type": "api_key",
                    "action": "rate_limit_test",
                    "outcome": "partial_failure" if blocked_count > 0 else "success",
                    "description": f"Rate limiting test '{scenario['name']}': {allowed_count} allowed, {blocked_count} blocked",
                    "resource_type": "api_endpoint",
                    "request_data": {
                        "endpoint": scenario["endpoint"],
                        "total_requests": scenario["requests"],
                        "allowed_requests": allowed_count,
                        "blocked_requests": blocked_count
                    },
                    "ip_address": scenario["ip_address"],
                    "processing_time_ms": 25
                },
                "compliance_tags": ["sox"]
            }, {})

        # Show rate limiting metrics
        metrics = security_manager.get_security_metrics()
        rate_limit_violations = metrics["security_metrics"]["rate_limit_violations"]
        print(f"\n📊 Total rate limit violations: {rate_limit_violations}")

    except Exception as e:
        logger.error(f"Rate limiting demo failed: {e}")
        print(f"❌ Rate limiting demo failed: {e}")

async def demo_threat_detection(security_manager, audit_system):
    """Demonstrate security threat detection"""
    print("\n🛡️  Scenario 3: Security Threat Detection")
    print("-" * 40)

    try:
        print("🔍 Testing threat detection with various attack patterns...")

        # Simulate different threat scenarios
        threat_scenarios = [
            {
                "name": "SQL Injection Attempt",
                "request_pattern": {
                    "endpoint": "/games/search",
                    "method": "POST",
                    "parameters": {
                        "query": "SELECT * FROM games WHERE year = 2025; --",
                        "team": "'; DROP TABLE teams; --"
                    }
                },
                "behavior_analysis": {
                    "requests_per_minute": 5,
                    "user_agent": "sqlmap/1.0",
                    "unique_endpoints": ["/games/search", "/teams/data"]
                },
                "context": {
                    "ip_address": "10.0.0.50",
                    "credential_id": None
                }
            },
            {
                "name": "Brute Force Attack",
                "request_pattern": {
                    "endpoint": "/auth/login",
                    "method": "POST",
                    "parameters": {
                        "username": "admin",
                        "password": "password123"
                    }
                },
                "behavior_analysis": {
                    "requests_per_minute": 200,
                    "user_agent": "Custom-Brute-Force-Tool/1.0",
                    "unique_endpoints": ["/auth/login"]
                },
                "context": {
                    "ip_address": "10.0.0.100",
                    "credential_id": None
                }
            },
            {
                "name": "API Endpoint Enumeration",
                "request_pattern": {
                    "endpoint": "/api/v1/unknown",
                    "method": "GET",
                    "parameters": {}
                },
                "behavior_analysis": {
                    "requests_per_minute": 150,
                    "user_agent": "API-Scanner/2.0",
                    "unique_endpoints": [f"/api/v1/endpoint_{i}" for i in range(1, 31)]
                },
                "context": {
                    "ip_address": "10.0.0.200",
                    "credential_id": None
                }
            }
        ]

        for scenario in threat_scenarios:
            print(f"\n🚨 Testing scenario: {scenario['name']}")

            # Run threat detection
            result = await security_manager._detect_threats({
                "request_pattern": scenario["request_pattern"],
                "behavior_analysis": scenario["behavior_analysis"],
                "context": scenario["context"]
            }, {})

            if result["status"] == "success":
                threat_level = result["threat_level"]
                threats_detected = result["threats_detected"]
                blocked = result["blocked"]

                print(f"   🔍 Threat Level: {threat_level.upper()}")
                print(f"   🚨 Threats Detected: {threats_detected}")
                print(f"   🚫 Blocked: {'YES' if blocked else 'NO'}")

                # Show detected threats
                for i, threat in enumerate(result.get("threats", [])):
                    print(f"   📋 Threat {i+1}: {threat['type']} ({threat['severity']})")
                    if 'description' in threat:
                        print(f"      Details: {threat['description']}")

                # Show recommendations
                recommendations = result.get("recommendations", [])
                if recommendations:
                    print(f"   💡 Recommendations:")
                    for rec in recommendations:
                        print(f"      - {rec}")

                # Log security event
                await audit_system._log_audit_event({
                    "audit_event_data": {
                        "category": "security_events",
                        "severity": "critical" if blocked else "warning",
                        "source_system": "cfbd_api_security_manager",
                        "actor_type": "potential_attacker",
                        "action": "threat_detection",
                        "outcome": "blocked" if blocked else "monitored",
                        "description": f"Threat detected: {scenario['name']} - {threats_detected} threats",
                        "ip_address": scenario["context"]["ip_address"],
                        "request_data": scenario["request_pattern"],
                        "response_data": {
                            "threat_level": threat_level,
                            "threats_detected": threats_detected,
                            "blocked": blocked,
                            "recommendations": recommendations
                        },
                        "processing_time_ms": 100
                    },
                    "compliance_tags": ["gdpr", "hipaa", "sox"]
                }, {})

            else:
                print(f"   ❌ Threat detection failed: {result['error']}")

        # Show security metrics
        metrics = security_manager.get_security_metrics()
        security_alerts = metrics["security_metrics"]["security_alerts_generated"]
        print(f"\n📊 Total security alerts generated: {security_alerts}")

    except Exception as e:
        logger.error(f"Threat detection demo failed: {e}")
        print(f"❌ Threat detection demo failed: {e}")

async def demo_audit_logging(audit_system):
    """Demonstrate comprehensive audit logging"""
    print("\n📝 Scenario 4: Comprehensive Audit Logging")
    print("-" * 40)

    try:
        print("🗂️  Demonstrating different types of audit events...")

        # Create various audit events
        audit_events = [
            {
                "name": "User Authentication",
                "category": "authentication",
                "severity": "info",
                "actor_id": "user_12345",
                "actor_type": "user",
                "action": "login_success",
                "description": "User successfully authenticated via CFBD API",
                "ip_address": "192.168.1.50",
                "user_agent": "CFBD-Client/2.0",
                "compliance_tags": ["gdpr", "sox"],
                "sensitive_data": True
            },
            {
                "name": "Data Access - Games",
                "category": "data_access",
                "severity": "info",
                "actor_id": "api_key_premium_001",
                "actor_type": "api_key",
                "action": "read_games_data",
                "description": "Accessed 2025 college football games data",
                "resource_id": "games_2025",
                "resource_type": "dataset",
                "ip_address": "10.0.1.100",
                "request_data": {"season": 2025, "week": 14},
                "response_data": {"games_count": 50, "data_size_mb": 2.5},
                "compliance_tags": ["gdpr", "hipaa"],
                "processing_time_ms": 350
            },
            {
                "name": "Security Violation",
                "category": "security_events",
                "severity": "error",
                "actor_id": "ip_blocked_001",
                "actor_type": "unknown",
                "action": "unauthorized_access_attempt",
                "description": "Attempted access to restricted endpoint without proper credentials",
                "outcome": "failure",
                "ip_address": "203.0.113.1",
                "resource_type": "api_endpoint",
                "compliance_tags": ["gdpr", "sox", "pci_dss"],
                "requires_encryption": True,
                "metadata": {
                    "threat_type": "unauthorized_access",
                    "blocked_automatically": True,
                    "investigation_required": True
                }
            },
            {
                "name": "System Configuration",
                "category": "configuration",
                "severity": "warning",
                "actor_id": "system_admin",
                "actor_type": "user",
                "action": "rate_limit_policy_update",
                "description": "Updated rate limiting policies for premium tier",
                "resource_type": "security_policy",
                "compliance_tags": ["sox"],
                "metadata": {
                    "old_policy": {"requests_per_hour": 5000},
                    "new_policy": {"requests_per_hour": 10000},
                    "reason": "increased capacity for premium customers"
                }
            },
            {
                "name": "Performance Monitoring",
                "category": "performance",
                "severity": "info",
                "actor_id": "monitoring_system",
                "actor_type": "system",
                "action": "performance_metrics_collection",
                "description": "Collected system performance metrics",
                "metadata": {
                    "cpu_usage": 45.2,
                    "memory_usage": 68.7,
                    "api_response_time_avg_ms": 125,
                    "active_connections": 234
                },
                "processing_time_ms": 15
            }
        ]

        logged_events = []

        for event_data in audit_events:
            print(f"📋 Logging: {event_data['name']}")

            result = await audit_system._log_audit_event({
                "audit_event_data": {
                    "category": event_data["category"],
                    "severity": event_data["severity"],
                    "source_system": "cfbd_security_demo",
                    "actor_id": event_data.get("actor_id"),
                    "actor_type": event_data.get("actor_type"),
                    "action": event_data.get("action"),
                    "outcome": event_data.get("outcome", "success"),
                    "description": event_data["description"],
                    "ip_address": event_data.get("ip_address"),
                    "user_agent": event_data.get("user_agent"),
                    "resource_id": event_data.get("resource_id"),
                    "resource_type": event_data.get("resource_type"),
                    "request_data": event_data.get("request_data", {}),
                    "response_data": event_data.get("response_data", {}),
                    "metadata": event_data.get("metadata", {}),
                    "compliance_tags": event_data.get("compliance_tags", []),
                    "requires_encryption": event_data.get("requires_encryption", False),
                    "sensitive_data": event_data.get("sensitive_data", False),
                    "processing_time_ms": event_data.get("processing_time_ms", 0)
                }
            }, {})

            if result["status"] == "success":
                logged_events.append(result["event_id"])
                print(f"   ✅ Event logged: {result['event_id']}")
                print(f"   🔗 Chain position: {result.get('chain_position', 0)}")
            else:
                print(f"   ❌ Failed to log event: {result['error']}")

        print(f"\n📊 Total audit events logged: {len(logged_events)}")

        # Show audit system metrics
        metrics = audit_system.get_audit_metrics()
        audit_metrics = metrics["audit_metrics"]
        print(f"📈 Audit System Metrics:")
        print(f"   - Events processed: {audit_metrics['events_processed']}")
        print(f"   - Events encrypted: {audit_metrics['events_encrypted']}")
        print(f"   - Files created: {audit_metrics['files_created']}")
        print(f"   - Storage used: {audit_metrics['storage_used_mb']:.2f} MB")
        print(f"   - Category distribution: {metrics['category_distribution']}")
        print(f"   - Severity distribution: {metrics['severity_distribution']}")

    except Exception as e:
        logger.error(f"Audit logging demo failed: {e}")
        print(f"❌ Audit logging demo failed: {e}")

async def demo_compliance_reporting(audit_system):
    """Demonstrate compliance reporting capabilities"""
    print("\n📊 Scenario 5: Compliance Reporting")
    print("-" * 40)

    try:
        print("📋 Generating compliance reports for different frameworks...")

        # Define date range for reports
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        report_frameworks = ["gdpr", "sox", "hipaa", "pci_dss"]

        generated_reports = []

        for framework in report_frameworks:
            print(f"\n🏛️  Generating {framework.upper()} compliance report...")

            result = await audit_system._generate_compliance_report({
                "framework": framework,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "report_format": "json"
            }, {})

            if result["status"] == "success":
                report_info = {
                    "framework": framework,
                    "report_id": result["report_id"],
                    "event_count": result["event_count"],
                    "download_url": result["download_url"]
                }
                generated_reports.append(report_info)

                print(f"   ✅ Report generated: {result['report_id']}")
                print(f"   📊 Events analyzed: {result['event_count']}")
                print(f"   📁 Report saved: {result['download_url']}")

                # Show report summary
                if result.get("report_data"):
                    summary = result["report_data"].get("summary", {})
                    print(f"   📈 Report Summary:")
                    for key, value in summary.items():
                        if isinstance(value, (int, float)):
                            print(f"      - {key}: {value}")
                        elif isinstance(value, list) and len(value) <= 3:
                            print(f"      - {key}: {', '.join(map(str, value))}")
            else:
                print(f"   ❌ Failed to generate {framework} report: {result['error']}")

        print(f"\n📊 Total compliance reports generated: {len(generated_reports)}")

        # Show compliance metrics
        metrics = audit_system.get_audit_metrics()
        compliance_reports = metrics["compliance_reports_count"]
        print(f"📈 Total compliance reports in system: {compliance_reports}")

    except Exception as e:
        logger.error(f"Compliance reporting demo failed: {e}")
        print(f"❌ Compliance reporting demo failed: {e}")

async def demo_forensic_analysis(audit_system):
    """Demonstrate forensic analysis capabilities"""
    print("\n🔍 Scenario 6: Forensic Analysis")
    print("-" * 40)

    try:
        print("🕵️  Performing forensic analysis on audit trails...")

        # Define analysis time range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=24)

        # Different analysis types
        analysis_types = ["timeline", "anomaly", "user_behavior", "security"]

        analysis_results = {}

        for analysis_type in analysis_types:
            print(f"\n🔬 Running {analysis_type} analysis...")

            result = await audit_system._perform_forensic_analysis({
                "analysis_type": analysis_type,
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "filters": {
                    "severity": ["error", "critical"] if analysis_type == "security" else None
                }
            }, {})

            if result["status"] == "success":
                analysis_results[analysis_type] = result
                events_analyzed = result["events_analyzed"]

                print(f"   ✅ Analysis completed: {analysis_type}")
                print(f"   📊 Events analyzed: {events_analyzed}")

                # Show analysis results
                results_data = result.get("analysis_results", {})
                if results_data:
                    print(f"   📋 Analysis Results:")

                    if analysis_type == "timeline":
                        summary = results_data.get("summary", {})
                        print(f"      - Time span: {summary.get('time_span_hours', 0):.1f} hours")
                        print(f"      - Events per hour: {summary.get('events_per_hour', 0):.1f}")

                    elif analysis_type == "anomaly":
                        summary = results_data.get("summary", {})
                        print(f"      - Total anomalies: {summary.get('total_anomalies', 0)}")
                        print(f"      - High severity: {summary.get('high_severity', 0)}")
                        print(f"      - Medium severity: {summary.get('medium_severity', 0)}")

                    elif analysis_type == "user_behavior":
                        summary = results_data.get("summary", {})
                        print(f"      - Total users: {summary.get('total_users', 0)}")
                        print(f"      - High risk users: {summary.get('high_risk_users', 0)}")

                    elif analysis_type == "security":
                        print(f"      - Security events: {results_data.get('security_events', 0)}")
                        print(f"      - Attack patterns: {len(results_data.get('attack_patterns', []))}")
                        print(f"      - Vulnerabilities: {len(results_data.get('vulnerabilities', []))}")

                # Show evidence chains
                evidence_chains = result.get("evidence_chains", [])
                if evidence_chains:
                    print(f"   ⛓️  Evidence chains found: {len(evidence_chains)}")
                    for chain in evidence_chains[:2]:  # Show first 2
                        print(f"      - {chain.get('summary', 'No summary')}")

                # Show recommendations
                recommendations = result.get("recommendations", [])
                if recommendations:
                    print(f"   💡 Recommendations: {len(recommendations)}")
                    for rec in recommendations[:2]:  # Show first 2
                        print(f"      - {rec}")

            else:
                print(f"   ❌ {analysis_type} analysis failed: {result['error']}")

        print(f"\n📊 Total forensic analyses completed: {len(analysis_results)}")

        # Show forensic metrics
        metrics = audit_system.get_audit_metrics()
        forensic_queries = metrics["audit_metrics"]["forensic_queries_handled"]
        print(f"🔍 Total forensic queries handled: {forensic_queries}")

    except Exception as e:
        logger.error(f"Forensic analysis demo failed: {e}")
        print(f"❌ Forensic analysis demo failed: {e}")

async def show_security_status(security_manager, audit_system):
    """Show final security system status"""
    try:
        print("📊 Final Security System Status:")
        print("-" * 30)

        # Security manager metrics
        security_metrics = security_manager.get_security_metrics()
        sec_metrics = security_metrics["security_metrics"]
        print(f"🔐 Security Manager:")
        print(f"   - Requests processed: {sec_metrics['requests_processed']}")
        print(f"   - Requests blocked: {sec_metrics['requests_blocked']}")
        print(f"   - Rate limit violations: {sec_metrics['rate_limit_violations']}")
        print(f"   - Auth failures: {sec_metrics['auth_failures']}")
        print(f"   - Security alerts: {sec_metrics['security_alerts_generated']}")
        print(f"   - Active credentials: {security_metrics['credentials_count']}")
        print(f"   - Blocked IPs: {security_metrics['blocked_ips_count']}")

        # Audit system metrics
        audit_metrics = audit_system.get_audit_metrics()
        aud_metrics = audit_metrics["audit_metrics"]
        print(f"\n📝 Audit System:")
        print(f"   - Events processed: {aud_metrics['events_processed']}")
        print(f"   - Events encrypted: {aud_metrics['events_encrypted']}")
        print(f"   - Files created: {aud_metrics['files_created']}")
        print(f"   - Storage used: {aud_metrics['storage_used_mb']:.2f} MB")
        print(f"   - Compliance reports: {audit_metrics['compliance_reports_count']}")
        print(f"   - Forensic queries: {aud_metrics['forensic_queries_handled']}")
        print(f"   - Event chains: {audit_metrics['event_chains_count']}")

        # Category and severity distribution
        category_dist = audit_metrics["category_distribution"]
        severity_dist = audit_metrics["severity_distribution"]

        print(f"\n📊 Event Distribution:")
        if category_dist:
            print(f"   Categories: {dict(category_dist)}")
        if severity_dist:
            print(f"   Severities: {dict(severity_dist)}")

        print(f"\n⏰ Status timestamp: {datetime.now(timezone.utc).isoformat()}")

    except Exception as e:
        logger.error(f"Failed to show security status: {e}")
        print(f"❌ Failed to show security status: {e}")

async def main():
    """Main demonstration function"""
    print("🛡️ CFBD API Security and Audit System Demo")
    print("=" * 50)
    print("This demonstration shows enterprise-grade API security,")
    print("rate limiting, comprehensive audit logging, compliance")
    print("reporting, and forensic analysis capabilities.")
    print()

    await demo_cfbd_security_audit()

if __name__ == "__main__":
    asyncio.run(main())