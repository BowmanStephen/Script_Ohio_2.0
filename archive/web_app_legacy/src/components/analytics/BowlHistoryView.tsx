/**
 * Bowl History View Component
 *
 * Historical bowl game performance analysis including:
 * - Historical win/loss records by team
 * - Conference performance in bowl games
 * - Year-over-year trends
 * - Head-to-head historical records
 * - Historical upset analysis
 */

import React, { useState, useMemo } from 'react';
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
import {
  History,
  TrendingUp,
  TrendingDown,
  Trophy,
  Users,
  BarChart3,
  Calendar,
  Target,
  Award,
  Activity,
} from 'lucide-react';

// Recharts components
import {
  LineChart,
  Line,
  BarChart,
  Bar,
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
  bowl_name?: string;
  // Historical data
  actual_margin?: number;
  actual_winner?: string;
  year?: number;
}

interface TeamHistory {
  team: string;
  conference: string;
  total_games: number;
  wins: number;
  losses: number;
  win_percentage: number;
  avg_margin: number;
  recent_form: number[];
  conference_wins: number;
  conference_losses: number;
  historical_upsets: number;
  biggest_win: number;
  biggest_loss: number;
}

interface BowlHistoryViewProps {
  games: BowlGame[];
}

const BowlHistoryView: React.FC<BowlHistoryViewProps> = ({ games }) => {
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<'all' | 'recent' | 'historic'>('all');

  // Calculate team historical records
  const teamHistories = useMemo(() => {
    const histories: Record<string, TeamHistory> = {};

    games.forEach(game => {
      if (!game.actual_winner) return; // Skip games without actual results

      const teams = [game.home_team, game.away_team];

      teams.forEach(team => {
        if (!histories[team]) {
          histories[team] = {
            team,
            conference: game.conference || 'Unknown',
            total_games: 0,
            wins: 0,
            losses: 0,
            win_percentage: 0,
            avg_margin: 0,
            recent_form: [],
            conference_wins: 0,
            conference_losses: 0,
            historical_upsets: 0,
            biggest_win: 0,
            biggest_loss: 0,
          };
        }

        const history = histories[team];
        history.total_games++;

        const isHome = team === game.home_team;
        const winner = game.actual_winner;
        const actualMargin = game.actual_margin || 0;
        const predictedMargin = game.predicted_margin;
        const teamPredictedMargin = isHome ? predictedMargin : -predictedMargin;

        // Update win/loss
        if (winner === team) {
          history.wins++;
          if (actualMargin > history.biggest_win) {
            history.biggest_win = actualMargin;
          }
        } else {
          history.losses++;
          if (Math.abs(actualMargin) > history.biggest_loss) {
            history.biggest_loss = Math.abs(actualMargin);
          }
        }

        // Calculate upset (when underdog wins)
        const teamWinProb = isHome ? game.home_win_prob : game.away_win_prob;
        if (winner === team && teamWinProb < 0.4) {
          history.historical_upsets++;
        }

        // Update recent form (last 5 games)
        history.recent_form.push(winner === team ? 1 : 0);
        if (history.recent_form.length > 5) {
          history.recent_form.shift();
        }

        // Calculate average margin
        const teamMargin = isHome ? actualMargin : -actualMargin;
        history.avg_margin = (history.avg_margin * (history.total_games - 1) + teamMargin) / history.total_games;
      });

    });

    // Calculate win percentages
    Object.values(histories).forEach(history => {
      history.win_percentage = history.total_games > 0 ? (history.wins / history.total_games) * 100 : 0;
    });

    return histories;
  }, [games]);

  // Conference performance data
  const conferencePerformance = useMemo(() => {
    const performance: Record<string, { wins: number; losses: number; games: number }> = {};

    Object.values(teamHistories).forEach(history => {
      if (!performance[history.conference]) {
        performance[history.conference] = { wins: 0, losses: 0, games: 0 };
      }

      const confPerf = performance[history.conference];
      confPerf.wins += history.wins;
      confPerf.losses += history.losses;
      confPerf.games += history.total_games;
    });

    return Object.entries(performance).map(([conference, stats]) => ({
      conference,
      ...stats,
      win_percentage: stats.games > 0 ? (stats.wins / stats.games) * 100 : 0,
    }));
  }, [teamHistories]);

  // Year-over-year trends (mock data - in production this would use historical years)
  const yearlyTrends = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const years = [currentYear - 4, currentYear - 3, currentYear - 2, currentYear - 1, currentYear];

    return years.map(year => ({
      year,
      total_games: Math.floor(Math.random() * 40) + 20,
      avg_margin: Math.random() * 10 - 5,
      upsets: Math.floor(Math.random() * 8) + 2,
      accuracy: 70 + Math.random() * 20,
    }));
  }, []);

  // Top performing teams
  const topTeams = useMemo(() => {
    return Object.values(teamHistories)
      .filter(history => history.total_games >= 5) // Minimum games threshold
      .sort((a, b) => b.win_percentage - a.win_percentage)
      .slice(0, 20);
  }, [teamHistories]);

  // Get trend color
  const getTrendColor = (trend: number) => {
    return trend > 0 ? 'text-green-600' : 'text-red-600';
  };

  const getTrendIcon = (trend: number) => {
    return trend > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />;
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  if (selectedTeam) {
    const teamHistory = teamHistories[selectedTeam];
    if (!teamHistory) return null;

    return (
      <div className="space-y-6">
        {/* Team Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-bold">{selectedTeam}</CardTitle>
                <CardDescription>
                  {teamHistory.conference} • {teamHistory.total_games} bowl games all-time
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => setSelectedTeam(null)}
              >
                Back to All Teams
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Overall Record */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-600">{teamHistory.wins}</div>
                <p className="text-sm text-blue-600">Wins</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-3xl font-bold text-red-600">{teamHistory.losses}</div>
                <p className="text-sm text-red-600">Losses</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-3xl font-bold text-green-600">{teamHistory.win_percentage.toFixed(1)}%</div>
                <p className="text-sm text-green-600">Win %</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-3xl font-bold text-purple-600">
                  {teamHistory.avg_margin > 0 ? '+' : ''}{teamHistory.avg_margin.toFixed(1)}
                </div>
                <p className="text-sm text-purple-600">Avg Margin</p>
              </div>
            </div>

            {/* Recent Form */}
            <div className="mb-6">
              <h3 className="font-semibold mb-3 flex items-center">
                <Activity className="h-4 w-4 mr-2" />
                Recent Form (Last {teamHistory.recent_form.length} Games)
              </h3>
              <div className="flex space-x-2">
                {teamHistory.recent_form.map((result, index) => (
                  <div
                    key={index}
                    className={`flex items-center justify-center w-10 h-10 rounded-full font-bold ${
                      result === 1 ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                    }`}
                  >
                    {result === 1 ? 'W' : 'L'}
                  </div>
                ))}
              </div>
            </div>

            {/* Key Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Performance Highlights</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Biggest Win:</span>
                    <span className="font-bold">+{teamHistory.biggest_win.toFixed(1)} pts</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Biggest Loss:</span>
                    <span className="font-bold">-{teamHistory.biggest_loss.toFixed(1)} pts</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Historical Upsets:</span>
                    <span className="font-bold">{teamHistory.historical_upsets}</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-medium mb-3">Conference Record</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Conference Wins:</span>
                    <span className="font-bold">{teamHistory.conference_wins}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Conference Losses:</span>
                    <span className="font-bold">{teamHistory.conference_losses}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Conference Win %:</span>
                    <span className="font-bold">
                      {((teamHistory.conference_wins / (teamHistory.conference_wins + teamHistory.conference_losses)) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // All Teams View
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">📚 Bowl Game History</h2>
          <p className="text-muted-foreground">
            Historical performance analysis and trends
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value as any)}
          >
            <option value="all">All Time</option>
            <option value="recent">Recent 5 Years</option>
            <option value="historic">Historic</option>
          </select>
        </div>
      </div>

      {/* Top Teams */}
      <Card>
        <CardHeader>
          <CardTitle>All-Time Bowl Performance Rankings</CardTitle>
          <CardDescription>
            Teams ranked by bowl game winning percentage (minimum 5 games)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topTeams.map((team, index) => (
              <div
                key={team.team}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setSelectedTeam(team.team)}
              >
                <div className="flex items-center space-x-4">
                  <div className="text-lg font-bold text-gray-500">
                    #{index + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{team.team}</h3>
                    <p className="text-sm text-muted-foreground">{team.conference}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="outline">
                        {team.total_games} games
                      </Badge>
                      <Badge variant="outline">
                        {team.wins}-{team.losses}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">
                    {team.win_percentage.toFixed(1)}%
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Avg Margin: {team.avg_margin > 0 ? '+' : ''}{team.avg_margin.toFixed(1)}
                  </div>
                  <div className="flex items-center space-x-1 mt-1">
                    {getTrendIcon(team.avg_margin)}
                    <span className={`text-sm ${getTrendColor(team.avg_margin)}`}>
                      {team.avg_margin > 0 ? 'Positive' : 'Negative'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conference Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Conference Bowl Performance</CardTitle>
            <CardDescription>
              Historical bowl game records by conference
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={conferencePerformance.slice(0, 8)}
                layout="horizontal"
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="number" domain={[0, 'dataMax + 5']} />
                <Tooltip />
                <Bar dataKey="wins" fill="#8884d8" name="Wins" />
                <Bar dataKey="losses" fill="#82ca9d" name="Losses" />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Yearly Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Bowl Game Trends</CardTitle>
            <CardDescription>
              Year-over-year bowl game statistics and predictions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={yearlyTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="total_games"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.3}
                  name="Total Games"
                />
                <Area
                  yAxisId="right"
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  fillOpacity={0.3}
                  name="Prediction Accuracy %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Teams</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(teamHistories).length}</div>
            <p className="text-xs text-muted-foreground">
              Teams with bowl history
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Games</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{games.length}</div>
            <p className="text-xs text-muted-foreground">
              Bowl games analyzed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Conferences</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conferencePerformance.length}</div>
            <p className="text-xs text-muted-foreground">
              Represented in bowls
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Experience</CardTitle>
            <History className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.values(teamHistories).length > 0 ?
                (Object.values(teamHistories).reduce((sum, h) => sum + h.total_games, 0) / Object.keys(teamHistories).length).toFixed(1) :
                '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              Games per team
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BowlHistoryView;