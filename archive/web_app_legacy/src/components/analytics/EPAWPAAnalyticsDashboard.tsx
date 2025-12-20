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
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChartIcon,
  ScatterChartIcon,
  Download
} from 'lucide-react';

interface EPAMetrics {
  offense_epa_per_game: number;
  defense_epa_per_game: number;
  net_epa: number;
  offense_wpa_per_game: number;
  defense_wpa_per_game: number;
  net_wpa: number;
  success_rate: number;
  explosiveness: number;
  power_success: number;
  stuff_rate: number;
  line_yards: number;
  line_yards_total: number;
  second_level_yards: number;
  open_field_yards: number;
}

interface GameEPAData {
  game_id: number;
  week: number;
  opponent: string;
  is_home: boolean;
  offense_epa: number;
  defense_epa: number;
  net_epa: number;
  offense_wpa: number;
  defense_wpa: number;
  net_wpa: number;
  result: 'Win' | 'Loss';
  score: string;
}

interface TrendData {
  week: number;
  offense_epa: number;
  defense_epa: number;
  net_epa: number;
  offense_wpa: number;
  defense_wpa: number;
  net_wpa: number;
  success_rate: number;
  explosiveness: number;
}

interface ComparisonData {
  team: string;
  offense_epa: number;
  defense_epa: number;
  net_epa: number;
  offense_wpa: number;
  defense_wpa: number;
  net_wpa: number;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff0000'];

const EPAWPAAnalyticsDashboard: React.FC = () => {
  const [selectedTeam, setSelectedTeam] = useState<string>('Ohio State');
  const [selectedSeason, setSelectedSeason] = useState<string>('2025');
  const [selectedMetric, setSelectedMetric] = useState<string>('net_epa');
  const [loading, setLoading] = useState<boolean>(false);
  const [teamMetrics, setTeamMetrics] = useState<EPAMetrics | null>(null);
  const [gameData, setGameData] = useState<GameEPAData[]>([]);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonData[]>([]);

  // Mock data generation - would be replaced with API calls
  useEffect(() => {
    const fetchEPAData = async () => {
      setLoading(true);
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Generate mock team metrics
        const mockMetrics: EPAMetrics = {
          offense_epa_per_game: 0.28,
          defense_epa_per_game: -0.15,
          net_epa: 0.43,
          offense_wpa_per_game: 0.05,
          defense_wpa_per_game: -0.03,
          net_wpa: 0.08,
          success_rate: 0.48,
          explosiveness: 1.2,
          power_success: 0.72,
          stuff_rate: 0.18,
          line_yards: 2.8,
          line_yards_total: 3.5,
          second_level_yards: 2.1,
          open_field_yards: 1.6,
        };

        // Generate mock game data
        const mockGameData: GameEPAData[] = Array.from({ length: 10 }, (_, i) => ({
          game_id: i + 1,
          week: i + 1,
          opponent: ['Oregon', 'Penn State', 'Michigan', 'Iowa', 'Wisconsin'][i % 5],
          is_home: i % 2 === 0,
          offense_epa: 0.15 + (Math.random() - 0.5) * 0.4,
          defense_epa: -0.1 + (Math.random() - 0.5) * 0.3,
          net_epa: 0.25 + (Math.random() - 0.5) * 0.5,
          offense_wpa: 0.02 + (Math.random() - 0.5) * 0.1,
          defense_wpa: -0.01 + (Math.random() - 0.5) * 0.08,
          net_wpa: 0.03 + (Math.random() - 0.5) * 0.12,
          result: Math.random() > 0.3 ? 'Win' : 'Loss',
          score: `${35 + Math.floor(Math.random() * 20)}-${14 + Math.floor(Math.random() * 15)}`
        }));

        // Generate mock trend data
        const mockTrendData: TrendData[] = Array.from({ length: 14 }, (_, i) => ({
          week: i + 1,
          offense_epa: 0.2 + (Math.random() - 0.5) * 0.3,
          defense_epa: -0.12 + (Math.random() - 0.5) * 0.2,
          net_epa: 0.32 + (Math.random() - 0.5) * 0.4,
          offense_wpa: 0.04 + (Math.random() - 0.5) * 0.08,
          defense_wpa: -0.02 + (Math.random() - 0.5) * 0.06,
          net_wpa: 0.06 + (Math.random() - 0.5) * 0.1,
          success_rate: 0.45 + (Math.random() - 0.5) * 0.1,
          explosiveness: 1.1 + (Math.random() - 0.5) * 0.3,
        }));

        // Generate mock comparison data
        const mockComparisonData: ComparisonData[] = [
          { team: 'Ohio State', offense_epa: 0.28, defense_epa: -0.15, net_epa: 0.43, offense_wpa: 0.05, defense_wpa: -0.03, net_wpa: 0.08 },
          { team: 'Oregon', offense_epa: 0.31, defense_epa: -0.18, net_epa: 0.49, offense_wpa: 0.06, defense_wpa: -0.04, net_wpa: 0.10 },
          { team: 'Georgia', offense_epa: 0.25, defense_epa: -0.22, net_epa: 0.47, offense_wpa: 0.04, defense_wpa: -0.05, net_wpa: 0.09 },
          { team: 'Texas', offense_epa: 0.22, defense_epa: -0.12, net_epa: 0.34, offense_wpa: 0.03, defense_wpa: -0.02, net_wpa: 0.05 },
          { team: 'Alabama', offense_epa: 0.26, defense_epa: -0.16, net_epa: 0.42, offense_wpa: 0.045, defense_wpa: -0.035, net_wpa: 0.08 },
        ];

        setTeamMetrics(mockMetrics);
        setGameData(mockGameData);
        setTrendData(mockTrendData);
        setComparisonData(mockComparisonData);
      } catch (error) {
        console.error('Error fetching EPA data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEPAData();
  }, [selectedTeam, selectedSeason]);

  const metricCards = useMemo(() => {
    if (!teamMetrics) return [];

    const metrics = [
      {
        title: 'Offense EPA/Game',
        value: teamMetrics.offense_epa_per_game.toFixed(2),
        change: '+0.05',
        trend: 'up' as const,
        icon: TrendingUp,
        description: 'Expected Points Added per offensive possession',
      },
      {
        title: 'Defense EPA/Game',
        value: teamMetrics.defense_epa_per_game.toFixed(2),
        change: '-0.02',
        trend: 'down' as const,
        icon: TrendingDown,
        description: 'Expected Points Saved per defensive possession',
      },
      {
        title: 'Net EPA/Game',
        value: teamMetrics.net_epa.toFixed(2),
        change: '+0.07',
        trend: 'up' as const,
        icon: Activity,
        description: 'Overall EPA differential per game',
      },
      {
        title: 'Success Rate',
        value: `${(teamMetrics.success_rate * 100).toFixed(1)}%`,
        change: '+2.3%',
        trend: 'up' as const,
        icon: Target,
        description: 'Percentage of successful plays',
      },
    ];

    return metrics;
  }, [teamMetrics]);

  const getPerformanceGrade = (value: number, metric: string): { grade: string; color: string } => {
    const thresholds = {
      net_epa: { A: 0.4, B: 0.2, C: 0.1, D: 0 },
      offense_epa_per_game: { A: 0.3, B: 0.2, C: 0.1, D: 0 },
      defense_epa_per_game: { A: -0.2, B: -0.1, C: -0.05, D: 0 },
      success_rate: { A: 0.5, B: 0.45, C: 0.4, D: 0.35 },
      explosiveness: { A: 1.3, B: 1.2, C: 1.1, D: 1.0 },
    };

    const threshold = thresholds[metric as keyof typeof thresholds] || thresholds.net_epa;

    let grade = 'D';
    let color = 'text-red-600';

    if (metric.includes('defense')) {
      if (value <= threshold.A) { grade = 'A'; color = 'text-green-600'; }
      else if (value <= threshold.B) { grade = 'B'; color = 'text-blue-600'; }
      else if (value <= threshold.C) { grade = 'C'; color = 'text-yellow-600'; }
    } else {
      if (value >= threshold.A) { grade = 'A'; color = 'text-green-600'; }
      else if (value >= threshold.B) { grade = 'B'; color = 'text-blue-600'; }
      else if (value >= threshold.C) { grade = 'C'; color = 'text-yellow-600'; }
    }

    return { grade, color };
  };

  const exportData = () => {
    const dataStr = JSON.stringify({
      teamMetrics,
      gameData,
      trendData,
      comparisonData,
      exportDate: new Date().toISOString(),
    }, null, 2);

    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `epa_wpa_analytics_${selectedTeam}_${selectedSeason}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-lg font-medium">Loading EPA/WPA Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">EPA/WPA Analytics Dashboard</h1>
          <p className="text-gray-600">Advanced Expected Points Added & Win Probability Analysis</p>
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
              <SelectItem value="Oregon">Oregon</SelectItem>
              <SelectItem value="Georgia">Georgia</SelectItem>
              <SelectItem value="Texas">Texas</SelectItem>
              <SelectItem value="Alabama">Alabama</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Season:</label>
          <Select value={selectedSeason} onValueChange={setSelectedSeason}>
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
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="games">Game Analysis</TabsTrigger>
          <TabsTrigger value="comparison">Team Comparison</TabsTrigger>
          <TabsTrigger value="advanced">Advanced Metrics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Season EPA Performance</CardTitle>
                <CardDescription>Offense vs Defense Expected Points Added</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[teamMetrics].map(m => ({
                    name: selectedTeam,
                    'Offense EPA': m?.offense_epa_per_game || 0,
                    'Defense EPA': Math.abs(m?.defense_epa_per_game || 0),
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Offense EPA" fill="#8884d8" />
                    <Bar dataKey="Defense EPA" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Grades</CardTitle>
                <CardDescription>Key metrics graded against national averages</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {teamMetrics && [
                  { metric: 'Net EPA', value: teamMetrics.net_epa, key: 'net_epa' },
                  { metric: 'Offense EPA/Game', value: teamMetrics.offense_epa_per_game, key: 'offense_epa_per_game' },
                  { metric: 'Defense EPA/Game', value: teamMetrics.defense_epa_per_game, key: 'defense_epa_per_game' },
                  { metric: 'Success Rate', value: teamMetrics.success_rate, key: 'success_rate' },
                ].map((item, index) => {
                  const { grade, color } = getPerformanceGrade(item.value, item.key);
                  return (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{item.metric}:</span>
                        <Badge variant="outline" className={color}>
                          {grade}
                        </Badge>
                      </div>
                      <span className="text-sm text-gray-600">
                        {typeof item.value === 'number'
                          ? item.key === 'success_rate'
                            ? `${(item.value * 100).toFixed(1)}%`
                            : item.value.toFixed(2)
                          : item.value
                        }
                      </span>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Season Trends</CardTitle>
              <CardDescription>Weekly EPA/WPA performance trends throughout the season</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="offense_epa" stroke="#8884d8" name="Offense EPA" strokeWidth={2} />
                  <Line type="monotone" dataKey="defense_epa" stroke="#82ca9d" name="Defense EPA" strokeWidth={2} />
                  <Line type="monotone" dataKey="net_epa" stroke="#ff7300" name="Net EPA" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Game Analysis Tab */}
        <TabsContent value="games" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Game-by-Game Performance</CardTitle>
              <CardDescription>EPA/WPA breakdown for each game this season</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart data={gameData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="offense_epa" name="Offense EPA" />
                  <YAxis dataKey="defense_epa" name="Defense EPA" />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload as GameEPAData;
                        return (
                          <div className="bg-white p-4 border rounded-lg shadow-lg">
                            <p className="font-medium">{data.opponent} (Week {data.week})</p>
                            <p className="text-sm">Score: {data.score}</p>
                            <p className="text-sm">Result: {data.result}</p>
                            <p className="text-sm">Offense EPA: {data.offense_epa.toFixed(2)}</p>
                            <p className="text-sm">Defense EPA: {data.defense_epa.toFixed(2)}</p>
                            <p className="text-sm">Net EPA: {data.net_epa.toFixed(2)}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter name="Games" dataKey="defense_epa" fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comparison Tab */}
        <TabsContent value="comparison" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Team Comparison</CardTitle>
              <CardDescription>Compare EPA/WPA metrics across top teams</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="team" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="offense_epa" fill="#8884d8" name="Offense EPA" />
                  <Bar dataKey="defense_epa" fill="#82ca9d" name="Defense EPA" />
                  <Bar dataKey="net_epa" fill="#ff7300" name="Net EPA" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Metrics Tab */}
        <TabsContent value="advanced" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Run Game Breakdown</CardTitle>
                <CardDescription>Line, second level, and open field yards analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Line Yards', value: teamMetrics?.line_yards || 0 },
                        { name: 'Second Level', value: teamMetrics?.second_level_yards || 0 },
                        { name: 'Open Field', value: teamMetrics?.open_field_yards || 0 },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {[0, 1, 2].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Key Efficiency Metrics</CardTitle>
                <CardDescription>Advanced team performance indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {teamMetrics && [
                  { label: 'Power Success', value: teamMetrics.power_success, max: 1 },
                  { label: 'Stuff Rate', value: teamMetrics.stuff_rate, max: 1 },
                  { label: 'Explosiveness', value: teamMetrics.explosiveness, max: 2 },
                ].map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{item.label}</span>
                      <span>{item.value.toFixed(2)}</span>
                    </div>
                    <Progress
                      value={(item.value / item.max) * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EPAWPAAnalyticsDashboard;