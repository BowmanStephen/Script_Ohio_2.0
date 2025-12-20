// Types for audit dashboard and monitoring system

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

export interface AuditSystemHealth {
  overall_status: 'healthy' | 'degraded' | 'critical';
  last_audit: AuditSummary | null;
  active_alerts: number;
  critical_issues: number;
  uptime_percentage: number;
  next_scheduled_audit: string | null;
}

export interface AlertRule {
  rule_id: string;
  name: string;
  description: string;
  severity: 'critical' | 'warning' | 'error' | 'info';
  enabled: boolean;
  threshold_conditions: Record<string, any>;
  channels: string[];
  last_triggered: string | null;
  trigger_count: number;
}

export interface AuditSchedule {
  schedule_id: string;
  audit_type: 'quick' | 'comprehensive' | 'domain';
  schedule_pattern: string;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
  run_count: number;
  success_count: number;
  failure_count: number;
}

export interface AuditReport {
  audit_id: string;
  report_format: 'json' | 'html' | 'pdf' | 'toon';
  generated_at: string;
  file_path: string;
  file_size: number;
}