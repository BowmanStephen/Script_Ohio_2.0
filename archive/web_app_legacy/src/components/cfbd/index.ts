// Enhanced CFBD Analytics Components
// CollegeFootballData.com Premium Integration Components

export { default as CFBDEnhancedAnalyticsDashboard } from './CFBDEnhancedAnalyticsDashboard';
export { default as AdvancedAnalyticsAgentView } from './AdvancedAnalyticsAgentView';

// Component information for documentation
export const CFBD_COMPONENTS = [
  {
    name: 'CFBDEnhancedAnalyticsDashboard',
    description: 'Comprehensive dashboard showcasing CFBD premium features and performance metrics',
    props: [],
    features: [
      'Real-time performance monitoring',
      'Premium feature status tracking',
      'Tier optimization metrics',
      'API performance indicators',
      'Data processing statistics'
    ]
  },
  {
    name: 'AdvancedAnalyticsAgentView',
    description: 'Interactive interface for the Advanced Analytics Agent with execution monitoring',
    props: [],
    features: [
      '5 major analytics capabilities',
      'Real-time execution monitoring',
      'Performance metrics tracking',
      'Execution history logs',
      'Report generation tools'
    ]
  }
] as const;