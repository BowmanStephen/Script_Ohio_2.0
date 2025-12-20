import React from 'react';
import { AIAssistant } from '../components/AIAssistant';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Bot, Brain, TrendingUp, Database, BookOpen, Zap } from 'lucide-react';

const features = [
  {
    icon: Database,
    title: 'Data Analysis',
    description: 'Analyze team performance, compare statistics, and identify trends in college football data.',
    color: 'bg-blue-100 text-blue-800'
  },
  {
    icon: TrendingUp,
    title: 'Game Predictions',
    description: 'Get predictions using our ML models (Ridge, XGBoost, FastAI) with confidence intervals.',
    color: 'bg-green-100 text-green-800'
  },
  {
    icon: Zap,
    title: 'Task Automation',
    description: 'Automate data updates, generate reports, and schedule recurring analysis tasks.',
    color: 'bg-orange-100 text-orange-800'
  },
  {
    icon: BookOpen,
    title: 'Learning Guidance',
    description: 'Learn about our models, analytics methodologies, and college football insights.',
    color: 'bg-purple-100 text-purple-800'
  }
];

const exampleQueries = [
  {
    category: 'Data Analysis',
    queries: [
      'Analyze Ohio State\'s performance this season',
      'Compare Alabama and Georgia defensive statistics',
      'Show me the top 10 offensive teams this year',
      'What are Ohio State\'s strengths and weaknesses?'
    ]
  },
  {
    category: 'Predictions',
    queries: [
      'Predict the Ohio State vs Michigan game',
      'Who will win the national championship?',
      'Generate predictions for all Week 14 games',
      'What\'s the probability of an upset this week?'
    ]
  },
  {
    category: 'Task Automation',
    queries: [
      'Generate a weekly analysis report',
      'Update team statistics with latest data',
      'Create a dashboard for season performance',
      'Schedule automated predictions for Saturdays'
    ]
  },
  {
    category: 'Learning',
    queries: [
      'Explain how your prediction models work',
      'Teach me about college football analytics',
      'What metrics do you use for team evaluation?',
      'How accurate are your predictions?'
    ]
  }
];

export function AIAssistantPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Brain className="h-8 w-8 text-blue-600" />
          AI Assistant
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Your conversational interface to college football analytics. Ask questions in natural language
          and get intelligent responses powered by our specialized agents.
        </p>
      </div>

      {/* Features Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {features.map((feature, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-2">
                <feature.icon className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-sm">
                {feature.description}
              </CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Assistant Chat */}
        <div className="lg:col-span-2">
          <AIAssistant
            onAnalysisRequest={(query) => {
              console.log('Analysis requested:', query);
              // Could trigger data visualization or detailed analysis
            }}
            onPredictionRequest={(query) => {
              console.log('Prediction requested:', query);
              // Could open prediction modal or navigate to predictions page
            }}
          />
        </div>

        {/* Example Queries */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Bot className="h-5 w-5" />
                Example Queries
              </CardTitle>
              <CardDescription>
                Click any example to try it out
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs defaultValue="analysis" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="analysis">Analysis</TabsTrigger>
                  <TabsTrigger value="predictions">Predictions</TabsTrigger>
                  <TabsTrigger value="automation">Automation</TabsTrigger>
                  <TabsTrigger value="learning">Learning</TabsTrigger>
                </TabsList>

                {exampleQueries.map((category) => (
                  <TabsContent key={category.category} value={category.category.toLowerCase()} className="space-y-2">
                    <div className="text-sm font-medium text-gray-600">
                      {category.category}
                    </div>
                    <div className="space-y-1">
                      {category.queries.map((query, index) => (
                        <div
                          key={index}
                          className="text-sm p-2 rounded bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
                          onClick={() => {
                            // This could be enhanced to actually send the query to the AI Assistant
                            console.log('Query clicked:', query);
                          }}
                        >
                          "{query}"
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </CardContent>
          </Card>

          {/* Capabilities */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Capabilities</CardTitle>
              <CardDescription>
                What the AI Assistant can do for you
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Natural Language Processing</span>
                <Badge variant="secondary">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Intent Recognition</span>
                <Badge variant="secondary">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Conversation Memory</span>
                <Badge variant="secondary">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Agent Orchestration</span>
                <Badge variant="secondary">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Data Integration</span>
                <Badge variant="secondary">CFBD Connected</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Integration Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Integration Information</CardTitle>
          <CardDescription>
            How the AI Assistant integrates with your system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">Available Interfaces</h4>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Web Application (current page)</li>
                <li>• Command Line Interface (CLI)</li>
                <li>• REST API Endpoints</li>
                <li>• Agent Framework Integration</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Connected Agents</h4>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• CFBD Integration Agent (data)</li>
                <li>• Model Execution Engine (predictions)</li>
                <li>• Analytics Orchestrator (analysis)</li>
                <li>• Learning Navigator (education)</li>
                <li>• Workflow Automator (automation)</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}