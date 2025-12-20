/**
 * Bowl Analytics Dashboard
 *
 * Comprehensive dashboard for detailed bowl game analysis including:
 * - Individual game breakdowns with team comparisons
 * - Multiple prediction method comparisons (ML, Massey, Simple)
 * - Historical performance trends
 * - Tournament bracket visualization
 * - Interactive features and detailed statistics
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Search, Filter, Download, Trophy, TrendingUp, Users, Calendar } from 'lucide-react';

// Recharts components for data visualization
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
} from 'recharts';

import BowlGameBreakdown from './BowlGameBreakdown';
import BowlPredictionsView from './BowlPredictionsView';
import BowlMatchupComparison from './BowlMatchupComparison';
import BowlTournamentView from './BowlTournamentView';
import BowlHistoryView from './BowlHistoryView';

// Types for bowl game data
interface BowlGame {
  id: number;
  date: string;
  home_team: string;
  away_team: string;
  home_win_prob: number;
  away_win_prob: number;
  predicted_margin: number;
  confidence: number;
  massey_prediction?: number;
  simple_prediction?: number;
  conference?: string;
  stadium?: string;
  location?: string;
}

interface TeamStats {
  team: string;
  offense_rating: number;
  defense_rating: number;
  special_teams: number;
  strength_of_schedule: number;
  recent_form: number;
  injuries_impact: number;
}

interface PredictionComparison {
  game_id: number;
  ml_prediction: number;
  massey_prediction: number;
  simple_prediction: number;
  consensus_pick: string;
  value_rating: number;
}

const BowlAnalyticsDashboard: React.FC = () => {
  const [bowlGames, setBowlGames] = useState<BowlGame[]>([]);
  const [teamStats, setTeamStats] = useState<Record<string, TeamStats>>({});
  const [predictions, setPredictions] = useState<PredictionComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConference, setSelectedConference] = useState('all');
  const [selectedGame, setSelectedGame] = useState<BowlGame | null>(null);

  // Mock data loading - replace with actual API calls
  useEffect(() => {
    loadBowlGameData();
  }, []);

  const loadBowlGameData = async () => {
    try {
      setLoading(true);

      // Load bowl games data
      const gamesResponse = await fetch('/api/bowl-games');
      const gamesData = await gamesResponse.json();
      setBowlGames(gamesData);

      // Load team statistics
      const statsResponse = await fetch('/api/team-stats');
      const statsData = await statsResponse.json();
      setTeamStats(statsData);

      // Load prediction comparisons
      const predictionsResponse = await fetch('/api/predictions-comparison');
      const predictionsData = await predictionsResponse.json();
      setPredictions(predictionsData);

    } catch (error) {
      console.error('Error loading bowl game data:', error);
      // Use mock data for development
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const loadMockData = () => {
    // Mock bowl games data
    const mockGames: BowlGame[] = [
      {
        id: 401778123,
        date: '2025-12-13T17:00:00Z',
        home_team: 'Washington',
        away_team: 'Boise State',
        home_win_prob: 0.654,
        away_win_prob: 0.346,
        predicted_margin: 7.2,
        confidence: 0.78,
        massey_prediction: 6.5,
        simple_prediction: 8.1,
        conference: 'Pac-12 vs MWC',
        stadium: 'Alamodome',
        location: 'San Antonio, TX'
      },
      {
        id: 401778302,
        date: '2025-12-15T20:00:00Z',
        home_team: 'Georgia',
        away_team: 'Florida State',
        home_win_prob: 0.712,
        away_win_prob: 0.288,
        predicted_margin: 9.8,
        confidence: 0.82,
        massey_prediction: 11.2,
        simple_prediction: 8.5,
        conference: 'SEC vs ACC',
        stadium: 'Mercedes-Benz Stadium',
        location: 'Atlanta, GA'
      },
      // Add more mock games as needed
    ];

    // Mock team statistics
    const mockStats: Record<string, TeamStats> = {
      'Washington': {
        team: 'Washington',
        offense_rating: 88.5,
        defense_rating: 76.2,
        special_teams: 82.1,
        strength_of_schedule: 79.3,
        recent_form: 85.7,
        injuries_impact: 5.2
      },
      'Boise State': {
        team: 'Boise State',
        offense_rating: 82.3,
        defense_rating: 79.8,
        special_teams: 78.5,
        strength_of_schedule: 72.1,
        recent_form: 88.2,
        injuries_impact: 3.1
      },
      // Add more team stats as needed
    };

    // Mock prediction comparisons
    const mockPredictions: PredictionComparison[] = [
      {
        game_id: 401778123,
        ml_prediction: 7.2,
        massey_prediction: 6.5,
        simple_prediction: 8.1,
        consensus_pick: 'Washington',
        value_rating: 0.73
      },
      {
        game_id: 401778302,
        ml_prediction: 9.8,
        massey_prediction: 11.2,
        simple_prediction: 8.5,
        consensus_pick: 'Georgia',
        value_rating: 0.81
      },
      // Add more predictions as needed
    ];

    setBowlGames(mockGames);
    setTeamStats(mockStats);
    setPredictions(mockPredictions);
  };

  // Filter bowl games based on search and conference
  const filteredGames = useMemo(() => {
    return bowlGames.filter(game => {
      const matchesSearch = searchTerm === '' ||
        game.home_team.toLowerCase().includes(searchTerm.toLowerCase()) ||
        game.away_team.toLowerCase().includes(searchTerm.toLowerCase()) ||
        game.stadium?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesConference = selectedConference === 'all' ||
        game.conference?.toLowerCase().includes(selectedConference.toLowerCase());

      return matchesSearch && matchesConference;
    });
  }, [bowlGames, searchTerm, selectedConference]);

  // Analytics calculations
  const analyticsData = useMemo(() => {
    const totalGames = bowlGames.length;
    const avgConfidence = bowlGames.reduce((sum, game) => sum + game.confidence, 0) / totalGames || 0;
    const highConfidenceGames = bowlGames.filter(game => game.confidence > 0.8).length;
    const avgPredictedMargin = bowlGames.reduce((sum, game) => sum + Math.abs(game.predicted_margin), 0) / totalGames || 0;

    return {
      totalGames,
      avgConfidence: avgConfidence * 100,
      highConfidenceGames,
      highConfidencePercentage: (highConfidenceGames / totalGames) * 100,
      avgPredictedMargin,
    };
  }, [bowlGames]);

  // Conference distribution for pie chart
  const conferenceDistribution = useMemo(() => {
    const distribution: Record<string, number> = {};
    bowlGames.forEach(game => {
      if (game.conference) {
        distribution[game.confference] = (distribution[game.conference] || 0) + 1;
      }
    });

    return Object.entries(distribution).map(([conference, count]) => ({
      name: conference,
      value: count,
      percentage: (count / bowlGames.length) * 100
    }));
  }, [bowlGames]);

  // Prediction accuracy trend data
  const predictionTrend = useMemo(() => {
    // This would normally come from historical data
    return [
      { week: 'Week 1', accuracy: 72.5 },
      { week: 'Week 2', accuracy: 75.2 },
      { week: 'Week 3', accuracy: 71.8 },
      { week: 'Week 4', accuracy: 78.1 },
      { week: 'Week 5', accuracy: 76.4 },
      { week: 'Bowl Season', accuracy: analyticsData.avgConfidence },
    ];
  }, [analyticsData.avgConfidence]);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">🏈 Bowl Game Analytics</h1>
          <p className="text-muted-foreground">
            Comprehensive analysis and predictions for all {analyticsData.totalGames} bowl games
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Data
          </Button>
          <Button size="sm">
            <Trophy className="h-4 w-4 mr-2" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col space-y-4 md:flex-row md:items-center md:space-y-0 md:space-x-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <input
                type="text"
                placeholder="Search teams, stadiums, locations..."
                className="pl-10 pr-4 py-2 w-full border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <select
              className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedConference}
              onChange={(e) => setSelectedConference(e.target.value)}
            >
              <option value="all">All Conferences</option>
              <option value="sec">SEC</option>
              <option value="acc">ACC</option>
              <option value="big-ten">Big Ten</option>
              <option value="pac-12">Pac-12</option>
              <option value="big-12">Big 12</option>
              <option value="mwc">Mountain West</option>
              <option value="aac">AAC</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Analytics Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Games</CardTitle>
            <Trophy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.totalGames}</div>
            <p className="text-xs text-muted-foreground">
              Bowl games this season
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.avgConfidence.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Across all prediction methods
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Confidence</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.highConfidencePercentage.toFixed(0)}%</div>
            <p className="text-xs text-muted-foreground">
              {analyticsData.highConfidenceGames} of {analyticsData.totalGames} games
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Margin</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.avgPredictedMargin.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">
              Points predicted margin
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="games" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="games">Games</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="matchups">Matchups</TabsTrigger>
          <TabsTrigger value="tournament">Bracket</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="games" className="space-y-4">
          <BowlGameBreakdown
            games={filteredGames}
            teamStats={teamStats}
            onGameSelect={setSelectedGame}
            selectedGame={selectedGame}
          />
        </TabsContent>

        <TabsContent value="predictions" className="space-y-4">
          <BowlPredictionsView
            predictions={predictions}
            games={filteredGames}
          />
        </TabsContent>

        <TabsContent value="matchups" className="space-y-4">
          <BowlMatchupComparison
            games={filteredGames}
            teamStats={teamStats}
          />
        </TabsContent>

        <TabsContent value="tournament" className="space-y-4">
          <BowlTournamentView
            games={filteredGames}
            predictions={predictions}
          />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <BowlHistoryView
            games={filteredGames}
          />
        </TabsContent>
      </Tabs>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conference Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Conference Distribution</CardTitle>
            <CardDescription>
              Breakdown of bowl games by conference matchups
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={conferenceDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({name, percentage}) => `${name}: ${percentage.toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {conferenceDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Prediction Accuracy Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Prediction Accuracy Trend</CardTitle>
            <CardDescription>
              Model performance throughout the season
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={predictionTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="Accuracy %"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BowlAnalyticsDashboard;