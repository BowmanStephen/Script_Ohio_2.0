/**
 * Bowl Game Breakdown Component
 *
 * Provides detailed analysis for individual bowl games including:
 * - Team statistical comparisons
 * - Head-to-head matchups
 * - Prediction confidence analysis
 * - Historical performance context
 * - Interactive team radar charts
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
  Star,
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  Shield,
  Zap,
  Award,
  Calendar,
  MapPin,
  BarChart3,
} from 'lucide-react';

// Recharts components for data visualization
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  Area,
  AreaChart,
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

interface BowlGameBreakdownProps {
  games: BowlGame[];
  teamStats: Record<string, TeamStats>;
  onGameSelect: (game: BowlGame | null) => void;
  selectedGame: BowlGame | null;
}

const BowlGameBreakdown: React.FC<BowlGameBreakdownProps> = ({
  games,
  teamStats,
  onGameSelect,
  selectedGame,
}) => {
  const [detailedView, setDetailedView] = useState(false);

  // Get team stats for selected game
  const getTeamStats = (teamName: string): TeamStats => {
    return teamStats[teamName] || {
      team: teamName,
      offense_rating: 75,
      defense_rating: 75,
      special_teams: 75,
      strength_of_schedule: 75,
      recent_form: 75,
      injuries_impact: 5,
    };
  };

  // Prepare radar chart data
  const prepareRadarData = (homeTeam: string, awayTeam: string) => {
    const homeStats = getTeamStats(homeTeam);
    const awayStats = getTeamStats(awayTeam);

    return [
      {
        stat: 'Offense',
        [homeTeam]: homeStats.offense_rating,
        [awayTeam]: awayStats.offense_rating,
        fullMark: 100,
      },
      {
        stat: 'Defense',
        [homeTeam]: homeStats.defense_rating,
        [awayTeam]: awayStats.defense_rating,
        fullMark: 100,
      },
      {
        stat: 'Special Teams',
        [homeTeam]: homeStats.special_teams,
        [awayTeam]: awayStats.special_teams,
        fullMark: 100,
      },
      {
        stat: 'SOS',
        [homeTeam]: homeStats.strength_of_schedule,
        [awayTeam]: awayStats.strength_of_schedule,
        fullMark: 100,
      },
      {
        stat: 'Recent Form',
        [homeTeam]: homeStats.recent_form,
        [awayTeam]: awayStats.recent_form,
        fullMark: 100,
      },
      {
        stat: 'Health',
        [homeTeam]: 100 - homeStats.injuries_impact * 10,
        [awayTeam]: 100 - awayStats.injuries_impact * 10,
        fullMark: 100,
      },
    ];
  };

  // Prepare performance trend data
  const prepareTrendData = (teamName: string) => {
    // Mock trend data - in production this would come from historical data
    return [
      { week: 'Week 10', performance: 72 + Math.random() * 20 },
      { week: 'Week 11', performance: 75 + Math.random() * 20 },
      { week: 'Week 12', performance: 78 + Math.random() * 20 },
      { week: 'Week 13', performance: 80 + Math.random() * 15 },
      { week: 'Week 14', performance: 82 + Math.random() * 15 },
      { week: 'Current', performance: getTeamStats(teamName).recent_form },
    ];
  };

  // Calculate matchup advantages
  const calculateAdvantages = (homeTeam: string, awayTeam: string) => {
    const homeStats = getTeamStats(homeTeam);
    const awayStats = getTeamStats(awayTeam);

    const advantages = [
      {
        category: 'Offense',
        winner: homeStats.offense_rating > awayStats.offense_rating ? homeTeam : awayTeam,
        margin: Math.abs(homeStats.offense_rating - awayStats.offense_rating),
        icon: <Zap className="h-4 w-4" />,
      },
      {
        category: 'Defense',
        winner: homeStats.defense_rating > awayStats.defense_rating ? homeTeam : awayTeam,
        margin: Math.abs(homeStats.defense_rating - awayStats.defense_rating),
        icon: <Shield className="h-4 w-4" />,
      },
      {
        category: 'Schedule',
        winner: homeStats.strength_of_schedule > awayStats.strength_of_schedule ? homeTeam : awayTeam,
        margin: Math.abs(homeStats.strength_of_schedule - awayStats.strength_of_schedule),
        icon: <BarChart3 className="h-4 w-4" />,
      },
      {
        category: 'Form',
        winner: homeStats.recent_form > awayStats.recent_form ? homeTeam : awayTeam,
        margin: Math.abs(homeStats.recent_form - awayStats.recent_form),
        icon: <TrendingUp className="h-4 w-4" />,
      },
    ];

    return advantages.sort((a, b) => b.margin - a.margin);
  };

  // Get confidence level badge
  const getConfidenceBadge = (confidence: number) => {
    const level = confidence > 0.8 ? 'High' : confidence > 0.6 ? 'Medium' : 'Low';
    const variant = confidence > 0.8 ? 'default' : confidence > 0.6 ? 'secondary' : 'outline';

    return (
      <Badge variant={variant} className="ml-2">
        {level} Confidence
      </Badge>
    );
  };

  const formatGameDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  if (selectedGame) {
    const homeStats = getTeamStats(selectedGame.home_team);
    const awayStats = getTeamStats(selectedGame.away_team);
    const radarData = prepareRadarData(selectedGame.home_team, selectedGame.away_team);
    const homeTrendData = prepareTrendData(selectedGame.home_team);
    const awayTrendData = prepareTrendData(selectedGame.away_team);
    const advantages = calculateAdvantages(selectedGame.home_team, selectedGame.away_team);

    return (
      <div className="space-y-6">
        {/* Game Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-bold">
                  {selectedGame.away_team} vs {selectedGame.home_team}
                </CardTitle>
                <CardDescription className="flex items-center space-x-4 mt-2">
                  <span className="flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    {formatGameDate(selectedGame.date)}
                  </span>
                  <span className="flex items-center">
                    <MapPin className="h-4 w-4 mr-1" />
                    {selectedGame.stadium}, {selectedGame.location}
                  </span>
                  <span>{selectedGame.conference}</span>
                  {getConfidenceBadge(selectedGame.confidence)}
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => onGameSelect(null)}
              >
                Back to All Games
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Prediction Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="text-center">
                <h3 className="font-semibold mb-2">{selectedGame.away_team}</h3>
                <div className="text-2xl font-bold text-blue-600">
                  {(selectedGame.away_win_prob * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-muted-foreground">Win Probability</p>
              </div>
              <div className="text-center">
                <h3 className="font-semibold mb-2">Predicted Margin</h3>
                <div className="text-3xl font-bold text-green-600">
                  {selectedGame.predicted_margin > 0 ? `${selectedGame.home_team}` : `${selectedGame.away_team}`}
                </div>
                <div className="text-xl font-semibold">
                  {Math.abs(selectedGame.predicted_margin).toFixed(1)} pts
                </div>
              </div>
              <div className="text-center">
                <h3 className="font-semibold mb-2">{selectedGame.home_team}</h3>
                <div className="text-2xl font-bold text-red-600">
                  {(selectedGame.home_win_prob * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-muted-foreground">Win Probability</p>
              </div>
            </div>

            {/* Prediction Methods Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-center">
                    <div className="text-sm font-medium text-muted-foreground">ML Model</div>
                    <div className="text-lg font-bold">
                      {selectedGame.predicted_margin > 0 ? `${selectedGame.home_team}` : `${selectedGame.away_team}`}
                    </div>
                    <div className="text-xl">
                      {Math.abs(selectedGame.predicted_margin).toFixed(1)}
                    </div>
                  </div>
                </CardContent>
              </Card>
              {selectedGame.massey_prediction && (
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-center">
                      <div className="text-sm font-medium text-muted-foreground">Massey</div>
                      <div className="text-lg font-bold">
                        {selectedGame.massey_prediction > 0 ? `${selectedGame.home_team}` : `${selectedGame.away_team}`}
                      </div>
                      <div className="text-xl">
                        {Math.abs(selectedGame.massey_prediction).toFixed(1)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              {selectedGame.simple_prediction && (
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-center">
                      <div className="text-sm font-medium text-muted-foreground">Simple</div>
                      <div className="text-lg font-bold">
                        {selectedGame.simple_prediction > 0 ? `${selectedGame.home_team}` : `${selectedGame.away_team}`}
                      </div>
                      <div className="text-xl">
                        {Math.abs(selectedGame.simple_prediction).toFixed(1)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Detailed Analysis Tabs */}
        <Tabs defaultValue="matchup" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="matchup">Matchup Analysis</TabsTrigger>
            <TabsTrigger value="trends">Performance Trends</TabsTrigger>
            <TabsTrigger value="stats">Statistical Breakdown</TabsTrigger>
            <TabsTrigger value="advantages">Key Advantages</TabsTrigger>
          </TabsList>

          <TabsContent value="matchup" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Team Comparison Radar */}
              <Card>
                <CardHeader>
                  <CardTitle>Team Comparison</CardTitle>
                  <CardDescription>
                    Head-to-head statistical comparison
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="stat" />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} />
                      <Radar
                        name={selectedGame.home_team}
                        dataKey={selectedGame.home_team}
                        stroke="#ef4444"
                        fill="#ef4444"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                      <Radar
                        name={selectedGame.away_team}
                        dataKey={selectedGame.away_team}
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                      <Legend />
                      <Tooltip />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Key Matchup Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>Key Matchup Statistics</CardTitle>
                  <CardDescription>
                    Critical performance indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                      <span className="font-medium">{selectedGame.home_team}</span>
                      <div className="text-right">
                        <div className="text-sm">Offense Rating</div>
                        <div className="font-bold">{homeStats.offense_rating.toFixed(1)}</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                      <span className="font-medium">{selectedGame.away_team}</span>
                      <div className="text-right">
                        <div className="text-sm">Offense Rating</div>
                        <div className="font-bold">{awayStats.offense_rating.toFixed(1)}</div>
                      </div>
                    </div>

                    <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                      <span className="font-medium">{selectedGame.home_team}</span>
                      <div className="text-right">
                        <div className="text-sm">Defense Rating</div>
                        <div className="font-bold">{homeStats.defense_rating.toFixed(1)}</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                      <span className="font-medium">{selectedGame.away_team}</span>
                      <div className="text-right">
                        <div className="text-sm">Defense Rating</div>
                        <div className="font-bold">{awayStats.defense_rating.toFixed(1)}</div>
                      </div>
                    </div>

                    <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                      <span className="font-medium">{selectedGame.home_team}</span>
                      <div className="text-right">
                        <div className="text-sm">Recent Form</div>
                        <div className="font-bold">{homeStats.recent_form.toFixed(1)}</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                      <span className="font-medium">{selectedGame.away_team}</span>
                      <div className="text-right">
                        <div className="text-sm">Recent Form</div>
                        <div className="font-bold">{awayStats.recent_form.toFixed(1)}</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Home Team Trend */}
              <Card>
                <CardHeader>
                  <CardTitle>{selectedGame.home_team} Performance Trend</CardTitle>
                  <CardDescription>
                    Season performance trajectory
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={homeTrendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" />
                      <YAxis domain={[60, 100]} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="performance"
                        stroke="#ef4444"
                        fill="#ef4444"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Away Team Trend */}
              <Card>
                <CardHeader>
                  <CardTitle>{selectedGame.away_team} Performance Trend</CardTitle>
                  <CardDescription>
                    Season performance trajectory
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={awayTrendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" />
                      <YAxis domain={[60, 100]} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="performance"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.3}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="stats" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Detailed Stats Cards */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{selectedGame.home_team}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>Offense Rating</span>
                    <span className="font-bold">{homeStats.offense_rating.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Defense Rating</span>
                    <span className="font-bold">{homeStats.defense_rating.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Special Teams</span>
                    <span className="font-bold">{homeStats.special_teams.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Strength of Schedule</span>
                    <span className="font-bold">{homeStats.strength_of_schedule.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Form</span>
                    <span className="font-bold">{homeStats.recent_form.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Injury Impact</span>
                    <span className="font-bold">{homeStats.injuries_impact.toFixed(1)}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{selectedGame.away_team}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>Offense Rating</span>
                    <span className="font-bold">{awayStats.offense_rating.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Defense Rating</span>
                    <span className="font-bold">{awayStats.defense_rating.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Special Teams</span>
                    <span className="font-bold">{awayStats.special_teams.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Strength of Schedule</span>
                    <span className="font-bold">{awayStats.strength_of_schedule.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Recent Form</span>
                    <span className="font-bold">{awayStats.recent_form.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Injury Impact</span>
                    <span className="font-bold">{awayStats.injuries_impact.toFixed(1)}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Prediction Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Prediction Analysis</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {selectedGame.predicted_margin > 0 ? `${selectedGame.home_team}` : `${selectedGame.away_team}`}
                    </div>
                    <div className="text-xl font-semibold">
                      {Math.abs(selectedGame.predicted_margin).toFixed(1)} points
                    </div>
                    <div className="text-sm text-muted-foreground mt-2">
                      {getConfidenceBadge(selectedGame.confidence)}
                    </div>
                  </div>
                  <div className="pt-4 border-t">
                    <div className="text-sm font-medium mb-2">Win Probability:</div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>{selectedGame.home_team}:</span>
                        <span className="font-bold">{(selectedGame.home_win_prob * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>{selectedGame.away_team}:</span>
                        <span className="font-bold">{(selectedGame.away_win_prob * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="advantages" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Key Matchup Advantages</CardTitle>
                <CardDescription>
                  Statistical advantages that may determine the outcome
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {advantages.map((advantage, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border-2 ${
                        advantage.winner === selectedGame.home_team
                          ? 'border-red-200 bg-red-50'
                          : 'border-blue-200 bg-blue-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {advantage.icon}
                          <span className="font-semibold">{advantage.category}</span>
                        </div>
                        <Badge
                          variant={
                            advantage.winner === selectedGame.home_team
                              ? 'default'
                              : 'secondary'
                          }
                        >
                          {advantage.winner}
                        </Badge>
                      </div>
                      <div className="text-2xl font-bold">
                        {advantage.margin.toFixed(1)} points
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Statistical advantage
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Games List View
  return (
    <Card>
      <CardHeader>
        <CardTitle>All Bowl Games</CardTitle>
        <CardDescription>
          Click on any game for detailed analysis and breakdown
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {games.map((game) => (
            <div
              key={game.id}
              className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onGameSelect(game)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-lg">
                    {game.away_team} vs {game.home_team}
                  </span>
                  {getConfidenceBadge(game.confidence)}
                </div>
                <div className="text-right">
                  <div className="font-semibold">
                    {game.predicted_margin > 0 ? `${game.home_team}` : `${game.away_team}`}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {Math.abs(game.predicted_margin).toFixed(1)} pts
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>{formatGameDate(game.date)}</span>
                <span>{game.stadium}, {game.location}</span>
                <span>{game.conference}</span>
              </div>
              <div className="flex items-center space-x-4 mt-2">
                <div className="flex items-center space-x-1">
                  <span>{game.home_team}:</span>
                  <span className="font-medium">{(game.home_win_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span>{game.away_team}:</span>
                  <span className="font-medium">{(game.away_win_prob * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default BowlGameBreakdown;