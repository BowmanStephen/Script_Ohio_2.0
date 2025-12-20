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
  FunnelChart,
  Funnel,
  LabelList,
  Cell,
} from 'recharts';
import {
  Users,
  Shield,
  TrendingUp,
  TrendingDown,
  Award,
  AlertTriangle,
  Target,
  Star,
  UserCheck,
  UserPlus,
  UserMinus,
  Download,
  Calendar,
  Dribbble,
  Flag
} from 'lucide-react';

interface Player {
  id: string;
  name: string;
  position: string;
  year: 'FR' | 'SO' | 'JR' | 'SR' | 'GR';
  height: string;
  weight: number;
  rating: number;
  nfl_draft_grade: string;
  draft_projection: number;
  experience: number;
  starts: number;
  games_played: number;
  status: 'Active' | 'Injured' | 'Transfer' | 'NFL Draft Eligible';
  transfer_risk: number;
  nfl_readiness: number;
  pro_potential: number;
}

interface PositionGroup {
  position: string;
  total_players: number;
  starters_count: number;
  depth_chart_quality: number;
  average_rating: number;
  nfl_draft_prospects: number;
  experience_level: number;
  future_outlook: number;
  transfer_portal_risk: number;
}

interface NFLDraftProjection {
  player_name: string;
  position: string;
  current_round: number;
  projection_range: [number, number];
  draft_probability: number;
  mock_draft_consensus: number;
  stock_trend: 'Rising' | 'Falling' | 'Stable';
  nfl_comparison: string;
}

interface DepthChart {
  position: string;
  depth: number;
  player_name: string;
  year: string;
  rating: number;
  experience: number;
  nfl_ready: boolean;
  special_teams_contributor: boolean;
}

interface TransferPortalAnalysis {
  player_name: string;
  position: string;
  current_risk: number;
  factors: string[];
  ncaa_transfer_rules: string[];
  potential_destinations: string[];
  replacement_quality: number;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff0000', '#00bfff', '#ff69b4'];

const RosterAnalyticsDashboard: React.FC = () => {
  const [selectedTeam, setSelectedTeam] = useState<string>('Ohio State');
  const [selectedSeason, setSelectedSeason] = useState<string>('2025');
  const [selectedView, setSelectedView] = useState<string>('current');
  const [loading, setLoading] = useState<boolean>(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [positionGroups, setPositionGroups] = useState<PositionGroup[]>([]);
  const [nflProjections, setNflProjections] = useState<NFLDraftProjection[]>([]);
  const [depthChart, setDepthChart] = useState<DepthChart[]>([]);
  const [transferAnalysis, setTransferAnalysis] = useState<TransferPortalAnalysis[]>([]);

  // Mock data generation
  useEffect(() => {
    const fetchRosterData = async () => {
      setLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Generate mock players
        const mockPlayers: Player[] = Array.from({ length: 85 }, (_, i) => {
          const positions = ['QB', 'RB', 'WR', 'TE', 'OT', 'OG', 'C', 'DT', 'DE', 'LB', 'CB', 'S', 'K', 'P'];
          const years = ['FR', 'SO', 'JR', 'SR', 'GR'];
          const statuses = ['Active', 'Active', 'Active', 'Injured', 'Transfer', 'NFL Draft Eligible'];

          return {
            id: `player_${i}`,
            name: `Player ${i + 1}`,
            position: positions[i % positions.length],
            year: years[Math.floor(i / 17)] as any,
            height: `${6 + Math.floor(i / 15)}'${(i % 12)}"`,
            weight: 180 + Math.floor(Math.random() * 120),
            rating: 0.75 + Math.random() * 0.25,
            nfl_draft_grade: ['1st Round', '2nd Round', '3rd Round', 'Mid Rounds', 'Late Rounds', 'UDFA'][Math.floor(Math.random() * 6)],
            draft_projection: Math.floor(Math.random() * 250) + 1,
            experience: Math.floor(Math.random() * 4) + 1,
            starts: Math.floor(Math.random() * 30),
            games_played: Math.floor(Math.random() * 40) + 5,
            status: statuses[Math.floor(Math.random() * statuses.length)] as any,
            transfer_risk: Math.random(),
            nfl_readiness: Math.random(),
            pro_potential: Math.random(),
          };
        });

        // Generate mock position groups
        const mockPositionGroups: PositionGroup[] = [
          { position: 'QB', total_players: 4, starters_count: 1, depth_chart_quality: 0.92, average_rating: 0.95, nfl_draft_prospects: 2, experience_level: 0.85, future_outlook: 0.90, transfer_portal_risk: 0.15 },
          { position: 'RB', total_players: 6, starters_count: 2, depth_chart_quality: 0.88, average_rating: 0.91, nfl_draft_prospects: 3, experience_level: 0.75, future_outlook: 0.85, transfer_portal_risk: 0.25 },
          { position: 'WR', total_players: 8, starters_count: 3, depth_chart_quality: 0.90, average_rating: 0.93, nfl_draft_prospects: 4, experience_level: 0.70, future_outlook: 0.88, transfer_portal_risk: 0.20 },
          { position: 'OT', total_players: 6, starters_count: 2, depth_chart_quality: 0.85, average_rating: 0.89, nfl_draft_prospects: 3, experience_level: 0.80, future_outlook: 0.82, transfer_portal_risk: 0.18 },
          { position: 'DT', total_players: 5, starters_count: 2, depth_chart_quality: 0.87, average_rating: 0.90, nfl_draft_prospects: 2, experience_level: 0.72, future_outlook: 0.84, transfer_portal_risk: 0.22 },
          { position: 'LB', total_players: 7, starters_count: 3, depth_chart_quality: 0.83, average_rating: 0.88, nfl_draft_prospects: 3, experience_level: 0.78, future_outlook: 0.80, transfer_portal_risk: 0.28 },
        ];

        // Generate mock NFL projections
        const mockNflProjections: NFLDraftProjection[] = [
          { player_name: 'Star QB', position: 'QB', current_round: 1, projection_range: [1, 5], draft_probability: 0.95, mock_draft_consensus: 3, stock_trend: 'Rising', nfl_comparison: 'Patrick Mahomes' },
          { player_name: 'Elite WR', position: 'WR', current_round: 1, projection_range: [5, 15], draft_probability: 0.88, mock_draft_consensus: 12, stock_trend: 'Stable', nfl_comparison: 'Ja'Marr Chase' },
          { player_name: 'Dominant DE', position: 'DE', current_round: 1, projection_range: [3, 12], draft_probability: 0.92, mock_draft_consensus: 8, stock_trend: 'Rising', nfl_comparison: 'Nick Bosa' },
          { player_name: 'Shutdown CB', position: 'CB', current_round: 2, projection_range: [25, 45], draft_probability: 0.78, mock_draft_consensus: 32, stock_trend: 'Falling', nfl_comparison: 'Jaire Alexander' },
          { player_name: 'Franchise OT', position: 'OT', current_round: 1, projection_range: [8, 20], draft_probability: 0.85, mock_draft_consensus: 15, stock_trend: 'Stable', nfl_comparison: 'Trent Williams' },
        ];

        // Generate mock depth chart
        const mockDepthChart: DepthChart[] = [];
        const positions = ['QB', 'RB', 'WR', 'TE', 'LT', 'LG', 'C', 'RG', 'RT', 'DE', 'DT', 'LB', 'CB', 'S'];

        positions.forEach((position) => {
          for (let depth = 1; depth <= 3; depth++) {
            mockDepthChart.push({
              position,
              depth,
              player_name: `Player ${position} Depth ${depth}`,
              year: ['SR', 'JR', 'SO', 'FR'][depth - 1],
              rating: 0.95 - (depth - 1) * 0.15,
              experience: depth === 1 ? 3 : depth === 2 ? 2 : 1,
              nfl_ready: depth <= 2,
              special_teams_contributor: depth >= 2,
            });
          }
        });

        // Generate mock transfer portal analysis
        const mockTransferAnalysis: TransferPortalAnalysis[] = [
          {
            player_name: 'Backup QB',
            position: 'QB',
            current_risk: 0.75,
            factors: ['Buried on depth chart', 'Graduate transfer eligible', 'Limited playing time'],
            ncaa_transfer_rules: ['Immediate eligibility', 'Graduate transfer'],
            potential_destinations: ['Miami', 'Washington', 'Oregon'],
            replacement_quality: 0.70
          },
          {
            player_name: ' sophomore WR',
            position: 'WR',
            current_risk: 0.60,
            factors: ['Heavy competition', 'Seeking more targets'],
            ncaa_transfer_rules: ['One-time transfer'],
            potential_destinations: ['TCU', 'Ole Miss', 'USC'],
            replacement_quality: 0.65
          },
        ];

        setPlayers(mockPlayers);
        setPositionGroups(mockPositionGroups);
        setNflProjections(mockNflProjections);
        setDepthChart(mockDepthChart);
        setTransferAnalysis(mockTransferAnalysis);
      } catch (error) {
        console.error('Error fetching roster data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRosterData();
  }, [selectedTeam, selectedSeason, selectedView]);

  const metricCards = useMemo(() => {
    const totalPlayers = players.length;
    const nflDraftProspects = players.filter(p => p.draft_projection <= 100).length;
    const averageExperience = players.reduce((sum, p) => sum + p.experience, 0) / totalPlayers;
    const highTransferRisk = players.filter(p => p.transfer_risk > 0.7).length;

    const metrics = [
      {
        title: 'Total Players',
        value: totalPlayers,
        change: '+3',
        trend: 'up' as const,
        icon: Users,
        description: 'Total roster count',
      },
      {
        title: 'NFL Draft Prospects',
        value: nflDraftProspects,
        change: '+2',
        trend: 'up' as const,
        icon: Star,
        description: 'Players projected in top 100',
      },
      {
        title: 'Avg Experience',
        value: `${averageExperience.toFixed(1)} yrs`,
        change: '+0.3',
        trend: 'up' as const,
        icon: Calendar,
        description: 'Average player experience',
      },
      {
        title: 'High Transfer Risk',
        value: highTransferRisk,
        change: '-1',
        trend: 'down' as const,
        icon: AlertTriangle,
        description: 'Players with >70% transfer risk',
      },
    ];

    return metrics;
  }, [players]);

  const getDraftRoundColor = (round: number): string => {
    switch (round) {
      case 1: return 'text-purple-600';
      case 2: return 'text-blue-600';
      case 3: return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getTransferRiskColor = (risk: number): string => {
    if (risk >= 0.7) return 'text-red-600';
    if (risk >= 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  const exportData = () => {
    const dataStr = JSON.stringify({
      players,
      positionGroups,
      nflProjections,
      depthChart,
      transferAnalysis,
      exportDate: new Date().toISOString(),
    }, null, 2);

    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `roster_analytics_${selectedTeam}_${selectedSeason}.json`;

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
          <p className="text-lg font-medium">Loading Roster Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Roster Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive roster analysis and NFL draft projections</p>
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

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">View:</label>
          <Select value={selectedView} onValueChange={setSelectedView}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="current">Current</SelectItem>
              <SelectItem value="future">Future</SelectItem>
              <SelectItem value="historical">Historical</SelectItem>
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
          <TabsTrigger value="position-groups">Position Groups</TabsTrigger>
          <TabsTrigger value="depth-chart">Depth Chart</TabsTrigger>
          <TabsTrigger value="nfl-draft">NFL Draft</TabsTrigger>
          <TabsTrigger value="transfer-portal">Transfer Portal</TabsTrigger>
          <TabsTrigger value="analytics">Advanced Analytics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Class Distribution</CardTitle>
                <CardDescription>Roster composition by academic year</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={['FR', 'SO', 'JR', 'SR', 'GR'].map(year => ({
                      year,
                      count: players.filter(p => p.year === year).length,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Roster Quality</CardTitle>
                <CardDescription>Player rating distribution</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart
                    data={Array.from({ length: 10 }, (_, i) => ({
                      rating: 0.7 + i * 0.03,
                      players: players.filter(p => p.rating >= 0.7 + i * 0.03 && p.rating < 0.7 + (i + 1) * 0.03).length,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="rating" tickFormatter={(value) => value.toFixed(2)} />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="players"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Position Groups Tab */}
        <TabsContent value="position-groups" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Position Group Analysis</CardTitle>
              <CardDescription>Depth chart quality and future outlook by position</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {positionGroups.map((group, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-medium text-lg">{group.position}</h3>
                        <p className="text-sm text-gray-600">
                          {group.total_players} players, {group.starters_count} starters
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className="text-lg">
                          {(group.depth_chart_quality * 100).toFixed(0)}%
                        </Badge>
                        <p className="text-xs text-gray-500">Depth Quality</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Avg Rating</p>
                        <p className="font-medium">{(group.average_rating * 100).toFixed(1)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">NFL Prospects</p>
                        <p className="font-medium">{group.nfl_draft_prospects}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Experience</p>
                        <Progress value={group.experience_level * 100} className="h-2 mt-2" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Transfer Risk</p>
                        <Progress
                          value={group.transfer_portal_risk * 100}
                          className="h-2 mt-2"
                          indicatorClassName="bg-red-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Depth Chart Tab */}
        <TabsContent value="depth-chart" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Interactive Depth Chart</CardTitle>
              <CardDescription>Complete depth chart with player ratings and NFL readiness</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Array.from(new Set(depthChart.map(d => d.position))).map(position => (
                  <div key={position} className="space-y-2">
                    <h3 className="font-medium text-lg">{position}</h3>
                    <div className="space-y-2">
                      {depthChart
                        .filter(d => d.position === position)
                        .sort((a, b) => a.depth - b.depth)
                        .map(player => (
                          <div key={`${position}-${player.depth}`} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center gap-4">
                              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                                {player.depth}
                              </div>
                              <div>
                                <p className="font-medium">{player.player_name}</p>
                                <p className="text-sm text-gray-600">{player.year} • {player.experience} yrs exp</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-right">
                                <p className="font-medium">{(player.rating * 100).toFixed(1)}</p>
                                <div className="flex gap-2">
                                  {player.nfl_ready && (
                                    <Badge variant="default" className="text-xs">NFL Ready</Badge>
                                  )}
                                  {player.special_teams_contributor && (
                                    <Badge variant="secondary" className="text-xs">ST</Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* NFL Draft Tab */}
        <TabsContent value="nfl-draft" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Top NFL Draft Prospects</CardTitle>
                <CardDescription>Players with NFL draft potential</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {nflProjections.map((prospect, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                          {prospect.current_round}
                        </div>
                        <div>
                          <p className="font-medium">{prospect.player_name}</p>
                          <p className="text-sm text-gray-600">
                            {prospect.position} • {prospect.nfl_comparison}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className={`font-medium ${getDraftRoundColor(prospect.current_round)}`}>
                            Round {prospect.current_round}
                          </p>
                          <p className="text-sm text-gray-600">
                            Picks {prospect.projection_range[0]}-{projection_range[1]}
                          </p>
                        </div>
                        <Badge variant={prospect.stock_trend === 'Rising' ? 'default' : prospect.stock_trend === 'Falling' ? 'destructive' : 'secondary'}>
                          {prospect.stock_trend}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Draft Probability Distribution</CardTitle>
                <CardDescription>likelihood of being drafted by round</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <FunnelChart>
                    <Funnel
                      data={[
                        { name: '1st Round', value: nflProjections.filter(p => p.current_round === 1).length },
                        { name: '2nd Round', value: nflProjections.filter(p => p.current_round === 2).length },
                        { name: '3rd Round', value: nflProjections.filter(p => p.current_round === 3).length },
                        { name: 'Mid Rounds', value: nflProjections.filter(p => p.current_round >= 4 && p.current_round <= 7).length },
                      ]}
                      dataKey="value"
                      fill="#8884d8"
                    >
                      <LabelList position="center" fill="#fff" fontSize={12} />
                    </Funnel>
                  </FunnelChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Transfer Portal Tab */}
        <TabsContent value="transfer-portal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Transfer Portal Risk Analysis</CardTitle>
              <CardDescription>Players at risk of entering transfer portal</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {transferAnalysis.map((analysis, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-medium">{analysis.player_name}</h3>
                        <p className="text-sm text-gray-600">{analysis.position}</p>
                      </div>
                      <Badge variant={analysis.current_risk >= 0.7 ? 'destructive' : analysis.current_risk >= 0.4 ? 'secondary' : 'default'}>
                        {(analysis.current_risk * 100).toFixed(0)}% Risk
                      </Badge>
                    </div>

                    <div className="space-y-2">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Risk Factors:</p>
                        <ul className="list-disc list-inside text-sm text-gray-600">
                          {analysis.factors.map((factor, i) => (
                            <li key={i}>{factor}</li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-700">Potential Destinations:</p>
                        <div className="flex gap-2 flex-wrap mt-1">
                          {analysis.potential_destinations.map((dest, i) => (
                            <Badge key={i} variant="outline">{dest}</Badge>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-700">Replacement Quality:</p>
                        <Progress value={analysis.replacement_quality * 100} className="h-2 mt-1" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Experience vs Rating Correlation</CardTitle>
                <CardDescription>Player experience level compared to rating</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart data={players}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="experience" name="Experience" />
                    <YAxis dataKey="rating" name="Rating" />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload as Player;
                          return (
                            <div className="bg-white p-4 border rounded-lg shadow-lg">
                              <p className="font-medium">{data.name}</p>
                              <p className="text-sm">{data.position} • {data.year}</p>
                              <p className="text-sm">Experience: {data.experience} years</p>
                              <p className="text-sm">Rating: {(data.rating * 100).toFixed(1)}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter name="Players" dataKey="rating" fill="#8884d8" />
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Position Group Radar</CardTitle>
                <CardDescription>Multi-dimensional analysis of position groups</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={positionGroups.slice(0, 5)}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="position" />
                    <PolarRadiusAxis angle={90} domain={[0, 1]} />
                    <Radar
                      name="Depth Quality"
                      dataKey="depth_chart_quality"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="Future Outlook"
                      dataKey="future_outlook"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="Experience"
                      dataKey="experience_level"
                      stroke="#ffc658"
                      fill="#ffc658"
                      fillOpacity={0.6}
                    />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RosterAnalyticsDashboard;