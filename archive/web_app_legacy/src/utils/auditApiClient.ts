import { AuditSummary, AlertData, MetricData, CategoryPerformance } from '../types/audit';

// Types for audit data
export interface AuditSummary {
  audit_id: string;
  audit_name: string;
  overall_status: 'passed' | 'failed' | 'warning';
  overall_score: number;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  warning_checks: number;
  critical_failures: number;
  execution_time: number;
  timestamp: string;
}

export interface AlertData {
  alert_id: string;
  rule_id: string;
  severity: 'critical' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface MetricData {
  timestamp: string;
  score: number;
  execution_time: number;
  total_checks: number;
}

export interface CategoryPerformance {
  category: string;
  score: number;
  checks: number;
  passed: number;
  failed: number;
}

// API Client for audit data
class AuditApiClient {
  private baseUrl: string;
  private timeout: number = 10000; // 10 seconds

  constructor(baseUrl: string = 'http://localhost:5001/api') {
    this.baseUrl = baseUrl;
  }

  private async fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${url}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  private async handleApiResponse<T>(response: Response, fallbackData?: T): Promise<T> {
    if (!response.ok) {
      console.warn(`API request failed: ${response.status} ${response.statusText}`);
      if (fallbackData) {
        return fallbackData;
      }
      throw new Error(`API request failed: ${response.status}`);
    }

    try {
      const data = await response.json();
      return data;
    } catch (error) {
      console.warn('Failed to parse API response:', error);
      if (fallbackData) {
        return fallbackData;
      }
      throw new Error('Failed to parse API response');
    }
  }

  // Check if audit API is available
  async checkAuditApiHealth(): Promise<boolean> {
    try {
      const response = await this.fetchWithTimeout('/api/audit/health', {
        method: 'GET',
      });
      return response.ok;
    } catch (error) {
      console.log('Audit API not available, using fallback data');
      return false;
    }
  }

  // Get audit summary
  async getAuditSummary(timeRange: '24h' | '7d' | '30d' = '7d'): Promise<AuditSummary[]> {
    try {
      const response = await this.fetchWithTimeout(`/api/audit/summary?timeRange=${timeRange}`);
      return this.handleApiResponse(response, this.generateMockAuditSummary());
    } catch (error) {
      console.warn('Failed to fetch audit summary, using fallback data');
      return this.generateMockAuditSummary();
    }
  }

  // Get recent alerts
  async getRecentAlerts(timeRange: '24h' | '7d' | '30d' = '7d'): Promise<AlertData[]> {
    try {
      const response = await this.fetchWithTimeout(`/api/audit/alerts?timeRange=${timeRange}`);
      return this.handleApiResponse(response, this.generateMockAlerts());
    } catch (error) {
      console.warn('Failed to fetch alerts, using fallback data');
      return this.generateMockAlerts();
    }
  }

  // Get performance metrics
  async getPerformanceMetrics(timeRange: '24h' | '7d' | '30d' = '7d'): Promise<MetricData[]> {
    try {
      const response = await this.fetchWithTimeout(`/api/audit/metrics?timeRange=${timeRange}`);
      return this.handleApiResponse(response, this.generateMockMetrics());
    } catch (error) {
      console.warn('Failed to fetch metrics, using fallback data');
      return this.generateMockMetrics();
    }
  }

  // Get category performance
  async getCategoryPerformance(): Promise<CategoryPerformance[]> {
    try {
      const response = await this.fetchWithTimeout('/api/audit/categories');
      return this.handleApiResponse(response, this.generateMockCategoryPerformance());
    } catch (error) {
      console.warn('Failed to fetch category performance, using fallback data');
      return this.generateMockCategoryPerformance();
    }
  }

  // Trigger a new audit
  async triggerAudit(auditType: 'quick' | 'comprehensive' = 'quick'): Promise<{ success: boolean; message: string }> {
    try {
      const response = await this.fetchWithTimeout('/api/audit/trigger', {
        method: 'POST',
        body: JSON.stringify({ auditType }),
      });
      return this.handleApiResponse(response, { success: false, message: 'Audit trigger failed' });
    } catch (error) {
      console.warn('Failed to trigger audit');
      return { success: false, message: 'Audit trigger failed - API unavailable' };
    }
  }

  // Mock data generators for fallback
  private generateMockAuditSummary(): AuditSummary[] {
    const now = new Date();
    const audits: AuditSummary[] = [];

    for (let i = 0; i < 30; i++) {
      const timestamp = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      const score = 85 + Math.random() * 15;
      const status = score > 90 ? 'passed' : score > 75 ? 'warning' : 'failed';

      audits.push({
        audit_id: `audit_${i}`,
        audit_name: `Production Audit ${i}`,
        overall_status: status,
        overall_score: score,
        total_checks: 20 + Math.floor(Math.random() * 10),
        passed_checks: 15 + Math.floor(Math.random() * 10),
        failed_checks: Math.floor(Math.random() * 5),
        warning_checks: Math.floor(Math.random() * 3),
        critical_failures: status === 'failed' ? Math.floor(Math.random() * 2) : 0,
        execution_time: 30 + Math.random() * 120,
        timestamp: timestamp.toISOString()
      });
    }

    return audits;
  }

  private generateMockAlerts(): AlertData[] {
    const now = new Date();
    const alerts: AlertData[] = [];
    const severities: AlertData['severity'][] = ['critical', 'warning', 'error', 'info'];

    for (let i = 0; i < 8; i++) {
      const severity = severities[Math.floor(Math.random() * severities.length)];
      alerts.push({
        alert_id: `alert_${i}`,
        rule_id: `rule_${i}`,
        severity,
        title: `${severity.charAt(0).toUpperCase() + severity.slice(1)} Alert ${i}`,
        message: `This is a ${severity} alert that requires attention.`,
        timestamp: new Date(now.getTime() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        acknowledged: Math.random() > 0.5
      });
    }

    return alerts;
  }

  private generateMockMetrics(): MetricData[] {
    const now = new Date();
    const metrics: MetricData[] = [];

    for (let i = 0; i < 30; i++) {
      const timestamp = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      metrics.push({
        timestamp: timestamp.toISOString(),
        score: 85 + Math.random() * 15,
        execution_time: 30 + Math.random() * 120,
        total_checks: 20 + Math.floor(Math.random() * 10)
      });
    }

    return metrics;
  }

  private generateMockCategoryPerformance(): CategoryPerformance[] {
    return [
      { category: 'System Integrity', score: 92, checks: 8, passed: 7, failed: 1 },
      { category: 'Data Pipeline', score: 88, checks: 6, passed: 5, failed: 1 },
      { category: 'Model Validation', score: 95, checks: 10, passed: 9, failed: 1 },
      { category: 'API Connectivity', score: 97, checks: 4, passed: 4, failed: 0 }
    ];
  }
}

// Create and export singleton instance
export const auditApiClient = new AuditApiClient();

// Export types for use in components
export type {
  AuditSummary,
  AlertData,
  MetricData,
  CategoryPerformance
};