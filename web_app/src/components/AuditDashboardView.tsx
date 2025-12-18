import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  Shield,
  Database,
  Brain,
  Calendar,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react';
import { auditApiClient } from '../utils/auditApiClient';
import {
  AuditSummary,
  AlertData,
  MetricData,
  CategoryPerformance
} from '../types/audit';

const COLORS = {
  critical: '#ef4444',
  warning: '#f59e0b',
  passed: '#10b981',
  failed: '#ef4444',
  warning_checks: '#f59e0b',
  info: '#3b82f6',
  primary: '#3b82f6',
  secondary: '#6b7280'
};

export const AuditDashboardView: React.FC = () => {
  const [auditData, setAuditData] = useState<AuditSummary[]>([]);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [categoryPerformance, setCategoryPerformance] = useState<CategoryPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d'>('7d');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // Fetch data from API with fallback to mock data
        const [auditData, metricsData, alertsData, categoryData] = await Promise.all([
          auditApiClient.getAuditSummary(selectedTimeRange),
          auditApiClient.getPerformanceMetrics(selectedTimeRange),
          auditApiClient.getRecentAlerts(selectedTimeRange),
          auditApiClient.getCategoryPerformance()
        ]);

        setAuditData(auditData);
        setMetrics(metricsData);
        setAlerts(alertsData);
        setCategoryPerformance(categoryData);

      } catch (error) {
        console.error('Failed to load audit data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [selectedTimeRange]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const [auditData, metricsData, alertsData, categoryData] = await Promise.all([
        auditApiClient.getAuditSummary(selectedTimeRange),
        auditApiClient.getPerformanceMetrics(selectedTimeRange),
        auditApiClient.getRecentAlerts(selectedTimeRange),
        auditApiClient.getCategoryPerformance()
      ]);

      setAuditData(auditData);
      setMetrics(metricsData);
      setAlerts(alertsData);
      setCategoryPerformance(categoryData);
    } catch (error) {
      console.error('Failed to refresh data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleTriggerAudit = async (auditType: 'quick' | 'comprehensive' = 'quick') => {
    try {
      const result = await auditApiClient.triggerAudit(auditType);
      if (result.success) {
        // Refresh data after successful audit trigger
        handleRefresh();
      }
    } catch (error) {
      console.error('Failed to trigger audit:', error);
    }
  };

  // Calculate summary metrics
  const latestAudit = auditData[0];
  const recentAlerts = alerts.filter(alert => {
    const alertTime = new Date(alert.timestamp);
    const cutoffTime = new Date();
    if (selectedTimeRange === '24h') {
      cutoffTime.setHours(cutoffTime.getHours() - 24);
    } else if (selectedTimeRange === '7d') {
      cutoffTime.setDate(cutoffTime.getDate() - 7);
    } else {
      cutoffTime.setDate(cutoffTime.getDate() - 30);
    }
    return alertTime >= cutoffTime;
  });

  const statusDistribution = useMemo(() => {
    const distribution = {
      passed: 0,
      warning: 0,
      failed: 0,
      info: 0
    };

    recentAlerts.forEach(alert => {
      if (alert.severity === 'critical' || alert.severity === 'error') {
        distribution.failed++;
      } else if (alert.severity === 'warning') {
        distribution.warning++;
      } else {
        distribution.info++;
      }
    });

    return Object.entries(distribution).map(([name, value]) => ({ name, value }));
  }, [recentAlerts]);

  const pieData = [
    { name: 'Passed', value: latestAudit?.passed_checks || 0, color: COLORS.passed },
    { name: 'Failed', value: latestAudit?.failed_checks || 0, color: COLORS.failed },
    { name: 'Warning', value: latestAudit?.warning_checks || 0, color: COLORS.warning_checks }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading audit dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">🔍 Audit Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time monitoring and analytics for system audits
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Tabs value={selectedTimeRange} onValueChange={(value) => setSelectedTimeRange(value as any)}>
            <TabsList>
              <TabsTrigger value="24h">24H</TabsTrigger>
              <TabsTrigger value="7d">7D</TabsTrigger>
              <TabsTrigger value="30d">30D</TabsTrigger>
            </TabsList>
          </Tabs>
          <Button onClick={() => handleTriggerAudit('quick')} variant="outline" size="sm">
            <Activity className="h-4 w-4 mr-2" />
            Quick Audit
          </Button>
          <Button onClick={() => handleTriggerAudit('comprehensive')} variant="outline" size="sm">
            <Shield className="h-4 w-4 mr-2" />
            Full Audit
          </Button>
          <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestAudit?.overall_score.toFixed(1)}%
            </div>
            <Progress value={latestAudit?.overall_score || 0} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {latestAudit?.overall_status === 'passed' ? '✅ System Healthy' :
               latestAudit?.overall_status === 'warning' ? '⚠️ Minor Issues' : '❌ Critical Issues'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Checks</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{latestAudit?.total_checks}</div>
            <p className="text-xs text-muted-foreground">
              {latestAudit?.passed_checks} passed, {latestAudit?.failed_checks} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentAlerts.length}</div>
            <p className="text-xs text-muted-foreground">
              {recentAlerts.filter(a => a.severity === 'critical').length} critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Execution</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {latestAudit?.execution_time.toFixed(1)}s
            </div>
            <p className="text-xs text-muted-foreground">
              {latestAudit ? new Date(latestAudit.timestamp).toLocaleString() : 'N/A'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Score Trend</CardTitle>
            <CardDescription>System audit scores over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics.slice(0, 10).reverse()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis domain={[70, 100]} />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value: any) => [`${value.toFixed(1)}%`, 'Score']}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  dot={{ fill: COLORS.primary }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Check Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Check Distribution</CardTitle>
            <CardDescription>Pass/Fail breakdown for latest audit</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Category Performance</CardTitle>
            <CardDescription>Performance by audit category</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: any) => [`${value}%`, 'Score']} />
                <Bar dataKey="score" fill={COLORS.primary} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Alert Status */}
        <Card>
          <CardHeader>
            <CardTitle>Alert Status</CardTitle>
            <CardDescription>Distribution of recent alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={statusDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill={COLORS.warning} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Latest system alerts and notifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentAlerts.slice(0, 5).map((alert) => (
              <div key={alert.alert_id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    alert.severity === 'critical' ? 'bg-red-500' :
                    alert.severity === 'warning' ? 'bg-yellow-500' :
                    alert.severity === 'error' ? 'bg-red-500' : 'bg-blue-500'
                  }`} />
                  <div>
                    <p className="font-medium">{alert.title}</p>
                    <p className="text-sm text-muted-foreground">{alert.message}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleString()}
                  </p>
                  {alert.acknowledged && (
                    <p className="text-xs text-green-600">Acknowledged</p>
                  )}
                </div>
              </div>
            ))}
            {recentAlerts.length === 0 && (
              <p className="text-center text-muted-foreground py-8">No recent alerts</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};