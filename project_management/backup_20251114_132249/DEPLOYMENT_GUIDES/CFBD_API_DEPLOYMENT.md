# CFBD API Deployment Guide
**Production Deployment Guide for Script Ohio 2.0 CFBD Integration**

---

## 📋 Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Environment Configuration](#environment-configuration)
3. [Production Setup](#production-setup)
4. [Security & API Management](#security--api-management)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Scaling & Performance](#scaling--performance)
7. [Disaster Recovery](#disaster-recovery)
8. [Maintenance & Updates](#maintenance--updates)

---

## 🚀 Deployment Overview

### Architecture Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Script Ohio 2.0 System                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Agent System │  │  ML Models      │  │ CFBD API    │ │
│  │   (92% ready)   │  │  (3 models)     │  │ Integration │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Cache Layer     │  │ Quality Assur-  │  │ Mock Data   │ │
│  │ (Redis/Local)   │  │ ance Framework  │  │ Fallback    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Environments
- **Development**: Local development with sandbox API access
- **Staging**: Pre-production environment for testing
- **Production**: Live environment for Week 12 predictions

### Key Deployment Metrics
- **Target Uptime**: 99.5% during peak usage
- **API Response Time**: <2 seconds for predictions
- **Data Freshness**: <1 hour for current season data
- **Error Rate**: <1% for all API operations

---

## ⚙️ Environment Configuration

### Environment Variables
```bash
# .env.production
# CFBD API Configuration
CFBD_API_KEY=your_production_api_key_here
CFBD_BASE_URL=https://api.collegefootballdata.com
CFBD_RATE_LIMIT_DELAY=0.5
CFBD_TIMEOUT=30
CFBD_CACHE_TTL=3600

# System Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Cache Configuration
CFBD_CACHE_DIR=/app/cache/cfbd
CACHE_ENABLED=true
CACHE_TYPE=redis  # or 'local' for file-based caching

# Monitoring Configuration
MONITORING_ENABLED=true
METRICS_PORT=8080
HEALTH_CHECK_PORT=8081

# Security Configuration
API_KEY_ROTATION_ENABLED=true
API_KEY_EXPIRY_DAYS=90
RATE_LIMIT_BURST=10
RATE_LIMIT_SUSTAINED=200

# Performance Configuration
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0

# Fallback Configuration
MOCK_DATA_FALLBACK_ENABLED=true
MOCK_DATA_PATH=/app/data/mock
DATA_QUALITY_THRESHOLD=0.95
```

### Configuration Management
```python
# config/production_config.py
import os
import logging
from typing import Dict, Any

class ProductionConfig:
    """Production environment configuration"""

    def __init__(self):
        self.load_environment_variables()
        self.setup_logging()

    def load_environment_variables(self):
        """Load and validate environment variables"""

        required_vars = [
            'CFBD_API_KEY',
            'ENVIRONMENT',
            'CFBD_CACHE_DIR'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        self.CFBD_API_KEY = os.getenv('CFBD_API_KEY')
        self.CFBD_BASE_URL = os.getenv('CFBD_BASE_URL', 'https://api.collegefootballdata.com')
        self.CFBD_RATE_LIMIT_DELAY = float(os.getenv('CFBD_RATE_LIMIT_DELAY', '0.5'))
        self.CFBD_TIMEOUT = int(os.getenv('CFBD_TIMEOUT', '30'))
        self.CFBD_CACHE_TTL = int(os.getenv('CFBD_CACHE_TTL', '3600'))

        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

        # Cache configuration
        self.CFBD_CACHE_DIR = os.getenv('CFBD_CACHE_DIR')
        self.CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.CACHE_TYPE = os.getenv('CACHE_TYPE', 'local')

        # Performance settings
        self.MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
        self.RETRY_DELAY = float(os.getenv('RETRY_DELAY', '1.0'))

    def setup_logging(self):
        """Setup production logging"""

        log_level = getattr(logging, self.LOG_LEVEL.upper())

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/logs/production.log'),
                logging.StreamHandler()
            ]
        )

    def get_cfbd_config(self) -> Dict[str, Any]:
        """Get CFBD API configuration"""

        return {
            'api_key': self.CFBD_API_KEY,
            'base_url': self.CFBD_BASE_URL,
            'rate_limit_delay': self.CFBD_RATE_LIMIT_DELAY,
            'timeout': self.CFBD_TIMEOUT,
            'cache_ttl': self.CFBD_CACHE_TTL,
            'max_concurrent_requests': self.MAX_CONCURRENT_REQUESTS,
            'retry_attempts': self.RETRY_ATTEMPTS,
            'retry_delay': self.RETRY_DELAY
        }

    def validate_configuration(self) -> bool:
        """Validate production configuration"""

        validations = [
            self._validate_api_key(),
            self._validate_cache_directory(),
            self._validate_network_connectivity(),
            self._validate_performance_settings()
        ]

        return all(validations)

    def _validate_api_key(self) -> bool:
        """Validate CFBD API key format"""
        return len(self.CFBD_API_KEY) >= 20

    def _validate_cache_directory(self) -> bool:
        """Validate cache directory exists and is writable"""
        return os.path.exists(self.CFBD_CACHE_DIR) and os.access(self.CFBD_CACHE_DIR, os.W_OK)

    def _validate_network_connectivity(self) -> bool:
        """Test network connectivity to CFBD API"""
        import requests
        try:
            response = requests.get(f"{self.CFBD_BASE_URL}/games", timeout=5)
            return response.status_code in [200, 401]  # 401 is ok, means server is reachable
        except:
            return False

    def _validate_performance_settings(self) -> bool:
        """Validate performance settings are reasonable"""
        return (
            1 <= self.MAX_CONCURRENT_REQUESTS <= 20 and
            5 <= self.REQUEST_TIMEOUT <= 300 and
            0.1 <= self.CFBD_RATE_LIMIT_DELAY <= 5.0
        )
```

---

## 🏭 Production Setup

### Docker Configuration
```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/cache/cfbd /app/data/mock /app/reports

# Set environment
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose ports
EXPOSE 8080 8081

# Run application
CMD ["python", "scripts/production_server.py"]
```

### Docker Compose
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  script-ohio-2.0:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "8080:8080"  # Main application
      - "8081:8081"  # Health check
    environment:
      - ENVIRONMENT=production
      - CFBD_API_KEY=${CFBD_API_KEY}
      - CFBD_CACHE_DIR=/app/cache/cfbd
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
      - ./data:/app/data
      - ./reports:/app/reports
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - script-ohio-2.0
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    driver: bridge
```

### Nginx Configuration
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream script_ohio_backend {
        server script-ohio-2.0:8080;
        keepalive 32;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=health:10m rate=30r/s;

    server {
        listen 80;
        server_name api.scripthio2.0.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.scripthio2.0.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://script_ohio_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check endpoint
        location /health {
            limit_req zone=health burst=5 nodelay;
            proxy_pass http://script_ohio_backend:8081;
            access_log off;
        }

        # Metrics endpoint
        location /metrics {
            proxy_pass http://script_ohio_backend:8080;
            allow 127.0.0.1;
            allow 10.0.0.0/8;
            deny all;
        }
    }
}
```

---

## 🔒 Security & API Management

### API Key Management
```python
# security/api_key_manager.py
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

class APIKeyManager:
    """Production API key management with rotation"""

    def __init__(self, config):
        self.config = config
        self.key_rotation_enabled = config.get('API_KEY_ROTATION_ENABLED', False)
        self.key_expiry_days = config.get('API_KEY_EXPIRY_DAYS', 90)
        self.key_storage_path = config.get('API_KEY_STORAGE_PATH', '/app/secrets/api_keys.json')

    def load_api_keys(self) -> Dict[str, Any]:
        """Load API keys from secure storage"""

        try:
            with open(self.key_storage_path, 'r') as f:
                key_data = json.load(f)
                return key_data
        except FileNotFoundError:
            return self._initialize_key_storage()

    def get_current_api_key(self) -> str:
        """Get current valid API key"""

        key_data = self.load_api_keys()
        current_key_id = key_data.get('current_key_id')

        if not current_key_id:
            raise ValueError("No current API key configured")

        key_info = key_data['keys'][current_key_id]

        # Check if key is expired
        if self._is_key_expired(key_info):
            if self.key_rotation_enabled:
                return self._rotate_to_next_key(key_data)
            else:
                raise ValueError("Current API key is expired and rotation is disabled")

        return key_info['key']

    def _is_key_expired(self, key_info: Dict[str, Any]) -> bool:
        """Check if API key has expired"""
        expiry_date = datetime.fromisoformat(key_info['expiry_date'])
        return datetime.now() > expiry_date

    def _rotate_to_next_key(self, key_data: Dict[str, Any]) -> str:
        """Rotate to next available API key"""

        current_key_id = key_data.get('current_key_id')
        available_keys = [k for k in key_data['keys'].keys() if k != current_key_id]

        if not available_keys:
            raise ValueError("No backup API keys available for rotation")

        # Select next key (simple round-robin)
        next_key_id = available_keys[0]
        key_data['current_key_id'] = next_key_id

        # Save updated configuration
        with open(self.key_storage_path, 'w') as f:
            json.dump(key_data, f, indent=2)

        return key_data['keys'][next_key_id]['key']

    def _initialize_key_storage(self) -> Dict[str, Any]:
        """Initialize API key storage with primary key from environment"""

        api_key = os.getenv('CFBD_API_KEY')
        if not api_key:
            raise ValueError("CFBD_API_KEY environment variable not set")

        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        expiry_date = (datetime.now() + timedelta(days=self.key_expiry_days)).isoformat()

        key_data = {
            'current_key_id': key_id,
            'keys': {
                key_id: {
                    'key': api_key,
                    'created_date': datetime.now().isoformat(),
                    'expiry_date': expiry_date,
                    'status': 'active'
                }
            }
        }

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.key_storage_path), exist_ok=True)

        # Save initial key storage
        with open(self.key_storage_path, 'w') as f:
            json.dump(key_data, f, indent=2)

        return key_data

    def validate_key_permissions(self, api_key: str) -> bool:
        """Validate API key permissions and scope"""

        # Test basic permissions with a simple request
        import requests

        try:
            response = requests.get(
                f"{self.config['CFBD_BASE_URL']}/games",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"year": 2025, "week": 12},
                timeout=10
            )

            return response.status_code == 200

        except:
            return False
```

### Rate Limiting & Throttling
```python
# security/rate_limiter.py
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List

class ProductionRateLimiter:
    """Production-grade rate limiting with burst handling"""

    def __init__(self, config):
        self.burst_limit = config.get('RATE_LIMIT_BURST', 10)
        self.sustained_limit = config.get('RATE_LIMIT_SUSTAINED', 200)
        self.window_size = 60  # 1 minute window

        # Rate limiting storage
        self.request_counts = defaultdict(lambda: deque())
        self.lock = threading.Lock()

        # Metrics
        self.total_requests = 0
        self.rejected_requests = 0
        self.last_reset = datetime.now()

    def is_request_allowed(self, client_id: str = "default") -> bool:
        """Check if request is allowed for client"""

        with self.lock:
            now = datetime.now()
            client_requests = self.request_counts[client_id]

            # Clean old requests outside window
            cutoff_time = now - timedelta(seconds=self.window_size)
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()

            # Check sustained limit
            if len(client_requests) >= self.sustained_limit:
                self.rejected_requests += 1
                return False

            # Check burst limit (requests in last 10 seconds)
            ten_seconds_ago = now - timedelta(seconds=10)
            recent_requests = sum(1 for req_time in client_requests if req_time > ten_seconds_ago)

            if recent_requests >= self.burst_limit:
                self.rejected_requests += 1
                return False

            # Allow request
            client_requests.append(now)
            self.total_requests += 1
            return True

    def wait_if_needed(self, client_id: str = "default") -> float:
        """Calculate wait time if request would exceed limits"""

        with self.lock:
            now = datetime.now()
            client_requests = self.request_counts[client_id]

            # Clean old requests
            cutoff_time = now - timedelta(seconds=self.window_size)
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()

            # If at sustained limit, calculate wait time
            if len(client_requests) >= self.sustained_limit:
                oldest_request = client_requests[0]
                wait_time = (oldest_request + timedelta(seconds=self.window_size) - now).total_seconds()
                return max(0, wait_time)

            return 0

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""

        with self.lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_size)

            # Calculate active clients
            active_clients = len([
                client for client, requests in self.request_counts.items()
                if requests and requests[-1] > window_start
            ])

            return {
                'total_requests': self.total_requests,
                'rejected_requests': self.rejected_requests,
                'rejection_rate': self.rejected_requests / max(1, self.total_requests),
                'active_clients': active_clients,
                'window_requests': sum(len(requests) for requests in self.request_counts.values()),
                'last_reset': self.last_reset.isoformat()
            }
```

---

## 📊 Monitoring & Alerting

### Health Check System
```python
# monitoring/health_check.py
import os
import psutil
import requests
import json
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self, config):
        self.config = config
        self.start_time = datetime.now()

    def check_cfbd_api_health(self) -> Dict[str, Any]:
        """Check CFBD API connectivity and authentication"""

        try:
            response = requests.get(
                f"{self.config['CFBD_BASE_URL']}/games",
                headers={"Authorization": f"Bearer {self.config['CFBD_API_KEY']}"},
                params={"year": 2025, "week": 12},
                timeout=10
            )

            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def check_system_health(self) -> Dict[str, Any]:
        """Check system resource health"""

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 else 'degraded',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'timestamp': datetime.now().isoformat()
        }

    def check_cache_health(self) -> Dict[str, Any]:
        """Check cache system health"""

        cache_dir = self.config.get('CFBD_CACHE_DIR', '/app/cache/cfbd')

        try:
            # Check if cache directory exists and is writable
            if not os.path.exists(cache_dir):
                return {'status': 'unhealthy', 'error': 'Cache directory does not exist'}

            if not os.access(cache_dir, os.W_OK):
                return {'status': 'unhealthy', 'error': 'Cache directory not writable'}

            # Count cache files
            cache_files = len([f for f in os.listdir(cache_dir) if f.endswith('.json')])
            cache_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in os.listdir(cache_dir))

            return {
                'status': 'healthy',
                'cache_files': cache_files,
                'cache_size_bytes': cache_size,
                'cache_size_mb': round(cache_size / (1024 * 1024), 2),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def check_model_health(self) -> Dict[str, Any]:
        """Check ML model availability"""

        model_files = [
            'model_pack/ridge_model_2025.joblib',
            'model_pack/xgb_home_win_model_2025.pkl',
            'model_pack/fastai_home_win_model_2025.pkl'
        ]

        available_models = []
        missing_models = []

        for model_file in model_files:
            if os.path.exists(model_file):
                available_models.append(model_file)
            else:
                missing_models.append(model_file)

        status = 'healthy' if len(available_models) >= 2 else 'degraded'

        return {
            'status': status,
            'available_models': available_models,
            'missing_models': missing_models,
            'total_models': len(model_files),
            'available_count': len(available_models),
            'timestamp': datetime.now().isoformat()
        }

    def get_uptime(self) -> Dict[str, Any]:
        """Get system uptime information"""

        uptime = datetime.now() - self.start_time

        return {
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_hours': round(uptime.total_seconds() / 3600, 2),
            'timestamp': datetime.now().isoformat()
        }

# Health check endpoints
@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""

    health_checker = HealthChecker(app.config)

    # Run all health checks
    checks = {
        'api': health_checker.check_cfbd_api_health(),
        'system': health_checker.check_system_health(),
        'cache': health_checker.check_cache_health(),
        'models': health_checker.check_model_health(),
        'uptime': health_checker.get_uptime()
    }

    # Determine overall status
    statuses = [check['status'] for check in checks.values()]
    if all(status == 'healthy' for status in statuses):
        overall_status = 'healthy'
        http_status = 200
    elif any(status == 'unhealthy' for status in statuses):
        overall_status = 'unhealthy'
        http_status = 503
    else:
        overall_status = 'degraded'
        http_status = 200

    response = {
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'checks': checks
    }

    return jsonify(response), http_status

@app.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint"""

    # Implementation for metrics collection
    return jsonify({
        'metrics': 'Metrics implementation here',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
```

### Monitoring Dashboard
```python
# monitoring/dashboard.py
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    timestamp: datetime
    api_response_time: float
    api_requests_per_minute: int
    cache_hit_rate: float
    cpu_usage: float
    memory_usage: float
    prediction_accuracy: float
    error_rate: float

class MonitoringDashboard:
    """Production monitoring dashboard"""

    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[Dict] = []

    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""

        # Implementation for collecting metrics from various sources
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            api_response_time=0.0,  # Collect from API
            api_requests_per_minute=0,  # Calculate from logs
            cache_hit_rate=0.0,  # Get from cache system
            cpu_usage=0.0,  # Get from psutil
            memory_usage=0.0,  # Get from psutil
            prediction_accuracy=0.0,  # Calculate from recent predictions
            error_rate=0.0  # Calculate from error logs
        )

        self.metrics_history.append(metrics)

        # Keep only last 24 hours of metrics
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        return metrics

    def check_alerts(self, metrics: SystemMetrics) -> List[Dict]:
        """Check for alert conditions"""

        new_alerts = []

        # API response time alert
        if metrics.api_response_time > 5.0:
            new_alerts.append({
                'type': 'api_slow',
                'severity': 'warning',
                'message': f"API response time: {metrics.api_response_time:.2f}s",
                'timestamp': datetime.now().isoformat()
            })

        # High CPU usage alert
        if metrics.cpu_usage > 80:
            new_alerts.append({
                'type': 'high_cpu',
                'severity': 'critical',
                'message': f"CPU usage: {metrics.cpu_usage:.1f}%",
                'timestamp': datetime.now().isoformat()
            })

        # Low prediction accuracy alert
        if metrics.prediction_accuracy < 0.4:
            new_alerts.append({
                'type': 'low_accuracy',
                'severity': 'warning',
                'message': f"Prediction accuracy: {metrics.prediction_accuracy:.1%}",
                'timestamp': datetime.now().isoformat()
            })

        # High error rate alert
        if metrics.error_rate > 0.05:
            new_alerts.append({
                'type': 'high_error_rate',
                'severity': 'critical',
                'message': f"Error rate: {metrics.error_rate:.1%}",
                'timestamp': datetime.now().isoformat()
            })

        self.alerts.extend(new_alerts)

        # Keep only last 100 alerts
        self.alerts = self.alerts[-100:]

        return new_alerts

    def get_dashboard_data(self) -> Dict:
        """Get complete dashboard data"""

        if not self.metrics_history:
            return {'status': 'no_data'}

        current_metrics = self.metrics_history[-1]

        return {
            'status': 'active',
            'current_metrics': {
                'api_response_time': current_metrics.api_response_time,
                'api_requests_per_minute': current_metrics.api_requests_per_minute,
                'cache_hit_rate': current_metrics.cache_hit_rate,
                'cpu_usage': current_metrics.cpu_usage,
                'memory_usage': current_metrics.memory_usage,
                'prediction_accuracy': current_metrics.prediction_accuracy,
                'error_rate': current_metrics.error_rate
            },
            'recent_alerts': self.alerts[-10:],
            'metrics_trend': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'api_response_time': m.api_response_time,
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage
                }
                for m in self.metrics_history[-60:]  # Last hour
            ]
        }
```

---

## ⚡ Scaling & Performance

### Horizontal Scaling
```python
# scaling/load_balancer.py
import random
import threading
from typing import List, Dict, Any
from datetime import datetime

class LoadBalancer:
    """Load balancer for CFBD API requests"""

    def __init__(self, config):
        self.config = config
        self.instances = []
        self.current_instance = 0
        self.lock = threading.Lock()

    def register_instance(self, instance_id: str, endpoint: str, weight: int = 1):
        """Register a new instance for load balancing"""

        instance = {
            'id': instance_id,
            'endpoint': endpoint,
            'weight': weight,
            'requests_served': 0,
            'last_health_check': None,
            'status': 'unknown'
        }

        with self.lock:
            self.instances.append(instance)

    def get_next_instance(self) -> Dict[str, Any]:
        """Get next instance using weighted round-robin"""

        with self.lock:
            # Filter healthy instances
            healthy_instances = [inst for inst in self.instances if inst['status'] == 'healthy']

            if not healthy_instances:
                raise Exception("No healthy instances available")

            # Weighted selection
            total_weight = sum(inst['weight'] for inst in healthy_instances)
            random_weight = random.uniform(0, total_weight)

            current_weight = 0
            for instance in healthy_instances:
                current_weight += instance['weight']
                if random_weight <= current_weight:
                    instance['requests_served'] += 1
                    return instance

            # Fallback to first instance
            healthy_instances[0]['requests_served'] += 1
            return healthy_instances[0]

    def health_check_all_instances(self):
        """Perform health check on all instances"""

        for instance in self.instances:
            try:
                # Health check implementation
                response = requests.get(f"{instance['endpoint']}/health", timeout=5)
                instance['status'] = 'healthy' if response.status_code == 200 else 'unhealthy'
                instance['last_health_check'] = datetime.now()

            except Exception:
                instance['status'] = 'unhealthy'
                instance['last_health_check'] = datetime.now()

    def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Get load balancing metrics"""

        with self.lock:
            total_requests = sum(inst['requests_served'] for inst in self.instances)
            healthy_count = sum(1 for inst in self.instances if inst['status'] == 'healthy')

            return {
                'total_instances': len(self.instances),
                'healthy_instances': healthy_count,
                'total_requests': total_requests,
                'instances': [
                    {
                        'id': inst['id'],
                        'endpoint': inst['endpoint'],
                        'requests_served': inst['requests_served'],
                        'status': inst['status'],
                        'last_health_check': inst['last_health_check'].isoformat() if inst['last_health_check'] else None
                    }
                    for inst in self.instances
                ]
            }
```

### Performance Optimization
```python
# performance/optimizer.py
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional

class PerformanceOptimizer:
    """Performance optimization for CFBD API requests"""

    def __init__(self, config):
        self.config = config
        self.session = None
        self.semaphore = None

    async def initialize(self):
        """Initialize async session and semaphore"""

        connector = aiohttp.TCPConnector(
            limit=self.config.get('MAX_CONCURRENT_REQUESTS', 10),
            limit_per_host=self.config.get('MAX_CONCURRENT_REQUESTS_PER_HOST', 5)
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.get('REQUEST_TIMEOUT', 30),
            connect=10
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

        self.semaphore = asyncio.Semaphore(self.config.get('MAX_CONCURRENT_REQUESTS', 10))

    async def make_parallel_requests(self, requests_data: List[Dict]) -> List[Dict]:
        """Make parallel CFBD API requests"""

        if not self.session:
            await self.initialize()

        async def fetch_single_request(request_data):
            async with self.semaphore:
                try:
                    url = request_data['url']
                    headers = request_data.get('headers', {})
                    params = request_data.get('params', {})

                    async with self.session.get(url, headers=headers, params=params) as response:
                        data = await response.json()
                        return {
                            'success': response.status == 200,
                            'status_code': response.status,
                            'data': data,
                            'request_data': request_data
                        }

                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'request_data': request_data
                    }

        # Execute all requests concurrently
        tasks = [fetch_single_request(req_data) for req_data in requests_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [result for result in results if not isinstance(result, Exception)]

    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()

# Usage example for batch game data retrieval
async def batch_get_week_data(year: int, weeks: List[int]) -> Dict[int, List[Dict]]:
    """Get data for multiple weeks in parallel"""

    optimizer = PerformanceOptimizer({
        'MAX_CONCURRENT_REQUESTS': 5,
        'REQUEST_TIMEOUT': 30
    })

    try:
        await optimizer.initialize()

        # Prepare requests for all weeks
        requests_data = []
        for week in weeks:
            requests_data.append({
                'url': f"https://api.collegefootballdata.com/games",
                'params': {'year': year, 'week': week},
                'week': week
            })

        # Make parallel requests
        results = await optimizer.make_parallel_requests(requests_data)

        # Organize results by week
        week_data = {}
        for result in results:
            if result['success']:
                week = result['request_data']['week']
                week_data[week] = result['data']

        return week_data

    finally:
        await optimizer.close()
```

---

## 🆘 Disaster Recovery

### Backup & Recovery
```python
# disaster_recovery/backup_system.py
import os
import json
import shutil
import gzip
import boto3
from datetime import datetime, timedelta
from pathlib import Path

class BackupSystem:
    """Automated backup and recovery system"""

    def __init__(self, config):
        self.config = config
        self.backup_dir = Path(config.get('BACKUP_DIR', '/app/backups'))
        self.backup_retention_days = config.get('BACKUP_RETENTION_DAYS', 30)
        self.s3_bucket = config.get('S3_BACKUP_BUCKET')

    def create_data_backup(self) -> Dict[str, Any]:
        """Create comprehensive data backup"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{timestamp}"

        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup cache data
            cache_backup_path = backup_path / "cache"
            if os.path.exists('/app/cache'):
                shutil.copytree('/app/cache', cache_backup_path)

            # Backup model files
            models_backup_path = backup_path / "models"
            if os.path.exists('/app/model_pack'):
                shutil.copytree('/app/model_pack', models_backup_path)

            # Backup configuration
            config_backup_path = backup_path / "config"
            config_backup_path.mkdir(exist_ok=True)
            shutil.copy('/app/.env', config_backup_path / '.env')

            # Create backup metadata
            backup_metadata = {
                'timestamp': timestamp,
                'backup_type': 'full',
                'components': ['cache', 'models', 'config'],
                'created_at': datetime.now().isoformat(),
                'system_info': self._get_system_info()
            }

            with open(backup_path / 'metadata.json', 'w') as f:
                json.dump(backup_metadata, f, indent=2)

            # Compress backup
            compressed_path = backup_path.with_suffix('.tar.gz')
            self._compress_backup(backup_path, compressed_path)

            # Remove uncompressed backup
            shutil.rmtree(backup_path)

            # Upload to S3 if configured
            if self.s3_bucket:
                self._upload_to_s3(compressed_path, f"backups/backup_{timestamp}.tar.gz")

            return {
                'success': True,
                'backup_path': str(compressed_path),
                'backup_size': os.path.getsize(compressed_path),
                'timestamp': timestamp
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': timestamp
            }

    def restore_from_backup(self, backup_path: str) -> Dict[str, Any]:
        """Restore system from backup"""

        try:
            # Extract backup
            extract_path = Path('/tmp/restore_temp')
            extract_path.mkdir(exist_ok=True)

            self._extract_backup(backup_path, extract_path)

            # Verify backup integrity
            metadata_path = extract_path / 'backup_*/metadata.json'
            if not metadata_path.exists():
                raise Exception("Invalid backup: metadata.json not found")

            with open(metadata_path) as f:
                metadata = json.load(f)

            # Restore components
            restore_path = extract_path / list(extract_path.glob('backup_*'))[0].name

            if 'cache' in metadata['components']:
                if os.path.exists(f"{restore_path}/cache"):
                    shutil.rmtree('/app/cache', ignore_errors=True)
                    shutil.copytree(f"{restore_path}/cache", '/app/cache')

            if 'models' in metadata['components']:
                if os.path.exists(f"{restore_path}/models"):
                    shutil.rmtree('/app/model_pack', ignore_errors=True)
                    shutil.copytree(f"{restore_path}/models", '/app/model_pack')

            if 'config' in metadata['components']:
                if os.path.exists(f"{restore_path}/config/.env"):
                    shutil.copy(f"{restore_path}/config/.env", '/app/.env')

            # Cleanup
            shutil.rmtree(extract_path)

            return {
                'success': True,
                'restored_components': metadata['components'],
                'backup_timestamp': metadata['timestamp']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_old_backups(self):
        """Clean up old backups beyond retention period"""

        cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)

        for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)

            if file_date < cutoff_date:
                backup_file.unlink()
                print(f"Deleted old backup: {backup_file}")

    def _compress_backup(self, source_path: Path, target_path: Path):
        """Compress backup directory"""

        shutil.make_archive(str(target_path.with_suffix('')), 'gztar', str(source_path.parent), source_path.name)

    def _extract_backup(self, backup_path: str, extract_path: Path):
        """Extract compressed backup"""

        shutil.unpack_archive(backup_path, extract_path)

    def _upload_to_s3(self, file_path: Path, s3_key: str):
        """Upload backup to S3"""

        s3 = boto3.client('s3')
        s3.upload_file(str(file_path), self.s3_bucket, s3_key)

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for backup metadata"""

        import platform
        import psutil

        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2)
        }
```

### Failover System
```python
# disaster_recovery/failover.py
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

class FailoverSystem:
    """Automatic failover system for high availability"""

    def __init__(self, config):
        self.config = config
        self.primary_status = 'unknown'
        self.failover_active = False
        self.last_health_check = None
        self.health_check_interval = config.get('HEALTH_CHECK_INTERVAL', 30)

    async def start_monitoring(self):
        """Start continuous health monitoring"""

        while True:
            await self._perform_health_check()
            await asyncio.sleep(self.health_check_interval)

    async def _perform_health_check(self):
        """Perform health check and trigger failover if needed"""

        health_status = await self._check_primary_system_health()
        self.last_health_check = datetime.now()

        if health_status['status'] == 'healthy':
            if self.failover_active:
                await self._restore_primary_system()
            self.primary_status = 'healthy'

        elif health_status['status'] == 'unhealthy':
            if not self.failover_active:
                await self._activate_failover()
            self.primary_status = 'unhealthy'

        elif health_status['status'] == 'degraded':
            # Log warning but don't trigger failover for degraded status
            self.primary_status = 'degraded'

    async def _check_primary_system_health(self) -> Dict[str, Any]:
        """Check primary system health"""

        try:
            # Check CFBD API
            api_check = await self._check_cfbd_api()

            # Check local models
            model_check = self._check_local_models()

            # Check cache system
            cache_check = self._check_cache_system()

            # Determine overall status
            if all(check['status'] == 'healthy' for check in [api_check, model_check, cache_check]):
                return {'status': 'healthy', 'checks': [api_check, model_check, cache_check]}
            elif any(check['status'] == 'unhealthy' for check in [api_check, model_check, cache_check]):
                return {'status': 'unhealthy', 'checks': [api_check, model_check, cache_check]}
            else:
                return {'status': 'degraded', 'checks': [api_check, model_check, cache_check]}

        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

    async def _activate_failover(self):
        """Activate failover to backup systems"""

        print(f"🚨 Activating failover system at {datetime.now()}")

        # Switch to mock data
        self.failover_active = True

        # Log failover activation
        with open('/app/logs/failover.log', 'a') as f:
            f.write(f"Failover activated: {datetime.now()}\n")

        # Send alert (implementation depends on alerting system)
        await self._send_alert('FAILOVER_ACTIVATED', 'Primary system unhealthy, failover activated')

    async def _restore_primary_system(self):
        """Restore primary system when healthy again"""

        print(f"✅ Restoring primary system at {datetime.now()}")

        self.failover_active = False

        # Log restoration
        with open('/app/logs/failover.log', 'a') as f:
            f.write(f"Primary system restored: {datetime.now()}\n")

        # Send alert
        await self._send_alert('PRIMARY_RESTORED', 'Primary system restored from failover')

    async def _send_alert(self, alert_type: str, message: str):
        """Send alert notification"""
        # Implementation depends on alerting system (email, Slack, etc.)
        pass

    def get_failover_status(self) -> Dict[str, Any]:
        """Get current failover system status"""

        return {
            'primary_status': self.primary_status,
            'failover_active': self.failover_active,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'health_check_interval': self.health_check_interval
        }
```

---

## 🔧 Maintenance & Updates

### Automated Maintenance Tasks
```python
# maintenance/maintenance_scheduler.py
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class MaintenanceScheduler:
    """Automated maintenance task scheduler"""

    def __init__(self, config):
        self.config = config
        self.maintenance_log = []

    def start_scheduler(self):
        """Start the maintenance scheduler"""

        # Daily tasks
        schedule.every().day.at("02:00").do(self.daily_cleanup)
        schedule.every().day.at("03:00").do(self.daily_backup)

        # Weekly tasks
        schedule.every().sunday.at("04:00").do(self.weekly_maintenance)

        # Hourly tasks
        schedule.every().hour.do(self.hourly_health_check)

        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)

    def daily_cleanup(self):
        """Perform daily cleanup tasks"""

        start_time = datetime.now()
        log_entry = {
            'task': 'daily_cleanup',
            'start_time': start_time.isoformat(),
            'status': 'running'
        }

        try:
            # Clean old logs
            self._cleanup_old_logs()

            # Clean old cache files
            self._cleanup_old_cache()

            # Update metrics
            self._update_metrics()

            log_entry.update({
                'status': 'completed',
                'end_time': datetime.now().isoformat(),
                'duration_minutes': (datetime.now() - start_time).total_seconds() / 60
            })

        except Exception as e:
            log_entry.update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })

        self.maintenance_log.append(log_entry)

    def daily_backup(self):
        """Perform daily backup"""

        from disaster_recovery.backup_system import BackupSystem

        backup_system = BackupSystem(self.config)
        result = backup_system.create_data_backup()

        log_entry = {
            'task': 'daily_backup',
            'start_time': datetime.now().isoformat(),
            'result': result
        }

        self.maintenance_log.append(log_entry)

    def weekly_maintenance(self):
        """Perform weekly maintenance tasks"""

        start_time = datetime.now()

        try:
            # Model retraining if needed
            self._check_model_retraining()

            # System performance analysis
            self._analyze_performance()

            # Security audit
            self._security_audit()

            print(f"✅ Weekly maintenance completed in {(datetime.now() - start_time).total_seconds():.1f}s")

        except Exception as e:
            print(f"❌ Weekly maintenance failed: {e}")

    def hourly_health_check(self):
        """Perform hourly health check"""

        # Quick health check
        health_status = self._quick_health_check()

        if health_status['status'] != 'healthy':
            print(f"⚠️ System health check: {health_status['status']}")

    def _cleanup_old_logs(self):
        """Clean log files older than retention period"""

        import os
        from pathlib import Path

        log_dir = Path('/app/logs')
        retention_days = self.config.get('LOG_RETENTION_DAYS', 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        for log_file in log_dir.glob("*.log"):
            file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_date < cutoff_date:
                log_file.unlink()
                print(f"Deleted old log: {log_file}")

    def _cleanup_old_cache(self):
        """Clean cache files older than retention period"""

        import os
        from pathlib import Path

        cache_dir = Path('/app/cache/cfbd')
        retention_hours = self.config.get('CACHE_RETENTION_HOURS', 24)
        cutoff_time = datetime.now() - timedelta(hours=retention_hours)

        for cache_file in cache_dir.glob("*.json"):
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_time < cutoff_time:
                cache_file.unlink()
                print(f"Deleted old cache: {cache_file}")

    def get_maintenance_status(self) -> Dict[str, Any]:
        """Get maintenance system status"""

        return {
            'scheduler_running': True,
            'total_maintenance_tasks': len(self.maintenance_log),
            'recent_tasks': self.maintenance_log[-10:],
            'last_cleanup': self._get_last_task_time('daily_cleanup'),
            'last_backup': self._get_last_task_time('daily_backup')
        }
```

---

## 📈 Deployment Checklist

### Pre-Deployment Checklist
```markdown
## Environment Setup
- [ ] Environment variables configured (.env.production)
- [ ] API keys obtained and tested
- [ ] Database connections verified
- [ ] Cache directories created with proper permissions
- [ ] SSL certificates installed
- [ ] Load balancer configured
- [ ] Monitoring endpoints accessible

## Application Validation
- [ ] All CFBD integration tests passing
- [ ] Model files present and validated
- [ ] Feature transformation pipeline working
- [ ] Rate limiting functional
- [ ] Error handling verified
- [ ] Logging system operational

## Security & Compliance
- [ ] API key rotation configured
- [ ] Rate limiting rules applied
- [ ] SSL certificates valid
- [ ] Security headers configured
- [ ] Access controls implemented
- [ ] Data encryption verified

## Performance & Scaling
- [ ] Load testing completed
- [ ] Caching strategy implemented
- [ ] Database queries optimized
- [ ] Resource limits configured
- [ ] Auto-scaling rules set
- [ ] Performance benchmarks met

## Monitoring & Alerting
- [ ] Health check endpoints responding
- [ ] Metrics collection configured
- [ ] Alert rules set up
- [ ] Notification channels tested
- [ ] Dashboard functional
- [ ] Log aggregation working

## Backup & Recovery
- [ ] Backup procedures tested
- [ ] Recovery procedures verified
- [ ] Disaster recovery plan documented
- [ ] Backup retention policies set
- [ ] Offsite backups configured
- [ ] Recovery time objectives met
```

### Post-Deployment Checklist
```markdown
## System Verification
- [ ] Application responding on all endpoints
- [ ] CFBD API integration functional
- [ ] Models loading and predicting correctly
- [ ] Cache system operational
- [ ] Rate limiting active
- [ ] Error monitoring working

## Performance Validation
- [ ] Response times within acceptable limits
- [ ] Resource utilization normal
- [ ] No memory leaks detected
- [ ] Database performance optimal
- [ ] Cache hit rates acceptable
- [ ] Error rates within threshold

## Security Verification
- [ ] All endpoints properly secured
- [ ] API authentication working
- [ ] Rate limiting enforced
- [ ] SSL/TLS encryption active
- [ ] Security headers present
- [ ] No security vulnerabilities detected

## Business Logic Verification
- [ ] Week 12 data retrieval working
- [ ] Feature generation accurate
- [ ] Predictions generating correctly
- [ ] Model performance as expected
- [ ] Data quality checks passing
- [ ] Reports generating properly
```

---

*This deployment guide provides comprehensive instructions for deploying the CFBD API integration in a production environment with proper security, monitoring, scaling, and disaster recovery capabilities.*