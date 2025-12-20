import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  BarChart3,
  TrendingUp,
  Users,
  Trophy,
  Star,
  Activity,
  Download,
  Settings,
  RefreshCw,
  Info,
} from 'lucide-react';

import EPAWPAAnalyticsDashboard from './EPAWPAAnalyticsDashboard';
import RecruitingAnalyticsDashboard from './RecruitingAnalyticsDashboard';
import RosterAnalyticsDashboard from './RosterAnalyticsDashboard';
import DraftAnalyticsDashboard from './DraftAnalyticsDashboard';

interface AnalyticsMetric {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  description: string;
}

interface AnalyticsFeature {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  status: 'active' | 'beta' | 'development';
  lastUpdated: string;
  dataPoints: number;
}

const AnalyticsHub: React.FC = () => {
  const [selectedDashboard, setSelectedDashboard] = useState<string>('overview');
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const analyticsFeatures: AnalyticsFeature[] = [
    {
      id: 'epa-wpa',
      name: 'EPA/WPA Analytics',
      description: 'Expected Points Added and Win Probability Advanced Metrics',
      icon: BarChart3,
      status: 'active',
      lastUpdated: '2025-12-18',
      dataPoints: 2500,
    },
    {
      id: 'recruiting',
      name: 'Recruiting Analytics',
      description: 'Comprehensive recruiting data analysis and talent evaluation',
      icon: Users,
      status: 'active',
      lastUpdated: '2025-12-18',
      dataPoints: 1800,
    },
    {
      id: 'roster',
      name: 'Roster Analytics',
      description: 'Team roster analysis and NFL draft projections',
      icon: TrendingUp,
      status: 'active',
      lastUpdated: '2025-12-18',
      dataPoints: 1200,
    },
    {
      id: 'draft',
      name: 'NFL Draft Analytics',
      description: 'Mock drafts, prospect analysis, and trade scenarios',
      icon: Trophy,
      status: 'active',
      lastUpdated: '2025-12-18',
      dataPoints: 3500,
    },
  ];

  const overallMetrics: AnalyticsMetric[] = [
    {
      title: 'Total Data Points',
      value: '9.0K',
      change: '+1.2K',
      trend: 'up',
      description: 'Total analytics data points processed',
    },
    {
      title: 'Active Features',
      value: '4',
      change: '+2',
      trend: 'up',
      description: 'Advanced analytics features deployed',
    },
    {
      title: 'API Integration',
      value: 'CFBD',
      change: 'Connected',
      trend: 'up',
      description: 'CFBD API integration status',
    },
    {
      title: 'Prediction Accuracy',
      value: '89.3%',
      change: '+5.2%',
      trend: 'up',
      description: 'Overall prediction accuracy improvement',
    },
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Simulate refresh delay
      await new Promise(resolve => setTimeout(resolve, 2000));
    } finally {
      setRefreshing(false);
    }
  };

  const exportAllData = () => {
    const dataStr = JSON.stringify({
      exportDate: new Date().toISOString(),
      analyticsHub: 'CFBD Advanced Analytics Integration',
      features: analyticsFeatures,
      metrics: overallMetrics,
      summary: {
        totalDataPoints: analyticsFeatures.reduce((sum, feature) => sum + feature.dataPoints, 0),
        activeFeatures: analyticsFeatures.filter(f => f.status === 'active').length,
        integrationStatus: 'Complete',
        lastUpdate: '2025-12-18',
      }
    }, null, 2);

    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = 'cfbd_analytics_hub_export.json';

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-600">Active</Badge>;
      case 'beta':
        return <Badge variant="secondary">Beta</Badge>;
      case 'development':
        return <Badge variant="outline">Development</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const renderDashboard = () => {
    switch (selectedDashboard) {
      case 'epa-wpa':
        return <EPAWPAAnalyticsDashboard />;
      case 'recruiting':
        return <RecruitingAnalyticsDashboard />;
      case 'roster':
        return <RosterAnalyticsDashboard />;
      case 'draft':
        return <DraftAnalyticsDashboard />;
      default:
        return <OverviewView />;
    }
  };

  const OverviewView = () => (
    <div className="space-y-6">
      <div className="text-center py-12">
        <Star className="h-16 w-16 text-blue-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">CFBD Advanced Analytics Hub</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Welcome to the comprehensive analytics dashboard for Script Ohio 2.0.
          Select any analytics module above to explore advanced insights powered by CollegeFootballData.com.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {analyticsFeatures.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card key={feature.id} className="hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => setSelectedDashboard(feature.id)}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="h-6 w-6 text-blue-600" />
                    <CardTitle className="text-lg">{feature.name}</CardTitle>
                  </div>
                  {getStatusBadge(feature.status)}
                </div>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center text-sm text-gray-600">
                  <span>{feature.dataPoints.toLocaleString()} data points</span>
                  <span>Updated: {feature.lastUpdated}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Integration Status</CardTitle>
          <CardDescription>Overall system health and integration metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">Complete</div>
              <div className="text-sm text-gray-600">Phase 1</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">Complete</div>
              <div className="text-sm text-gray-600">Phase 2</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">Complete</div>
              <div className="text-sm text-gray-600">Dashboard</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">Pending</div>
              <div className="text-sm text-gray-600">Validation</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">CFBD Analytics Hub</h1>
              <p className="text-gray-600">Advanced College Football Analytics Platform</p>
            </div>
            <div className="flex items-center gap-4">
              <Button
                onClick={handleRefresh}
                variant="outline"
                disabled={refreshing}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button onClick={exportAllData} variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export All
              </Button>
            </div>
          </div>

          {/* Overall Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 py-4">
            {overallMetrics.map((metric, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{metric.title}</p>
                    <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                    <div className="flex items-center mt-1">
                      {metric.trend === 'up' ? (
                        <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                      ) : (
                        <Activity className="h-4 w-4 text-red-600 mr-1" />
                      )}
                      <span className={`text-sm ${
                        metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {metric.change}
                      </span>
                    </div>
                  </div>
                  <Info className="h-5 w-5 text-gray-400" />
                </div>
                <p className="text-xs text-gray-500 mt-2">{metric.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Tabs value={selectedDashboard} onValueChange={setSelectedDashboard} className="w-full">
            <TabsList className="grid w-full grid-cols-5 h-auto p-1">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Star className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="epa-wpa" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                EPA/WPA
              </TabsTrigger>
              <TabsTrigger value="recruiting" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Recruiting
              </TabsTrigger>
              <TabsTrigger value="roster" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Roster
              </TabsTrigger>
              <TabsTrigger value="draft" className="flex items-center gap-2">
                <Trophy className="h-4 w-4" />
                Draft
              </TabsTrigger>
            </TabsList>

            <div className="p-4">
              {selectedDashboard !== 'overview' && (
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">
                      {analyticsFeatures.find(f => f.id === selectedDashboard)?.name}
                    </h2>
                    <p className="text-sm text-gray-600">
                      {analyticsFeatures.find(f => f.id === selectedDashboard)?.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(analyticsFeatures.find(f => f.id === selectedDashboard)?.status || 'development')}
                    <span className="text-sm text-gray-500">
                      {analyticsFeatures.find(f => f.id === selectedDashboard)?.dataPoints.toLocaleString()} data points
                    </span>
                  </div>
                </div>
              )}
            </div>
          </Tabs>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderDashboard()}
      </div>
    </div>
  );
};

export default AnalyticsHub;