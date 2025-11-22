#!/usr/bin/env python3
"""
CFBD Integration KPI Dashboard
📊 Web-based dashboard for real-time KPI monitoring
📈 Interactive charts and visualizations
🎯 Live updates and alerting

Author: Script Ohio 2.0 Agent System
Version: 1.0.0
Created: 2025-01-14
"""

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict

try:
    from flask import Flask, render_template_string, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available - dashboard will run in static mode")

from kpi_tracker import kpi_tracker, get_project_overview, generate_dashboard

class KPIDashboard:
    """KPI Dashboard for CFBD Integration Project"""

    def __init__(self, port: int = 5000, debug: bool = False):
        self.port = port
        self.debug = debug
        self.app = None
        self.socketio = None
        self.update_thread = None
        self.running = False

        if FLASK_AVAILABLE:
            self._setup_flask_app()

    def _setup_flask_app(self):
        """Setup Flask application for web dashboard"""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'cfbd-kpi-dashboard-secret'

        # Setup SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Routes
        self.app.route('/')(self.index)
        self.app.route('/api/kpi-data')(self.get_kpi_data)
        self.app.route('/api/overview')(self.get_overview)
        self.app.route('/api/update-kpi', methods=['POST'])(self.update_kpi)
        self.app.route('/api/update-phase', methods=['POST'])(self.update_phase)

        # SocketIO events
        self.socketio.on('connect')(self.handle_connect)
        self.socketio.on('disconnect')(self.handle_disconnect)

        logger.info("📊 Flask dashboard app configured")

    def index(self):
        """Main dashboard page"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CFBD Integration KPI Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .status-bar {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
        }

        .status-healthy { background: #d4edda; color: #155724; }
        .status-degraded { background: #fff3cd; color: #856404; }
        .status-critical { background: #f8d7da; color: #721c24; }

        .content {
            padding: 30px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        .kpi-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }

        .kpi-card.target-met {
            border-left-color: #28a745;
        }

        .kpi-card.target-missed {
            border-left-color: #dc3545;
        }

        .kpi-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }

        .kpi-value {
            font-size: 2.2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .kpi-unit {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }

        .kpi-target {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 15px;
        }

        .kpi-trend {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9em;
            font-weight: bold;
        }

        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-stable { color: #6c757d; }

        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        .chart-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .chart-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        }

        .phase-progress {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 25px;
        }

        .phase-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        }

        .phase-item {
            margin-bottom: 20px;
        }

        .phase-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }

        .progress-bar {
            width: 100%;
            height: 25px;
            background: #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }

        .alerts-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .alert-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }

        .alert-critical {
            background: #f8d7da;
            border-color: #721c24;
        }

        .alert-high {
            background: #fcf8e3;
            border-color: #8a6d3b;
        }

        .alert-medium {
            background: #d1ecf1;
            border-color: #0c5460;
        }

        .alert-low {
            background: #d4edda;
            border-color: #155724;
        }

        .timestamp {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }

        .controls {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        }

        .control-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            margin: 5px;
            font-weight: bold;
            transition: background 0.3s ease;
        }

        .control-button:hover {
            background: #5a67d8;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: bold;
            z-index: 1000;
        }

        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🏈 CFBD Integration KPI Dashboard</h1>
            <p>Real-time monitoring of CFBD integration enhancement project</p>
        </div>

        <div class="status-bar">
            <div class="status-indicator" id="overall-status">
                <span id="status-text">Loading...</span>
            </div>
            <div>
                Last updated: <span id="last-updated">Loading...</span>
            </div>
        </div>

        <div class="content">
            <div class="kpi-grid" id="kpi-grid">
                <!-- KPI cards will be populated by JavaScript -->
            </div>

            <div class="phase-progress">
                <div class="phase-title">📋 Phase Progress</div>
                <div id="phase-progress-container">
                    <!-- Phase progress will be populated by JavaScript -->
                </div>
            </div>

            <div class="charts-section">
                <div class="chart-card">
                    <div class="chart-title">📈 KPI Trends (24h)</div>
                    <canvas id="trends-chart" height="200"></canvas>
                </div>
                <div class="chart-card">
                    <div class="chart-title">🎯 Target Achievement</div>
                    <canvas id="targets-chart" height="200"></canvas>
                </div>
            </div>

            <div class="alerts-section">
                <div class="chart-title">🚨 Active Alerts</div>
                <div id="alerts-container">
                    <!-- Alerts will be populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>

    <div class="connection-status" id="connection-status">
        🔌 Connecting...
    </div>

    <div class="controls">
        <button class="control-button" onclick="refreshData()">🔄 Refresh</button>
        <button class="control-button" onclick="exportData()">📊 Export</button>
    </div>

    <script>
        // Global variables
        let socket;
        let dashboardData = {};
        let trendsChart = null;
        let targetsChart = null;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeSocket();
            loadInitialData();
            initializeCharts();
        });

        function initializeSocket() {
            socket = io();

            socket.on('connect', function() {
                updateConnectionStatus(true);
                console.log('Connected to dashboard server');
            });

            socket.on('disconnect', function() {
                updateConnectionStatus(false);
                console.log('Disconnected from dashboard server');
            });

            socket.on('kpi_update', function(data) {
                updateKPI(data.kpi_name, data.value, data.metadata);
            });

            socket.on('dashboard_update', function(data) {
                updateDashboard(data);
            });
        }

        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connection-status');
            if (connected) {
                statusElement.textContent = '🟢 Connected';
                statusElement.className = 'connection-status connected';
            } else {
                statusElement.textContent = '🔴 Disconnected';
                statusElement.className = 'connection-status disconnected';
            }
        }

        async function loadInitialData() {
            try {
                const response = await fetch('/api/kpi-data');
                dashboardData = await response.json();
                updateDashboard(dashboardData);
            } catch (error) {
                console.error('Error loading initial data:', error);
                loadStaticData();
            }
        }

        function loadStaticData() {
            // Fallback static data for when API is not available
            dashboardData = {
                overview: {
                    timestamp: new Date().toISOString(),
                    overall_health: 'healthy',
                    active_alerts: 0,
                    critical_alerts: 0
                },
                kpi_details: {
                    agent_compliance: {
                        summary: { current_value: 75, target: 100, target_met: false, trend: 'stable' },
                        definition: { name: 'Agent Compliance', unit: 'percent' }
                    },
                    dataset_coverage: {
                        summary: { current_value: 8, target: 12, target_met: false, trend: 'stable' },
                        definition: { name: 'Dataset Coverage', unit: 'datasets' }
                    },
                    api_error_rate: {
                        summary: { current_value: 0.3, target: 0.5, target_met: true, trend: 'stable' },
                        definition: { name: 'API Error Rate', unit: 'percent' }
                    },
                    rate_limit_breaches: {
                        summary: { current_value: 0, target: 0, target_met: true, trend: 'stable' },
                        definition: { name: 'Rate Limit Breaches', unit: 'count' }
                    }
                },
                phase_details: {
                    'phase_0_foundation': { progress: 60, last_updated: new Date().toISOString() }
                },
                alerts: []
            };
            updateDashboard(dashboardData);
        }

        function updateDashboard(data) {
            dashboardData = data;
            updateKPIGrid();
            updatePhaseProgress();
            updateStatus();
            updateAlerts();
            updateCharts();
            updateLastUpdated();
        }

        function updateKPIGrid() {
            const kpiGrid = document.getElementById('kpi-grid');
            const kpis = dashboardData.kpi_details || {};

            kpiGrid.innerHTML = '';

            Object.entries(kpis).forEach(([kpiName, kpiData]) => {
                const summary = kpiData.summary || {};
                const definition = kpiData.definition || {};

                const card = document.createElement('div');
                card.className = `kpi-card ${summary.target_met ? 'target-met' : 'target-missed'}`;

                card.innerHTML = `
                    <div class="kpi-title">${definition.name || kpiName}</div>
                    <div class="kpi-value">${summary.current_value || 0}</div>
                    <div class="kpi-unit">${definition.unit || ''}</div>
                    <div class="kpi-target">Target: ${summary.target || 0}</div>
                    <div class="kpi-trend ${getTrendClass(summary.trend)}">
                        ${getTrendIcon(summary.trend)} ${summary.trend || 'stable'}
                    </div>
                `;

                kpiGrid.appendChild(card);
            });
        }

        function updatePhaseProgress() {
            const container = document.getElementById('phase-progress-container');
            const phases = dashboardData.phase_details || {};

            container.innerHTML = '';

            Object.entries(phases).forEach(([phaseName, phaseData]) => {
                const phaseItem = document.createElement('div');
                phaseItem.className = 'phase-item';

                phaseItem.innerHTML = `
                    <div class="phase-name">${formatPhaseName(phaseName)}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${phaseData.progress}%">
                            ${phaseData.progress}%
                        </div>
                    </div>
                `;

                container.appendChild(phaseItem);
            });
        }

        function updateStatus() {
            const statusElement = document.getElementById('overall-status');
            const statusText = document.getElementById('status-text');
            const overview = dashboardData.overview || {};

            let statusClass = 'status-healthy';
            let statusText = 'Healthy';

            if (overview.critical_alerts > 0) {
                statusClass = 'status-critical';
                statusText = 'Critical';
            } else if (overview.active_alerts > 0) {
                statusClass = 'status-degraded';
                statusText = 'Degraded';
            }

            statusElement.className = `status-indicator ${statusClass}`;
            statusText.textContent = `${statusText} (${overview.active_alerts || 0} alerts)`;
        }

        function updateAlerts() {
            const container = document.getElementById('alerts-container');
            const alerts = dashboardData.alerts || [];

            if (alerts.length === 0) {
                container.innerHTML = '<p style="color: #666; text-align: center;">No active alerts</p>';
                return;
            }

            container.innerHTML = '';

            alerts.forEach(alert => {
                const alertItem = document.createElement('div');
                alertItem.className = `alert-item alert-${alert.severity}`;

                alertItem.innerHTML = `
                    <div><strong>${alert.kpi_name}</strong></div>
                    <div>${alert.message}</div>
                    <div class="timestamp">${new Date(alert.timestamp).toLocaleString()}</div>
                `;

                container.appendChild(alertItem);
            });
        }

        function updateLastUpdated() {
            const element = document.getElementById('last-updated');
            const timestamp = dashboardData.overview?.timestamp || new Date().toISOString();
            element.textContent = new Date(timestamp).toLocaleString();
        }

        function initializeCharts() {
            // Initialize trends chart
            const trendsCtx = document.getElementById('trends-chart').getContext('2d');
            trendsChart = new Chart(trendsCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });

            // Initialize targets chart
            const targetsCtx = document.getElementById('targets-chart').getContext('2d');
            targetsChart = new Chart(targetsCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Current',
                        data: [],
                        backgroundColor: '#667eea'
                    }, {
                        label: 'Target',
                        data: [],
                        backgroundColor: '#28a745'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });

            updateCharts();
        }

        function updateCharts() {
            if (!trendsChart || !targetsChart) return;

            // Update targets chart
            const kpis = dashboardData.kpi_details || {};
            const labels = [];
            const currentValues = [];
            const targetValues = [];

            Object.entries(kpis).forEach(([kpiName, kpiData]) => {
                const summary = kpiData.summary || {};
                const definition = kpiData.definition || {};

                labels.push(definition.name || kpiName);
                currentValues.push(summary.current_value || 0);
                targetValues.push(summary.target || 0);
            });

            targetsChart.data.labels = labels;
            targetsChart.data.datasets[0].data = currentValues;
            targetsChart.data.datasets[1].data = targetValues;
            targetsChart.update();
        }

        function getTrendClass(trend) {
            switch (trend) {
                case 'improving': return 'trend-up';
                case 'degrading': return 'trend-down';
                default: return 'trend-stable';
            }
        }

        function getTrendIcon(trend) {
            switch (trend) {
                case 'improving': return '📈';
                case 'degrading': return '📉';
                default: return '➡️';
            }
        }

        function formatPhaseName(phaseName) {
            return phaseName.split('_').map(word =>
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }

        async function refreshData() {
            try {
                const response = await fetch('/api/kpi-data');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }

        function exportData() {
            const dataStr = JSON.stringify(dashboardData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

            const exportFileDefaultName = `cfbd-kpi-dashboard-${new Date().toISOString().split('T')[0]}.json`;

            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
        }

        async function updateKPI(kpiName, value, metadata) {
            try {
                const response = await fetch('/api/update-kpi', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        kpi_name: kpiName,
                        value: value,
                        metadata: metadata
                    })
                });

                if (response.ok) {
                    refreshData();
                }
            } catch (error) {
                console.error('Error updating KPI:', error);
            }
        }
    </script>
</body>
</html>
        """
        return render_template_string(html_template)

    def get_kpi_data(self):
        """API endpoint to get KPI data"""
        try:
            data = generate_dashboard()
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_overview(self):
        """API endpoint to get project overview"""
        try:
            overview = get_project_overview()
            return jsonify(overview)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def update_kpi(self):
        """API endpoint to update KPI value"""
        try:
            data = request.json
            kpi_name = data.get("kpi_name")
            value = data.get("value")
            metadata = data.get("metadata", {})

            result = kpi_tracker.record_kpi(kpi_name, value, metadata, "dashboard")

            # Broadcast update to connected clients
            if self.socketio:
                self.socketio.emit("kpi_update", {
                    "kpi_name": kpi_name,
                    "value": value,
                    "metadata": metadata
                })

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def update_phase(self):
        """API endpoint to update phase progress"""
        try:
            data = request.json
            phase_name = data.get("phase_name")
            progress = data.get("progress")
            metadata = data.get("metadata", {})

            result = kpi_tracker.update_phase_progress(phase_name, progress, metadata)

            # Broadcast update to connected clients
            if self.socketio:
                self.socketio.emit("phase_update", {
                    "phase_name": phase_name,
                    "progress": progress,
                    "metadata": metadata
                })

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def handle_connect(self):
        """Handle client connection"""
        logger.info("📊 Dashboard client connected")
        emit("connected", {"message": "Connected to CFBD KPI Dashboard"})

    def handle_disconnect(self):
        """Handle client disconnection"""
        logger.info("📊 Dashboard client disconnected")

    def run(self):
        """Run the dashboard server"""
        if not FLASK_AVAILABLE:
            logger.error("Flask not available - cannot run web dashboard")
            return False

        if not self.app or not self.socketio:
            logger.error("Flask app not properly initialized")
            return False

        try:
            self.running = True
            self.start_update_thread()

            logger.info(f"📊 Starting KPI Dashboard on port {self.port}")

            self.socketio.run(
                self.app,
                host="0.0.0.0",
                port=self.port,
                debug=self.debug,
                allow_unsafe_werkzeug=True
            )

            return True

        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
            return False

    def start_update_thread(self):
        """Start background thread for periodic updates"""
        def update_loop():
            while self.running:
                try:
                    # Broadcast dashboard updates
                    if self.socketio:
                        data = generate_dashboard()
                        self.socketio.emit("dashboard_update", data)

                    time.sleep(30)  # Update every 30 seconds

                except Exception as e:
                    logger.error(f"Error in dashboard update loop: {e}")
                    time.sleep(30)

        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()

    def stop(self):
        """Stop the dashboard server"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("📊 KPI Dashboard stopped")

# Convenience functions
def create_dashboard(port: int = 5000, debug: bool = False) -> KPIDashboard:
    """Create and return KPI dashboard instance"""
    return KPIDashboard(port=port, debug=debug)

def run_dashboard(port: int = 5000, debug: bool = False):
    """Run the KPI dashboard"""
    dashboard = create_dashboard(port, debug)
    return dashboard.run()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Create and run dashboard
    dashboard = KPIDashboard(port=5000, debug=True)

    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("\\n📊 Dashboard stopped by user")
        dashboard.stop()