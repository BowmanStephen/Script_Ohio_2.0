import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Treemap,
  FunnelChart,
  Funnel,
  LabelList,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Star,
  Trophy,
  Award,
  Download,
  Calendar,
  DollarSign,
  Activity,
  Flag
} from 'lucide-react';

interface DraftProspect {
  id: string;
  name: string;
  position: string;
  school: string;
  height: string;
  weight: number;
  overall_grade: string;
  round_projection: number;
  pick_range: [number, number];
  positional_rank: number;
  overall_rank: number;
  forty_time?: number;
  production_score: number;
  athleticism_score: number;
  draft_stock_trend: 'Rising' | 'Falling' | 'Stable';
  risk_factor: number;
  ceiling_grade: string;
  floor_grade: string;
  top_team_fits: string[];
  nfl_success_probability: number;
  pro_bowl_probability: number;
}

interface MockDraftConsensus {
  consensus_round: number;
  consensus_pick: number;
  prospect_name: string;
  position: string;
  school: string;
  agreement_level: number;
  confidence_score: number;
  volatility_score: number;
  pick_range: [number, number];
  team_probability: Record<string, number>;
}

interface TeamDraftAnalysis {
  team: string;
  current_picks: Array<[number, number]>;
  total_pick_value: number;
  positional_needs: Record<string, number>;
  target_prospects: string[];
  draft_class_grade: string;
  value_acquired: number;
  risk_assessment: number;
}

interface DraftTradeValue {
  current_pick: [number, number];
  target_pick: [number, number];
  current_pick_value: number;
  target_pick_value: number;
  value_difference: number;
  recommended_compensation: Array<[number, number]>;
  trade_probability: number;
  risk_assessment: number;
  reward_potential: number;
}

interface DraftPrediction {
  prospect_name: string;
  draft_probability: number;
  average_pick: number;
  pick_range: [number, number];
  most_common_team: string;
  team_probability: Record<string, number>;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff0000', '#00bfff', '#ff69b4'];

const DraftAnalyticsDashboard: React.FC = () => {
  const [selectedYear, setSelectedYear] = useState<string>('2025');
  const [selectedRound, setSelectedRound] = useState<string>('1');
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>('prospects');
  const [loading, setLoading] = useState<boolean>(false);
  const [prospects, setProspects] = useState<DraftProspect[]>([]);
  const [mockDraftConsensus, setMockDraftConsensus] = useState<MockDraftConsensus[]>([]);
  const [teamAnalysis, setTeamAnalysis] = useState<TeamDraftAnalysis[]>([]);
  const [tradeScenarios, setTradeScenarios] = useState<DraftTradeValue[]>([]);
  const [predictions, setPredictions] = useState<DraftPrediction[]>([]);

  // Mock data generation
  useEffect(() => {
    const fetchDraftData = async () => {
      setLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Generate mock prospects
        const mockProspects: DraftProspect[] = Array.from({ length: 100 }, (_, i) => {
          const positions = ['QB', 'OT', 'DE', 'WR', 'CB', 'DT', 'LB', 'S', 'TE', 'EDGE', 'OG', 'C'];
          const grades = ['Elite', 'First Round', 'Second Round', 'Third Round', 'Middle Rounds', 'Late Rounds'];
          const trends = ['Rising', 'Falling', 'Stable'];

          return {
            id: `prospect_${i}`,
            name: `Draft Prospect ${i + 1}`,
            position: positions[i % positions.length],
            school: ['Ohio State', 'Alabama', 'Georgia', 'Clemson', 'Texas'][i % 5],
            height: `${6 + Math.floor(i / 20)}'${(i % 12)}"`,
            weight: 180 + Math.floor(Math.random() * 140),
            overall_grade: grades[Math.min(Math.floor(i / 16), grades.length - 1)],
            round_projection: Math.min(Math.floor(i / 15) + 1, 7),
            pick_range: [Math.max(1, i * 2 - 10), i * 2 + 10] as [number, number],
            positional_rank: (i % 10) + 1,
            overall_rank: i + 1,
            forty_time: 4.2 + Math.random() * 1.2,
            production_score: Math.random(),
            athleticism_score: Math.random(),
            draft_stock_trend: trends[Math.floor(Math.random() * trends.length)] as any,
            risk_factor: Math.random(),
            ceiling_grade: grades[Math.max(0, Math.floor(i / 20) - 1)],
            floor_grade: grades[Math.min(grades.length - 1, Math.floor(i / 15) + 2)],
            top_team_fits: ['Chiefs', 'Bills', 'Cowboys', 'Packers', 'Ravens'].slice(0, 3),
            nfl_success_probability: Math.random(),
            pro_bowl_probability: Math.random() * 0.5,
          };
        });

        // Generate mock draft consensus
        const mockConsensus: MockDraftConsensus[] = Array.from({ length: 32 }, (_, i) => ({
          consensus_round: 1,
          consensus_pick: i + 1,
          prospect_name: mockProspects[i]?.name || `Prospect ${i + 1}`,
          position: mockProspects[i]?.position || 'QB',
          school: mockProspects[i]?.school || 'School',
          agreement_level: Math.random(),
          confidence_score: Math.random(),
          volatility_score: Math.random(),
          pick_range: [Math.max(1, i - 2), i + 3] as [number, number],
          team_probability: {
            'Chiefs': Math.random(),
            'Bills': Math.random(),
            'Cowboys': Math.random(),
            'Packers': Math.random(),
            'Ravens': Math.random(),
          },
        }));

        // Generate mock team analysis
        const mockTeamAnalysis: TeamDraftAnalysis[] = [
          {
            team: 'Chiefs',
            current_picks: [[1, 32], [2, 65], [3, 96], [4, 130]],
            total_pick_value: 2500,
            positional_needs: { 'CB': 0.9, 'WR': 0.7, 'OT': 0.8, 'DE': 0.6 },
            target_prospects: mockProspects.slice(0, 5).map(p => p.name),
            draft_class_grade: 'A-',
            value_acquired: 0.85,
            risk_assessment: 0.3,
          },
          {
            team: 'Bills',
            current_picks: [[1, 28], [2, 60], [3, 92], [5, 167]],
            total_pick_value: 2800,
            positional_needs: { 'WR': 0.9, 'S': 0.7, 'LB': 0.8, 'DT': 0.5 },
            target_prospects: mockProspects.slice(5, 10).map(p => p.name),
            draft_class_grade: 'B+',
            value_acquired: 0.78,
            risk_assessment: 0.4,
          },
        ];

        // Generate mock trade scenarios
        const mockTradeScenarios: DraftTradeValue[] = [
          {
            current_pick: [1, 15],
            target_pick: [1, 5],
            current_pick_value: 1050,
            target_pick_value: 1700,
            value_difference: -650,
            recommended_compensation: [[2, 45], [3, 80]],
            trade_probability: 0.25,
            risk_assessment: 0.7,
            reward_potential: 0.9,
          },
          {
            current_pick: [2, 10],
            target_pick: [1, 32],
            current_pick_value: 490,
            target_pick_value: 590,
            value_difference: -100,
            recommended_compensation: [[4, 120]],
            trade_probability: 0.65,
            risk_assessment: 0.3,
            reward_potential: 0.6,
          },
        ];

        // Generate mock predictions
        const mockPredictions: DraftPrediction[] = mockProspects.slice(0, 20).map(prospect => ({
          prospect_name: prospect.name,
          draft_probability: Math.random(),
          average_pick: Math.floor(Math.random() * 100) + 1,
          pick_range: [Math.floor(Math.random() * 50) + 1, Math.floor(Math.random() * 50) + 51] as [number, number],
          most_common_team: ['Chiefs', 'Bills', 'Cowboys', 'Packers'][Math.floor(Math.random() * 4)],
          team_probability: {
            'Chiefs': Math.random(),
            'Bills': Math.random(),
            'Cowboys': Math.random(),
            'Packers': Math.random(),
          },
        }));

        setProspects(mockProspects);
        setMockDraftConsensus(mockConsensus);
        setTeamAnalysis(mockTeamAnalysis);
        setTradeScenarios(mockTradeScenarios);
        setPredictions(mockPredictions);
      } catch (error) {
        console.error('Error fetching draft data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDraftData();
  }, [selectedYear, selectedRound, selectedAnalysis]);

  const metricCards = useMemo(() => {
    const totalProspects = prospects.length;
    const firstRoundProspects = prospects.filter(p => p.round_projection === 1).length;
    const averageRisk = prospects.reduce((sum, p) => sum + p.risk_factor, 0) / totalProspects;
    const risingStock = prospects.filter(p => p.draft_stock_trend === 'Rising').length;

    const metrics = [
      {
        title: 'Total Prospects',
        value: totalProspects,
        change: '+15',
        trend: 'up' as const,
        icon: Users,
        description: 'Prospects analyzed',
      },
      {
        title: '1st Round Prospects',
        value: firstRoundProspects,
        change: '+3',
        trend: 'up' as const,
        icon: Star,
        description: 'Projected first rounders',
      },
      {
        title: 'Average Risk',
        value: `${(averageRisk * 100).toFixed(0)}%`,
        change: '-5%',
        trend: 'down' as const,
        icon: AlertTriangle,
        description: 'Average risk factor',
      },
      {
        title: 'Rising Stock',
        value: risingStock,
        change: '+8',
        trend: 'up' as const,
        icon: TrendingUp,
        description: 'Players with rising draft stock',
      },
    ];

    return metrics;
  }, [prospects]);

  const getGradeColor = (grade: string): string => {
    switch (grade) {
      case 'Elite': return 'text-purple-600';
      case 'First Round': return 'text-blue-600';
      case 'Second Round': return 'text-green-600';
      case 'Third Round': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const exportData = () => {
    const dataStr = JSON.stringify({
      prospects,
      mockDraftConsensus,
      teamAnalysis,
      tradeScenarios,
      predictions,
      exportDate: new Date().toISOString(),
    }, null, 2);

    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `draft_analytics_${selectedYear}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Trophy className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-lg font-medium">Loading Draft Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">NFL Draft Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive draft analysis, projections, and trade scenarios</p>
        </div>
        <Button onClick={exportData} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* Controls */}
      <div className="flex gap-4 items-center bg-white p-4 rounded-lg border">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Year:</label>
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2023">2023</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Round:</label>
          <Select value={selectedRound} onValueChange={setSelectedRound}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1st</SelectItem>
              <SelectItem value="2">2nd</SelectItem>
              <SelectItem value="3">3rd</SelectItem>
              <SelectItem value="all">All</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Analysis:</label>
          <Select value={selectedAnalysis} onValueChange={setSelectedAnalysis}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="prospects">Prospects</SelectItem>
              <SelectItem value="teams">Teams</SelectItem>
              <SelectItem value="trades">Trades</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((metric, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{metric.title}</p>
                  <p className="text-2xl font-bold">{metric.value}</p>
                  <div className="flex items-center mt-1">
                    <metric.icon className={`h-4 w-4 mr-1 ${
                      metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`} />
                    <span className={`text-sm ${
                      metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {metric.change}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{metric.description}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="prospects" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="prospects">Prospects</TabsTrigger>
          <TabsTrigger value="mock-draft">Mock Draft</TabsTrigger>
          <TabsTrigger value="teams">Team Analysis</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="trades">Trade Analysis</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        {/* Prospects Tab */}
        <TabsContent value="prospects" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Top Prospects by Position</CardTitle>
                <CardDescription>Highest rated prospects at each position</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Array.from(new Set(prospects.map(p => p.position))).slice(0, 6).map(position => {
                    const topProspect = prospects
                      .filter(p => p.position === position)
                      .sort((a, b) => a.overall_rank - b.overall_rank)[0];

                    return topProspect ? (
                      <div key={position} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold">
                            {position}
                          </div>
                          <div>
                            <p className="font-medium">{topProspect.name}</p>
                            <p className="text-sm text-gray-600">{topProspect.school} • #{topProspect.overall_rank}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-medium ${getGradeColor(topProspect.overall_grade)}`}>
                            {topProspect.overall_grade}
                          </p>
                          <p className="text-sm text-gray-600">
                            Round {topProspect.round_projection}
                          </p>
                        </div>
                      </div>
                    ) : null;
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Position Distribution</CardTitle>
                <CardDescription>Distribution of prospects by position</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Array.from(new Set(prospects.map(p => p.position))).map(position => ({
                        position,
                        count: prospects.filter(p => p.position === position).length,
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ position, count }) => `${position}: ${count}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {prospects.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Mock Draft Tab */}
        <TabsContent value="mock-draft" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Consensus Mock Draft</CardTitle>
              <CardDescription>Round 1 consensus with confidence levels</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockDraftConsensus.slice(0, 10).map((consensus, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                        {consensus.consensus_pick}
                      </div>
                      <div>
                        <p className="font-medium">{consensus.prospect_name}</p>
                        <p className="text-sm text-gray-600">
                          {consensus.position} • {consensus.school}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">Confidence</p>
                        <p className="text-sm text-gray-600">
                          {(consensus.confidence_score * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">Volatility</p>
                        <p className="text-sm text-gray-600">
                          {(consensus.volatility_score * 100).toFixed(0)}%
                        </p>
                      </div>
                      <Badge variant={consensus.agreement_level > 0.7 ? 'default' : 'secondary'}>
                        {consensus.agreement_level > 0.7 ? 'High' : 'Medium'} Consensus
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Teams Tab */}
        <TabsContent value="teams" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Team Draft Capital</CardTitle>
                <CardDescription>Total draft pick value by team</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={teamAnalysis}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="team" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="total_pick_value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Positional Needs Analysis</CardTitle>
                <CardDescription>Team needs by position</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {teamAnalysis.map((team) => (
                    <div key={team.team} className="space-y-2">
                      <h3 className="font-medium">{team.team}</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(team.positional_needs).map(([position, need]) => (
                          <div key={position} className="flex items-center gap-2">
                            <span className="text-sm w-4">{position}:</span>
                            <Progress value={need * 100} className="flex-1 h-2" />
                            <span className="text-xs">{(need * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predictions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Draft Probability Analysis</CardTitle>
              <CardDescription>Monte Carlo simulation results</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart data={predictions}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="average_pick" name="Average Pick" />
                  <YAxis dataKey="draft_probability" name="Draft Probability" />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload as DraftPrediction;
                        return (
                          <div className="bg-white p-4 border rounded-lg shadow-lg">
                            <p className="font-medium">{data.prospect_name}</p>
                            <p className="text-sm">Avg Pick: {data.average_pick}</p>
                            <p className="text-sm">Draft Prob: {(data.draft_probability * 100).toFixed(1)}%</p>
                            <p className="text-sm">Most Likely: {data.most_common_team}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter name="Prospects" dataKey="draft_probability" fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trade Analysis Tab */}
        <TabsContent value="trades" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trade Scenarios</CardTitle>
              <CardDescription>Analysis of potential draft day trades</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {tradeScenarios.map((trade, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-medium">
                          Trade: {trade.current_pick[0]}.{trade.current_pick[1]} → {trade.target_pick[0]}.{trade.target_pick[1]}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Value Difference: {trade.value_difference > 0 ? '+' : ''}{trade.value_difference} points
                        </p>
                      </div>
                      <Badge variant={trade.trade_probability > 0.5 ? 'default' : 'secondary'}>
                        {(trade.trade_probability * 100).toFixed(0)}% Probability
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm font-medium">Risk Assessment</p>
                        <Progress value={trade.risk_assessment * 100} className="h-2 mt-1" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Reward Potential</p>
                        <Progress value={trade.reward_potential * 100} className="h-2 mt-1" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Current Value</p>
                        <p className="text-lg font-bold">{trade.current_pick_value}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Target Value</p>
                        <p className="text-lg font-bold">{trade.target_pick_value}</p>
                      </div>
                    </div>

                    {trade.recommended_compensation.length > 0 && (
                      <div className="mt-4">
                        <p className="text-sm font-medium mb-2">Recommended Compensation:</p>
                        <div className="flex gap-2 flex-wrap">
                          {trade.recommended_compensation.map((pick, i) => (
                            <Badge key={i} variant="outline">
                              {pick[0]}.{pick[1]}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk vs Reward Analysis</CardTitle>
                <CardDescription>Prospect risk factors vs potential rewards</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart data={prospects.slice(0, 50)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="risk_factor" name="Risk Factor" />
                    <YAxis dataKey="nfl_success_probability" name="NFL Success Probability" />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload as DraftProspect;
                          return (
                            <div className="bg-white p-4 border rounded-lg shadow-lg">
                              <p className="font-medium">{data.name}</p>
                              <p className="text-sm">{data.position} • {data.school}</p>
                              <p className="text-sm">Risk: {(data.risk_factor * 100).toFixed(0)}%</p>
                              <p className="text-sm">NFL Success: {(data.nfl_success_probability * 100).toFixed(0)}%</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter name="Prospects" dataKey="nfl_success_probability" fill="#8884d8" />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Draft Stock Trends</CardTitle>
                <CardDescription>Analysis of player draft stock movements</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['Rising', 'Falling', 'Stable'].map(trend => (
                    <div key={trend} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {trend === 'Rising' && <TrendingUp className="h-4 w-4 text-green-600" />}
                        {trend === 'Falling' && <TrendingDown className="h-4 w-4 text-red-600" />}
                        {trend === 'Stable' && <Activity className="h-4 w-4 text-blue-600" />}
                        <span className="font-medium">{trend}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-lg font-bold">
                          {prospects.filter(p => p.draft_stock_trend === trend).length}
                        </span>
                        <div className="w-32">
                          <Progress
                            value={(prospects.filter(p => p.draft_stock_trend === trend).length / prospects.length) * 100}
                            className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DraftAnalyticsDashboard;