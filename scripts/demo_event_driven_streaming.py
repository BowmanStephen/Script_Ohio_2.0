#!/usr/bin/env python3
"""
Event-Driven Streaming Architecture Demonstration
Shows how the complete data pipeline works with real-time events
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_event_driven_streaming():
    """Demonstrate the complete event-driven streaming architecture"""

    print("🚀 Event-Driven Streaming Architecture Demonstration")
    print("=" * 60)

    try:
        # Import streaming components
        from agents.core.streaming_integration_config import initialize_streaming_system, get_streaming_config
        from agents.core.event_stream_manager import Event, EventPriority

        # Initialize the streaming system
        print("\n📡 Initializing Streaming System...")
        init_result = await initialize_streaming_system()

        if init_result["status"] != "success":
            print(f"❌ Failed to initialize streaming system: {init_result['error']}")
            return

        print(f"✅ Streaming system initialized successfully!")
        print(f"   - Event Backend: {init_result['event_backend']}")
        print(f"   - Components: {', '.join(init_result['components_initialized'])}")
        print(f"   - Pipeline Configs: {init_result['pipeline_configs']}")

        # Get the streaming configuration and components
        streaming_config = get_streaming_config()
        event_manager = streaming_config.components.get("event_manager")
        pipeline_orchestrator = streaming_config.components.get("data_pipeline_orchestrator")
        data_monitor = streaming_config.components.get("data_flow_monitor")

        if not all([event_manager, pipeline_orchestrator, data_monitor]):
            print("❌ Not all components were initialized properly")
            return

        print("\n🎯 Starting Demonstration Scenarios...")

        # Scenario 1: CFBD Data Ingestion Pipeline
        await demo_cfbd_data_ingestion(event_manager, pipeline_orchestrator)

        # Scenario 2: Real-time Game Updates
        await demo_realtime_updates(event_manager, data_monitor)

        # Scenario 3: Pipeline Health Monitoring
        await demo_health_monitoring(data_monitor, pipeline_orchestrator)

        # Scenario 4: Alert System
        await demo_alert_system(event_manager, data_monitor)

        print("\n📊 Final System Status...")
        await show_system_status(streaming_config)

    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        print(f"❌ Demonstration failed: {e}")

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if 'streaming_config' in locals():
            await streaming_config.shutdown()
        print("✅ Cleanup complete")

async def demo_cfbd_data_ingestion(event_manager, pipeline_orchestrator):
    """Demonstrate CFBD data ingestion through the pipeline"""
    print("\n🏈 Scenario 1: CFBD Data Ingestion Pipeline")
    print("-" * 40)

    try:
        # Start a CFBD data processing pipeline
        print("📥 Starting CFBD data processing pipeline...")
        pipeline_result = await pipeline_orchestrator._coordinate_pipeline_execution({
            "pipeline_name": "cfbd_data_processing",
            "data_source": "cfbd_api",
            "batch_size": 50
        }, {})

        if pipeline_result["status"] == "success":
            pipeline_id = pipeline_result["pipeline_id"]
            print(f"✅ Pipeline started: {pipeline_id}")

            # Simulate CFBD data events
            await simulate_cfbd_events(event_manager, pipeline_id)

            # Wait for pipeline processing
            await asyncio.sleep(2)

            # Check pipeline status
            pipeline_instance = pipeline_orchestrator.pipeline_instances.get(pipeline_id)
            if pipeline_instance:
                print(f"📊 Pipeline Status: {pipeline_instance['status']}")
                print(f"   - Created: {pipeline_instance['created_at']}")
                print(f"   - Batches Processed: {pipeline_instance['batches_processed']}")
                print(f"   - Total Processing Time: {pipeline_instance['total_processing_time']:.2f}s")

        else:
            print(f"❌ Pipeline failed to start: {pipeline_result['error']}")

    except Exception as e:
        logger.error(f"CFBD ingestion demo failed: {e}")
        print(f"❌ CFBD ingestion demo failed: {e}")

async def simulate_cfbd_events(event_manager, pipeline_id: str):
    """Simulate CFBD data events"""
    print("📡 Simulating CFBD data events...")

    # Simulate data retrieval event
    data_retrieved_event = Event(
        type="cfbd.data.retrieved",
        source="cfbd_integration_agent",
        data={
            "batch_id": f"cfbd_batch_{int(time.time())}",
            "pipeline_id": pipeline_id,
            "data": {
                "games_count": 50,
                "teams_count": 130,
                "season": 2025,
                "week": 14
            },
            "quality_indicators": {
                "completeness": 0.95,
                "accuracy": 0.98,
                "freshness": 0.99
            }
        },
        priority=EventPriority.HIGH
    )
    await event_manager.publish_event(data_retrieved_event)

    await asyncio.sleep(0.5)

    # Simulate validation completion
    validation_event = Event(
        type="validation.completed",
        source="data_validation_agent",
        data={
            "batch_id": f"cfbd_batch_{int(time.time())}",
            "pipeline_id": pipeline_id,
            "results": {
                "overall_score": 0.92,
                "schema_valid": True,
                "quality_level": "high",
                "errors": [],
                "warnings": ["Missing weather data for 3 games"]
            }
        },
        priority=EventPriority.NORMAL
    )
    await event_manager.publish_event(validation_event)

    await asyncio.sleep(0.5)

    # Simulate stage completion
    stage_event = Event(
        type="stage.completed",
        source="data_pipeline_orchestrator",
        data={
            "pipeline_id": pipeline_id,
            "stage": "validation",
            "processing_time": 1.2,
            "result": {"status": "success", "records_validated": 50}
        },
        priority=EventPriority.NORMAL
    )
    await event_manager.publish_event(stage_event)

async def demo_realtime_updates(event_manager, data_monitor):
    """Demonstrate real-time game updates"""
    print("\n⚡ Scenario 2: Real-time Game Updates")
    print("-" * 40)

    try:
        print("📡 Simulating real-time game updates...")

        # Simulate live game score updates
        games = [
            {"id": "401752911", "home": "Oregon", "away": "USC", "home_score": 24, "away_score": 21, "quarter": 3},
            {"id": "401752912", "home": "Alabama", "away": "Georgia", "home_score": 17, "away_score": 14, "quarter": 2},
            {"id": "401752913", "home": "Ohio State", "away": "Michigan", "home_score": 28, "away_score": 28, "quarter": 4}
        ]

        for i, game in enumerate(games):
            # Create live score update event
            score_event = Event(
                type="game.score.update",
                source="cfbd_websocket",
                data={
                    "game_id": game["id"],
                    "home_team": game["home"],
                    "away_team": game["away"],
                    "home_score": game["home_score"],
                    "away_score": game["away_score"],
                    "quarter": game["quarter"],
                    "time_remaining": f"{4-game['quarter']}:15",
                    "possession": "home" if i % 2 == 0 else "away"
                },
                priority=EventPriority.HIGH
            )
            await event_manager.publish_event(score_event)
            print(f"🏈 Score Update: {game['home']} {game['home_score']} - {game['away']} {game['away_score']} (Q{game['quarter']})")

            await asyncio.sleep(0.3)

        # Monitor performance impact
        performance_result = await data_monitor._monitor_pipeline_performance({
            "pipeline_ids": ["realtime_game_updates"],
            "metric_types": ["throughput", "latency"],
            "time_window": "1m"
        }, {})

        if performance_result["status"] == "success":
            metrics = performance_result["performance_metrics"]
            print("📊 Real-time Processing Metrics:")
            print(f"   - Throughput: {metrics.get('throughput', {}).get('current', 0):.1f} updates/min")
            print(f"   - Latency: {metrics.get('latency', {}).get('current', 0):.2f} seconds")

    except Exception as e:
        logger.error(f"Real-time updates demo failed: {e}")
        print(f"❌ Real-time updates demo failed: {e}")

async def demo_health_monitoring(data_monitor, pipeline_orchestrator):
    """Demonstrate health monitoring capabilities"""
    print("\n🏥 Scenario 3: Pipeline Health Monitoring")
    print("-" * 40)

    try:
        print("🔍 Monitoring system health...")

        # Generate comprehensive health report
        health_result = await data_monitor._generate_health_report({
            "report_type": "comprehensive",
            "components": ["all"],
            "time_range": "1h"
        }, {})

        if health_result["status"] == "success":
            health_report = health_result["health_report"]
            print("📊 System Health Report:")
            print(f"   - Overall Health: {health_report['overall_health']}")
            print(f"   - Health Score: {health_report['health_score']:.2f}/1.0")
            print(f"   - Active Alerts: {len(health_report['active_alerts'])}")

            # Component health
            component_health = health_report.get("component_health", {})
            for component, health in component_health.items():
                status = health.get("status", "unknown")
                score = health.get("health_score", 0)
                issues = health.get("issues", [])
                print(f"   - {component.title()}: {status} ({score:.2f})")
                if issues:
                    for issue in issues[:2]:  # Show first 2 issues
                        print(f"     ⚠️  {issue}")

            # Recommendations
            recommendations = health_report.get("recommendations", [])
            if recommendations:
                print("   💡 Recommendations:")
                for rec in recommendations[:3]:  # Show first 3 recommendations
                    priority = rec.get("priority", "medium")
                    recommendation = rec.get("recommendation", "")
                    print(f"     - {priority.title()}: {recommendation}")

        # Monitor specific pipeline performance
        performance_result = await data_monitor._monitor_pipeline_performance({
            "metric_types": ["quality", "error_rate", "throughput"],
            "time_window": "15m"
        }, {})

        if performance_result["status"] == "success":
            metrics = performance_result["performance_metrics"]
            print("\n📈 Performance Metrics:")
            for metric_name, metric_data in metrics.items():
                current = metric_data.get("current", 0)
                average = metric_data.get("average", 0)
                print(f"   - {metric_name.title()}: {current:.2f} (avg: {average:.2f})")

    except Exception as e:
        logger.error(f"Health monitoring demo failed: {e}")
        print(f"❌ Health monitoring demo failed: {e}")

async def demo_alert_system(event_manager, data_monitor):
    """Demonstrate alert system functionality"""
    print("\n🚨 Scenario 4: Alert System")
    print("-" * 40)

    try:
        print("🔔 Setting up and triggering alerts...")

        # Create a custom alert rule
        alert_config = {
            "name": "Demo High Processing Time Alert",
            "description": "Alert when processing time exceeds demo threshold",
            "metric_name": "end_to_end_latency",
            "condition": "gt",
            "threshold": 45.0,
            "severity": "warning"
        }

        create_result = await data_monitor._manage_alerts({
            "action": "create_rule",
            "alert_config": alert_config
        }, {})

        if create_result["status"] == "success":
            print(f"✅ Alert rule created: {create_result['rule_id']}")

        # Simulate high processing time to trigger alert
        high_latency_event = Event(
            type="stage.completed",
            source="demo_component",
            data={
                "pipeline_id": "demo_pipeline",
                "stage": "transformation",
                "processing_time": 50.5,  # Above threshold
                "result": {"status": "success", "latency_high": True}
            },
            priority=EventPriority.NORMAL
        )
        await event_manager.publish_event(high_latency_event)

        # Wait for alert evaluation
        await asyncio.sleep(2)

        # Check for triggered alerts
        alerts_result = await data_monitor._manage_alerts({
            "action": "list_alerts",
            "severity": "warning"
        }, {})

        if alerts_result["status"] == "success":
            active_alerts = alerts_result.get("active_alerts", 0)
            alerts = alerts_result.get("alerts", [])
            print(f"🚨 Active Alerts: {active_alerts}")

            for alert in alerts:
                print(f"   - {alert['severity'].upper()}: {alert['message']}")
                print(f"     Triggered: {alert['triggered_at']}")

                # Acknowledge the alert
                acknowledge_result = await data_monitor._manage_alerts({
                    "action": "acknowledge_alert",
                    "alert_id": alert['alert_id']
                }, {})

                if acknowledge_result["status"] == "success":
                    print(f"   ✅ Alert acknowledged")

        # List all alert rules
        rules_result = await data_monitor._manage_alerts({
            "action": "list_rules"
        }, {})

        if rules_result["status"] == "success":
            rules = rules_result.get("rules", [])
            print(f"\n📋 Alert Rules: {len(rules)}")
            for rule in rules:
                enabled_status = "✅" if rule.get("enabled", True) else "❌"
                print(f"   {enabled_status} {rule['name']} ({rule['severity']})")

    except Exception as e:
        logger.error(f"Alert system demo failed: {e}")
        print(f"❌ Alert system demo failed: {e}")

async def show_system_status(streaming_config):
    """Show final system status"""
    try:
        print("📊 Final System Status:")
        print("-" * 25)

        status = streaming_config.get_system_status()

        print(f"🔗 Event Manager: {'✅' if status['event_manager_initialized'] else '❌'}")
        print(f"🌐 Event Backend: {status['event_backend']}")
        print(f"🔧 Active Components: {len(status['components_active'])}")

        for component in status['components_active']:
            print(f"   - {component}")

        # Show event stream metrics
        event_manager = streaming_config.components.get("event_manager")
        if event_manager:
            metrics = event_manager.get_metrics()
            event_metrics = metrics["performance_metrics"]
            print(f"\n📡 Event Stream Metrics:")
            print(f"   - Events Published: {event_metrics['events_published']}")
            print(f"   - Events Processed: {event_metrics['events_processed']}")
            print(f"   - Events Failed: {event_metrics['events_failed']}")
            print(f"   - Avg Processing Time: {event_metrics['average_processing_time']:.3f}s")
            print(f"   - Buffer Utilization: {event_metrics['buffer_utilization']:.1%}")

        print(f"\n⏰ Configuration Timestamp: {status['config_timestamp']}")

    except Exception as e:
        logger.error(f"Failed to show system status: {e}")
        print(f"❌ Failed to show system status: {e}")

async def main():
    """Main demonstration function"""
    print("🎭 Event-Driven Streaming Architecture Demo")
    print("=" * 50)
    print("This demonstration shows how the complete event-driven")
    print("data pipeline works with real-time events, monitoring,")
    print("and alerting capabilities.")
    print()

    await demo_event_driven_streaming()

if __name__ == "__main__":
    asyncio.run(main())