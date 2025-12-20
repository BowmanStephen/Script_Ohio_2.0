/**
 * Unified Postseason Dashboard
 *
 * A comprehensive dashboard that combines the audit dashboard predictions
 * with bowl analytics for a cohesive postseason experience.
 *
 * Features:
 * - Live predictions against the spread
 * - Value opportunities analysis
 * - Model performance tracking
 * - Bowl game breakdowns with radar charts
 * - Tournament bracket visualization
 * - Historical performance trends
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import {
  Trophy,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Calendar,
  DollarSign,
  Shield,
  BarChart3,
  Eye,
  Star,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Brain,
  Cpu,
  Network
} from 'lucide-react';

// Import our new model comparison component
import { ModelComparisonDashboard } from './ModelComparisonDashboard';

// Recharts components
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from 'recharts';

// Types
interface PostseasonGame {
  id: number;
  date: string;
  home_team: string;
  away_team: string;
  home_win_prob: number;
  away_win_prob: number;
  predicted_margin: number;
  confidence: number;
  predicted_winner?: string;
  massey_prediction?: number;
  simple_prediction?: number;
  conference?: string;
  stadium?: string;
  location?: string;
  bowl_name?: string;
  year: number;
  actual_margin?: number;
  actual_winner?: string;
  spread?: number;
  over_under?: number;
  value_rating?: number;

  // New model details structure
  model_details?: {
    ridge?: {
      margin?: number;
      probability?: number;
    };
    xgb?: {
      margin?: number;
      probability?: number;
    };
    fastai?: {
      margin?: number;
      probability?: number;
    };
  };
}

interface ModelPerformance {
  model: string;
  accuracy: number;
  avg_error: number;
  confidence_score: number;
  value_games_found: number;
}

interface ValueOpportunity {
  game_id: number;
  game: string;
  prediction: string;
  spread: number;
  predicted_margin: number;
  value_score: number;
  confidence: number;
}

const COLORS = {
  primary: '#3b82f6',
  secondary: '#6b7280',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  gold: '#f59e0b',
  silver: '#6b7280',
  bronze: '#92400e',
  upset: '#8b5cf6',
  favorite: '#059669',
};

const BOWL_GAME_MAPPING = {
  401778123: { name: "Cricket Celebration Bowl", date: "2025-12-13" },
  401778302: { name: "Bucked Up LA Bowl", date: "2025-12-14" },
  401778303: { name: "IS4S Salute to Veterans Bowl", date: "2025-12-15" },
  401778304: { name: "StaffDNA Cure Bowl", date: "2025-12-16" },
  401778305: { name: "Hancock Whitney Stadium Bowl", date: "2025-12-17" },
  401778306: { name: "Tony the Tiger Sun Bowl", date: "2025-12-20" },
  401778307: { name: "Fiesta Bowl", date: "2025-12-31" },
  401778308: { name: "Rose Bowl", date: "2025-01-01" },
  401778309: { name: "Sugar Bowl", date: "2025-01-01" },
  401778310: { name: "Orange Bowl", date: "2025-01-02" },
  401778311: { name: "Cotton Bowl", date: "2025-12-29" },
  401778312: { name: "Peach Bowl", date: "2025-12-31" },
  401778313: { name: "CFP National Championship", date: "2025-01-20" },
};

const UnifiedPostseasonDashboard: React.FC = () => {
  const [games, setGames] = useState<PostseasonGame[]>([]);
  const [teamStats, setTeamStats] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [selectedGame, setSelectedGame] = useState<PostseasonGame | null>(null);
  const [modelPerformance, setModelPerformance] = useState<ModelPerformance[]>([]);

  // Fetch postseason data
  useEffect(() => {
    const fetchPostseasonData = async () => {
      setLoading(true);
      try {
        // Fetch bowl games
        const gamesResponse = await fetch('http://localhost:5002/api/bowl-games');
        const gamesData = await gamesResponse.json();

        if (gamesData.success) {
          // Enhance games with bowl information
          const enhancedGames = gamesData.games.map((game: PostseasonGame) => {
            const bowlInfo = BOWL_GAME_MAPPING[game.id as keyof typeof BOWL_GAME_MAPPING];
            return {
              ...game,
              bowl_name: bowlInfo?.name || `Bowl Game ${game.id}`,
              date: bowlInfo?.date || game.date,
              // Add mock spread and value data for demonstration
              spread: game.predicted_margin > 0 ? -game.predicted_margin : Math.abs(game.predicted_margin),
              value_rating: Math.abs(game.predicted_margin) > 5 ? 0.8 : 0.3,
              over_under: 45 + Math.random() * 30,
            };
          });
          setGames(enhancedGames);
        }

        // Fetch team stats
        const statsResponse = await fetch('http://localhost:5002/api/team-stats');
        const statsData = await statsResponse.json();
        if (statsData.success) {
          setTeamStats(statsData.stats);
        }

      } catch (err) {
        setError('Failed to load postseason data');
        console.error('Error loading postseason data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPostseasonData();
  }, []);

  // Model performance data (mock for now)
  useEffect(() => {
    setModelPerformance([
      { model: 'ML Ensemble', accuracy: 68.5, avg_error: 4.2, confidence_score: 0.74, value_games_found: 12 },
      { model: 'Massey Ratings', accuracy: 65.2, avg_error: 4.8, confidence_score: 0.71, value_games_found: 8 },
      { model: 'Simple Model', accuracy: 62.1, avg_error: 5.3, confidence_score: 0.68, value_games_found: 5 },
    ]);
  }, []);

  // Value opportunities analysis
  const valueOpportunities = useMemo(() => {
    return games
      .filter(game => game.spread && game.value_rating && game.value_rating > 0.7)
      .map(game => ({
        game_id: game.id,
        game: `${game.away_team} vs ${game.home_team}`,
        prediction: game.predicted_margin > 0 ? game.home_team : game.away_team,
        spread: game.spread || 0,
        predicted_margin: game.predicted_margin,
        value_score: game.value_rating || 0,
        confidence: game.confidence,
      }))
      .sort((a, b) => b.value_score - a.value_score)
      .slice(0, 10);
  }, [games]);

  // Confidence distribution
  const confidenceDistribution = useMemo(() => {
    const ranges = [
      { range: '90-100%', count: 0, color: COLORS.success },
      { range: '80-89%', count: 0, color: COLORS.primary },
      { range: '70-79%', count: 0, color: COLORS.warning },
      { range: '60-69%', count: 0, color: COLORS.secondary },
      { range: '< 60%', count: 0, color: COLORS.danger },
    ];

    games.forEach(game => {
      const confidence = game.confidence * 100;
      if (confidence >= 90) ranges[0].count++;
      else if (confidence >= 80) ranges[1].count++;
      else if (confidence >= 70) ranges[2].count++;
      else if (confidence >= 60) ranges[3].count++;
      else ranges[4].count++;
    });

    return ranges;
  }, [games]);

  // Prepare radar data for selected game
  const prepareRadarData = (game: PostseasonGame) => {
    if (!game) return [];

    const homeStats = teamStats[game.home_team];
    const awayStats = teamStats[game.away_team];

    return [
      { stat: 'Offense', home: homeStats?.offense_rating || 75, away: awayStats?.offense_rating || 75 },
      { stat: 'Defense', home: homeStats?.defense_rating || 75, away: awayStats?.defense_rating || 75 },
      { stat: 'Special Teams', home: homeStats?.special_teams || 75, away: awayStats?.special_teams || 75 },
      { stat: 'Strength of Schedule', home: homeStats?.strength_of_schedule || 75, away: awayStats?.strength_of_schedule || 75 },
      { stat: 'Recent Form', home: homeStats?.recent_form || 75, away: awayStats?.recent_form || 75 },
      { stat: 'Turnover Margin', home: homeStats?.turnover_margin || 0, away: awayStats?.turnover_margin || 0 },
    ];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-lg font-semibold">Loading Postseason Analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-lg font-semibold text-red-600">{error}</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Trophy className="h-8 w-8 text-yellow-500" />
            2025 Postseason Analytics Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            Comprehensive bowl game predictions, value opportunities, and performance analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            December 18, 2025
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Target className="h-4 w-4" />
            {games.length} Games
          </Badge>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Bowl Games</CardTitle>
            <Trophy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{games.length}</div>
            <p className="text-xs text-muted-foreground">
              Active predictions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Value Opportunities</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{valueOpportunities.length}</div>
            <p className="text-xs text-muted-foreground">
              High-value bets found
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {games.length > 0 ? (games.reduce((sum, g) => sum + g.confidence, 0) / games.length * 100).toFixed(1) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              Model confidence
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ML Model Accuracy</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">68.5%</div>
            <p className="text-xs text-muted-foreground">
              Historical performance
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="predictions">Game Predictions</TabsTrigger>
          <TabsTrigger value="models">Model Comparison</TabsTrigger>
          <TabsTrigger value="value">Value Analysis</TabsTrigger>
          <TabsTrigger value="performance">Model Performance</TabsTrigger>
          <TabsTrigger value="breakdown">Game Breakdown</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Games by Date */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Upcoming Bowl Games</CardTitle>
                <CardDescription>
                  Chronological schedule of all postseason matchups
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {games.slice(0, 10).map((game) => (
                    <div key={game.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                         onClick={() => setSelectedGame(game)}>
                      <div className="flex-1">
                        <div className="font-semibold text-sm">{game.bowl_name}</div>
                        <div className="text-xs text-gray-600">
                          {game.away_team} vs {game.home_team}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(game.date).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">
                          {game.predicted_margin > 0 ? `${game.home_team} ${game.predicted_margin.toFixed(1)}` : `${game.away_team} ${Math.abs(game.predicted_margin).toFixed(1)}`}
                        </div>
                        <div className="text-xs text-gray-600">
                          {(game.confidence * 100).toFixed(0)}% confidence
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Confidence Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Prediction Confidence Distribution</CardTitle>
                <CardDescription>
                  How confident our models are in each prediction
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={confidenceDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill={COLORS.primary} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Top Value Opportunities */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-500" />
                Top Value Opportunities
              </CardTitle>
              <CardDescription>
                Games where our predictions significantly differ from the spread
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {valueOpportunities.slice(0, 5).map((opp, index) => (
                  <div key={opp.game_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="text-lg font-bold text-gray-500">#{index + 1}</div>
                      <div>
                        <div className="font-semibold">{opp.game}</div>
                        <div className="text-sm text-gray-600">
                          Prediction: {opp.prediction} ({opp.predicted_margin > 0 ? '+' : ''}{opp.predicted_margin.toFixed(1)})
                        </div>
                        <div className="text-sm text-gray-600">
                          Spread: {opp.spread > 0 ? `${opp.away_team} ${opp.spread.toFixed(1)}` : `${opp.home_team} ${Math.abs(opp.spread).toFixed(1)}`}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-600">
                        {(opp.value_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-gray-600">Value Score</div>
                      <Badge variant={opp.value_score > 0.8 ? "default" : "secondary"}>
                        {opp.confidence > 0.7 ? "High Confidence" : "Medium Confidence"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="predictions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>All Bowl Game Predictions</CardTitle>
              <CardDescription>
                Complete list of postseason predictions with confidence scores
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Bowl Game</th>
                      <th className="text-left p-2">Matchup</th>
                      <th className="text-center p-2">Date</th>
                      <th className="text-center p-2">Prediction</th>
                      <th className="text-center p-2">Margin</th>
                      <th className="text-center p-2">Confidence</th>
                      <th className="text-center p-2">Spread</th>
                      <th className="text-center p-2">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {games.map((game) => (
                      <tr key={game.id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-semibold">{game.bowl_name}</td>
                        <td className="p-2">
                          {game.away_team} vs {game.home_team}
                        </td>
                        <td className="p-2 text-center text-sm">
                          {new Date(game.date).toLocaleDateString()}
                        </td>
                        <td className="p-2 text-center">
                          {game.predicted_margin > 0 ? game.home_team : game.away_team}
                        </td>
                        <td className="p-2 text-center">
                          {game.predicted_margin > 0 ? '+' : ''}{game.predicted_margin.toFixed(1)}
                        </td>
                        <td className="p-2 text-center">
                          <Badge variant={game.confidence > 0.7 ? "default" : "secondary"}>
                            {(game.confidence * 100).toFixed(0)}%
                          </Badge>
                        </td>
                        <td className="p-2 text-center">
                          {game.spread ? (game.spread > 0 ? `${game.away_team} ${game.spread.toFixed(1)}` : `${game.home_team} ${Math.abs(game.spread).toFixed(1)}`) : 'N/A'}
                        </td>
                        <td className="p-2 text-center">
                          {game.value_rating ? (
                            <Badge variant={game.value_rating > 0.7 ? "default" : "secondary"}>
                              {(game.value_rating * 100).toFixed(0)}%
                            </Badge>
                          ) : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-500" />
                ML Model Comparison Dashboard
              </CardTitle>
              <CardDescription>
                Detailed comparison of all 4 machine learning models with individual predictions and consensus analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Info className="h-4 w-4" />
                  <span>
                    <strong>FBS-Only Data:</strong> {games.length} games filtered for FBS teams only
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Network className="h-4 w-4" />
                  <span>
                    <strong>Models:</strong> Ridge Regression, XGBoost, FastAI Neural Network, Ensemble Method
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Model Comparison Dashboard Component */}
          <ModelComparisonDashboard />
        </TabsContent>

        <TabsContent value="value" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-green-500" />
                Value Betting Analysis
              </CardTitle>
              <CardDescription>
                Identify games where our models predict outcomes that differ significantly from betting lines
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Value Opportunities */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">High Value Opportunities</h3>
                  <div className="space-y-4">
                    {valueOpportunities.map((opp, index) => (
                      <div key={opp.game_id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <div className="text-lg font-bold text-green-600">#{index + 1}</div>
                            <div>
                              <div className="font-semibold">{opp.game}</div>
                              <div className="text-sm text-gray-600">{opp.bowl_name}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xl font-bold text-green-600">
                              ${(opp.value_score * 1000).toFixed(0)}
                            </div>
                            <div className="text-sm text-gray-600">Expected Value</div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
                          <div className="text-center p-2 bg-blue-50 rounded">
                            <div className="text-sm text-gray-600">Our Prediction</div>
                            <div className="font-bold text-blue-600">{opp.prediction}</div>
                            <div className="text-sm">{opp.predicted_margin > 0 ? '+' : ''}{opp.predicted_margin.toFixed(1)}</div>
                          </div>
                          <div className="text-center p-2 bg-gray-50 rounded">
                            <div className="text-sm text-gray-600">Vegas Spread</div>
                            <div className="font-bold">{opp.spread > 0 ? `${opp.away_team}` : `${opp.home_team}`}</div>
                            <div className="text-sm">{Math.abs(opp.spread).toFixed(1)}</div>
                          </div>
                          <div className="text-center p-2 bg-green-50 rounded">
                            <div className="text-sm text-gray-600">Edge</div>
                            <div className="font-bold text-green-600">
                              {Math.abs(opp.predicted_margin - opp.spread).toFixed(1)}
                            </div>
                            <div className="text-sm">point advantage</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Value Distribution Chart */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Value Distribution</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={games.map(g => ({
                      name: g.bowl_name?.split(' ')[0] || `Game ${g.id}`,
                      value: (g.value_rating || 0) * 100,
                    })).slice(0, 15)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill={COLORS.success} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Model Performance Comparison */}
            <Card>
              <CardHeader>
                <CardTitle>Model Performance</CardTitle>
                <CardDescription>
                  Compare accuracy across different prediction models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={modelPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="model" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="accuracy" fill={COLORS.primary} name="Accuracy %" />
                    <Bar dataKey="confidence_score" fill={COLORS.success} name="Confidence" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Model Metrics Table */}
            <Card>
              <CardHeader>
                <CardTitle>Detailed Model Metrics</CardTitle>
                <CardDescription>
                  Performance statistics for each prediction model
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {modelPerformance.map((model) => (
                    <div key={model.model} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-semibold">{model.model}</div>
                        <Badge variant={model.accuracy > 65 ? "default" : "secondary"}>
                          {model.accuracy.toFixed(1)}% Accurate
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Avg Error:</span> {model.avg_error.toFixed(1)} points
                        </div>
                        <div>
                          <span className="text-gray-600">Confidence:</span> {(model.confidence_score * 100).toFixed(0)}%
                        </div>
                        <div>
                          <span className="text-gray-600">Value Games:</span> {model.value_games_found}
                        </div>
                      </div>
                      <Progress value={model.confidence_score * 100} className="mt-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="breakdown" className="space-y-6">
          {selectedGame ? (
            <div className="space-y-6">
              {/* Game Header */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-2xl">{selectedGame.bowl_name}</CardTitle>
                      <CardDescription className="text-lg">
                        {selectedGame.away_team} vs {selectedGame.home_team}
                      </CardDescription>
                      <div className="text-sm text-gray-600">
                        {new Date(selectedGame.date).toLocaleDateString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </div>
                    </div>
                    <Button variant="outline" onClick={() => setSelectedGame(null)}>
                      Back to Games
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedGame.predicted_margin > 0 ? selectedGame.home_team : selectedGame.away_team}
                      </div>
                      <p className="text-sm text-blue-600">Predicted Winner</p>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {selectedGame.predicted_margin > 0 ? '+' : ''}{selectedGame.predicted_margin.toFixed(1)}
                      </div>
                      <p className="text-sm text-green-600">Predicted Margin</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {(selectedGame.confidence * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-purple-600">Confidence</p>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {selectedGame.value_rating ? `${(selectedGame.value_rating * 100).toFixed(0)}%` : 'N/A'}
                      </div>
                      <p className="text-sm text-orange-600">Value Rating</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Team Comparison Radar */}
              <Card>
                <CardHeader>
                  <CardTitle>Team Comparison Analysis</CardTitle>
                  <CardDescription>
                    Head-to-head statistical comparison
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={prepareRadarData(selectedGame)}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="stat" />
                      <PolarRadiusAxis />
                      <Radar
                        name={selectedGame.home_team}
                        dataKey="home"
                        stroke={COLORS.primary}
                        fill={COLORS.primary}
                        fillOpacity={0.6}
                      />
                      <Radar
                        name={selectedGame.away_team}
                        dataKey="away"
                        stroke={COLORS.danger}
                        fill={COLORS.danger}
                        fillOpacity={0.6}
                      />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Prediction Comparison */}
              <Card>
                <CardHeader>
                  <CardTitle>Model Predictions Comparison</CardTitle>
                  <CardDescription>
                    How different models predict this game
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center p-4 border rounded-lg">
                        <div className="font-semibold mb-2">ML Ensemble</div>
                        <div className="text-2xl font-bold">
                          {selectedGame.predicted_margin > 0 ? '+' : ''}{selectedGame.predicted_margin.toFixed(1)}
                        </div>
                        <div className="text-sm text-gray-600">
                          {selectedGame.predicted_margin > 0 ? selectedGame.home_team : selectedGame.away_team}
                        </div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="font-semibold mb-2">Massey Ratings</div>
                        <div className="text-2xl font-bold">
                          {selectedGame.massey_prediction ?
                            (selectedGame.massey_prediction > 0 ? '+' : '') + selectedGame.massey_prediction.toFixed(1) :
                            'N/A'
                          }
                        </div>
                        <div className="text-sm text-gray-600">
                          {selectedGame.massey_prediction ?
                            (selectedGame.massey_prediction > 0 ? selectedGame.home_team : selectedGame.away_team) :
                            'N/A'
                          }
                        </div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="font-semibold mb-2">Simple Model</div>
                        <div className="text-2xl font-bold">
                          {selectedGame.simple_prediction ?
                            (selectedGame.simple_prediction > 0 ? '+' : '') + selectedGame.simple_prediction.toFixed(1) :
                            'N/A'
                          }
                        </div>
                        <div className="text-sm text-gray-600">
                          {selectedGame.simple_prediction ?
                            (selectedGame.simple_prediction > 0 ? selectedGame.home_team : selectedGame.away_team) :
                            'N/A'
                          }
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Select a Game for Detailed Breakdown</CardTitle>
                <CardDescription>
                  Choose from the bowl games below to see detailed analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {games.map((game) => (
                    <div
                      key={game.id}
                      className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => setSelectedGame(game)}
                    >
                      <div className="font-semibold text-sm mb-2">{game.bowl_name}</div>
                      <div className="text-sm text-gray-600 mb-1">
                        {game.away_team} vs {game.home_team}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(game.date).toLocaleDateString()}
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <Badge variant="outline">
                          {(game.confidence * 100).toFixed(0)}% confident
                        </Badge>
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UnifiedPostseasonDashboard;