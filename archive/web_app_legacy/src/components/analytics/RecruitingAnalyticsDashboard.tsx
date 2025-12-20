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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Treemap,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  Star,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Trophy,
  Award,
  Download,
  UserCheck,
  UserPlus,
  Calendar
} from 'lucide-react';

interface RecruitingClass {
  year: number;
  total_commits: number;
  five_star_count: number;
  four_star_count: number;
  three_star_count: number;
  average_rating: number;
  national_rank: number;
  conference_rank: number;
  class_score: number;
  momentum_score: number;
  needs_filled: number;
  position_breakdown: Record<string, number>;
}

interface Prospect {
  id: string;
  name: string;
  position: string;
  stars: number;
  rating: number;
  rank_national: number;
  rank_position: number;
  rank_state: number;
  height: string;
  weight: number;
  high_school: string;
  city: string;
  state: string;
  commitment_date: string;
  status: 'Committed' | 'Uncommitted' | 'Signed';
  crystal_ball: string;
  prediction_confidence: number;
}

interface PositionNeed {
  position: string;
  need_level: number;
  commits_filled: number;
  commits_needed: number;
  average_commit_rating: number;
  top_target: string;
  recruiting_momentum: number;
}

interface TalentCorrelation {
  position: string;
  recruiting_score: number;
  on_field_performance: number;
  correlation_strength: number;
  sample_size: number;
  success_rate: number;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff0000', '#00bfff', '#ff69b4'];

const RecruitingAnalyticsDashboard: React.FC = () => {
  const [selectedTeam, setSelectedTeam] = useState<string>('Ohio State');
  const [selectedYear, setSelectedYear] = useState<string>('2025');
  const [selectedView, setSelectedView] = useState<string>('current');
  const [loading, setLoading] = useState<boolean>(false);
  const [recruitingClass, setRecruitingClass] = useState<RecruitingClass | null>(null);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [positionNeeds, setPositionNeeds] = useState<PositionNeed[]>([]);
  const [talentCorrelations, setTalentCorrelations] = useState<TalentCorrelation[]>([]);
  const [historicalData, setHistoricalData] = useState<RecruitingClass[]>([]);

  // Mock data generation
  useEffect(() => {
    const fetchRecruitingData = async () => {
      setLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Generate mock recruiting class
        const mockClass: RecruitingClass = {
          year: parseInt(selectedYear),
          total_commits: 23,
          five_star_count: 3,
          four_star_count: 14,
          three_star_count: 6,
          average_rating: 92.3,
          national_rank: 2,
          conference_rank: 1,
          class_score: 298.45,
          momentum_score: 0.78,
          needs_filled: 18,
          position_breakdown: {
            'QB': 1, 'RB': 2, 'WR': 4, 'TE': 2, 'OT': 3, 'OG': 2,
            'DT': 2, 'DE': 3, 'LB': 2, 'CB': 1, 'S': 1
          }
        };

        // Generate mock prospects
        const mockProspects: Prospect[] = Array.from({ length: 23 }, (_, i) => ({
          id: `prospect_${i}`,
          name: `Top Prospect ${i + 1}`,
          position: ['QB', 'RB', 'WR', 'TE', 'OT', 'OG', 'DT', 'DE', 'LB', 'CB', 'S'][i % 11],
          stars: [5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 3][i % 11],
          rating: 0.98 - (i * 0.02),
          rank_national: i + 1,
          rank_position: (i % 5) + 1,
          rank_state: (i % 10) + 1,
          height: `${6 + Math.floor(i / 10)}'${(i % 12)}"`,
          weight: 200 + Math.floor(Math.random() * 100),
          high_school: `High School ${i + 1}`,
          city: 'City',
          state: 'OH',
          commitment_date: `2024-12-${String(i + 1).padStart(2, '0')}`,
          status: i < 18 ? 'Committed' : 'Uncommitted',
          crystal_ball: i < 18 ? selectedTeam : ['Team A', 'Team B'][i % 2],
          prediction_confidence: i < 18 ? 100 : 75 + Math.random() * 20
        }));

        // Generate mock position needs
        const mockPositionNeeds: PositionNeed[] = [
          { position: 'QB', need_level: 2, commits_filled: 1, commits_needed: 1, average_commit_rating: 95, top_target: '5-Star QB', recruiting_momentum: 0.85 },
          { position: 'WR', need_level: 4, commits_filled: 3, commits_needed: 1, average_commit_rating: 93, top_target: '5-Star WR', recruiting_momentum: 0.92 },
          { position: 'OT', need_level: 3, commits_filled: 2, commits_needed: 1, average_commit_rating: 94, top_target: '5-Star OT', recruiting_momentum: 0.78 },
          { position: 'DT', need_level: 2, commits_filled: 1, commits_needed: 1, average_commit_rating: 91, top_target: '4-Star DT', recruiting_momentum: 0.65 },
          { position: 'CB', need_level: 2, commits_filled: 0, commits_needed: 2, average_commit_rating: 0, top_target: '5-Star CB', recruiting_momentum: 0.88 },
        ];

        // Generate mock talent correlations
        const mockCorrelations: TalentCorrelation[] = [
          { position: 'QB', recruiting_score: 95, on_field_performance: 88, correlation_strength: 0.85, sample_size: 45, success_rate: 0.78 },
          { position: 'OT', recruiting_score: 92, on_field_performance: 90, correlation_strength: 0.82, sample_size: 38, success_rate: 0.82 },
          { position: 'WR', recruiting_score: 90, on_field_performance: 85, correlation_strength: 0.78, sample_size: 52, success_rate: 0.75 },
          { position: 'DE', recruiting_score: 93, on_field_performance: 87, correlation_strength: 0.80, sample_size: 41, success_rate: 0.79 },
          { position: 'LB', recruiting_score: 89, on_field_performance: 84, correlation_strength: 0.76, sample_size: 47, success_rate: 0.74 },
        ];

        // Generate historical data
        const mockHistorical: RecruitingClass[] = Array.from({ length: 5 }, (_, i) => ({
          year: 2025 - i,
          total_commits: 20 + Math.floor(Math.random() * 8),
          five_star_count: Math.floor(Math.random() * 4),
          four_star_count: 10 + Math.floor(Math.random() * 8),
          three_star_count: 8 + Math.floor(Math.random() * 6),
          average_rating: 88 + Math.random() * 6,
          national_rank: 1 + Math.floor(Math.random() * 8),
          conference_rank: 1 + Math.floor(Math.random() * 3),
          class_score: 250 + Math.random() * 80,
          momentum_score: 0.6 + Math.random() * 0.3,
          needs_filled: 15 + Math.floor(Math.random() * 6),
          position_breakdown: {}
        }));

        setRecruitingClass(mockClass);
        setProspects(mockProspects);
        setPositionNeeds(mockPositionNeeds);
        setTalentCorrelations(mockCorrelations);
        setHistoricalData(mockHistorical.reverse());
      } catch (error) {
        console.error('Error fetching recruiting data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecruitingData();
  }, [selectedTeam, selectedYear, selectedView]);

  const metricCards = useMemo(() => {
    if (!recruitingClass) return [];

    const metrics = [
      {
        title: 'National Ranking',
        value: `#${recruitingClass.national_rank}`,
        change: recruitingClass.national_rank <= 3 ? '+2' : '-1',
        trend: recruitingClass.national_rank <= 3 ? 'up' as const : 'down' as const,
        icon: Trophy,
        description: 'National recruiting class ranking',
      },
      {
        title: 'Average Rating',
        value: recruitingClass.average_rating.toFixed(1),
        change: '+1.2',
        trend: 'up' as const,
        icon: Star,
        description: 'Average prospect rating',
      },
      {
        title: '5-Star Commits',
        value: recruitingClass.five_star_count,
        change: `+${recruitingClass.five_star_count}`,
        trend: 'up' as const,
        icon: Award,
        description: 'Number of 5-star prospects',
      },
      {
        title: 'Momentum Score',
        value: `${(recruitingClass.momentum_score * 100).toFixed(0)}%`,
        change: '+5%',
        trend: 'up' as const,
        icon: TrendingUp,
        description: 'Recruiting momentum indicator',
      },
    ];

    return metrics;
  }, [recruitingClass]);

  const getNeedLevelColor = (level: number): string => {
    if (level >= 3) return 'text-red-600';
    if (level >= 2) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getStarRatingColor = (stars: number): string => {
    switch (stars) {
      case 5: return 'text-purple-600';
      case 4: return 'text-blue-600';
      case 3: return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const exportData = () => {
    const dataStr = JSON.stringify({
      recruitingClass,
      prospects,
      positionNeeds,
      talentCorrelations,
      historicalData,
      exportDate: new Date().toISOString(),
    }, null, 2);

    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `recruiting_analytics_${selectedTeam}_${selectedYear}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Users className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-lg font-medium">Loading Recruiting Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Recruiting Analytics Dashboard</h1>
          <p className="text-gray-600">Advanced recruiting analysis and talent evaluation</p>
        </div>
        <Button onClick={exportData} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* Controls */}
      <div className="flex gap-4 items-center bg-white p-4 rounded-lg border">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Team:</label>
          <Select value={selectedTeam} onValueChange={setSelectedTeam}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Ohio State">Ohio State</SelectItem>
              <SelectItem value="Alabama">Alabama</SelectItem>
              <SelectItem value="Georgia">Georgia</SelectItem>
              <SelectItem value="Clemson">Clemson</SelectItem>
              <SelectItem value="Texas">Texas</SelectItem>
            </SelectContent>
          </Select>
        </div>

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
          <label className="text-sm font-medium">View:</label>
          <Select value={selectedView} onValueChange={setSelectedView}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="current">Current</SelectItem>
              <SelectItem value="historical">Historical</SelectItem>
              <SelectItem value="comparison">Comparison</SelectItem>
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
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="prospects">Prospects</TabsTrigger>
          <TabsTrigger value="needs">Position Needs</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="correlation">Talent Correlation</TabsTrigger>
          <TabsTrigger value="momentum">Momentum</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Class Composition</CardTitle>
                <CardDescription>Distribution by star ratings</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <Treemap
                    data={[
                      { name: '5-Star', size: recruitingClass?.five_star_count || 0, fill: '#8884d8' },
                      { name: '4-Star', size: recruitingClass?.four_star_count || 0, fill: '#82ca9d' },
                      { name: '3-Star', size: recruitingClass?.three_star_count || 0, fill: '#ffc658' },
                    ]}
                    dataKey="size"
                    aspectRatio={4 / 3}
                    stroke="#fff"
                    fill="#8884d8"
                  />
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Position Breakdown</CardTitle>
                <CardDescription>Commits by position group</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={Object.entries(recruitingClass?.position_breakdown || {}).map(([pos, count]) => ({
                      position: pos,
                      commits: count,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="position" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="commits" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Prospects Tab */}
        <TabsContent value="prospects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Prospects</CardTitle>
              <CardDescription>Highest rated prospects in this class</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {prospects.slice(0, 10).map((prospect, index) => (
                  <div key={prospect.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium">{prospect.name}</p>
                        <p className="text-sm text-gray-600">{prospect.position} • {prospect.high_school}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className={`font-bold ${getStarRatingColor(prospect.stars)}`}>
                          {'★'.repeat(prospect.stars)}
                        </div>
                        <p className="text-sm text-gray-600">Rating: {prospect.rating.toFixed(3)}</p>
                      </div>
                      <Badge variant={prospect.status === 'Committed' ? 'default' : 'secondary'}>
                        {prospect.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Position Needs Tab */}
        <TabsContent value="needs" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Priority Position Needs</CardTitle>
                <CardDescription>Remaining needs and recruiting status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {positionNeeds.map((need, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{need.position}</span>
                        <span className={`font-bold ${getNeedLevelColor(need.need_level)}`}>
                          Need Level: {need.need_level}/3
                        </span>
                      </div>
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>{need.commits_filled} filled, {need.commits_needed} needed</span>
                        <span>Momentum: {(need.recruiting_momentum * 100).toFixed(0)}%</span>
                      </div>
                      <Progress
                        value={(need.commits_filled / (need.commits_filled + need.commits_needed)) * 100}
                        className="h-2"
                      />
                      {need.top_target && (
                        <p className="text-sm text-blue-600">Target: {need.top_target}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Target Radar</CardTitle>
                <CardDescription>Multi-dimensional analysis of position needs</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={positionNeeds}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="position" />
                    <PolarRadiusAxis angle={90} domain={[0, 3]} />
                    <Radar
                      name="Need Level"
                      dataKey="need_level"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="Momentum"
                      dataKey="recruiting_momentum"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.6}
                    />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Historical Performance</CardTitle>
              <CardDescription>Recruiting class rankings over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="national_rank"
                    stroke="#8884d8"
                    name="National Rank"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="average_rating"
                    stroke="#82ca9d"
                    name="Average Rating"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="momentum_score"
                    stroke="#ff7300"
                    name="Momentum"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Correlation Tab */}
        <TabsContent value="correlation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Talent Correlation Analysis</CardTitle>
              <CardDescription>Recruiting ratings vs on-field performance by position</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart data={talentCorrelations}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="recruiting_score" name="Recruiting Score" />
                  <YAxis dataKey="on_field_performance" name="On-Field Performance" />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload as TalentCorrelation;
                        return (
                          <div className="bg-white p-4 border rounded-lg shadow-lg">
                            <p className="font-medium">{data.position}</p>
                            <p className="text-sm">Recruiting Score: {data.recruiting_score}</p>
                            <p className="text-sm">On-Field Performance: {data.on_field_performance}</p>
                            <p className="text-sm">Correlation: {data.correlation_strength.toFixed(2)}</p>
                            <p className="text-sm">Success Rate: {(data.success_rate * 100).toFixed(1)}%</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter name="Positions" dataKey="on_field_performance" fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Momentum Tab */}
        <TabsContent value="momentum" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recruiting Momentum</CardTitle>
                <CardDescription>Recent commitment trends and momentum indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart
                    data={Array.from({ length: 30 }, (_, i) => ({
                      day: i + 1,
                      momentum: 0.6 + Math.random() * 0.3 + (i > 20 ? 0.2 : 0),
                      commitments: Math.floor(Math.random() * 3) + (i > 20 ? 1 : 0),
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="momentum"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Commitment Timeline</CardTitle>
                <CardDescription>Distribution of commitments by date</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['Early Period', 'Regular Season', 'Championship Week', 'Early Signing Day', 'Late Period'].map((period, index) => (
                    <div key={period} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{period}</span>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={Math.random() * 100}
                          className="w-24 h-2"
                        />
                        <span className="text-sm text-gray-600">{Math.floor(Math.random() * 8) + 1}</span>
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

export default RecruitingAnalyticsDashboard;