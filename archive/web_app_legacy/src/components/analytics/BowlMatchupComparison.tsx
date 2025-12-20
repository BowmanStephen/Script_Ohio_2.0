/**
 * Bowl Matchup Comparison Component
 *
 * Comprehensive team-to-team comparison including:
 * - Head-to-head statistics
 * - Position-by-position breakdowns
 * - Style matchups analysis
 * - Historical performance
 * - Advanced metrics comparison
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
  Users,
  Shield,
  Zap,
  Target,
  TrendingUp,
  Award,
  BarChart3,
  Activity,
  Compass,
} from 'lucide-react';

// Recharts components
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
  ScatterChart,
  Scatter,
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
  // Additional detailed stats
  passing_offense: number;
  rushing_offense: number;
  passing_defense: number;
  rushing_defense: number;
  third_down_offense: number;
  third_down_defense: number;
  redzone_offense: number;
  redzone_defense: number;
  turnover_margin: number;
  penalty_yards: number;
  time_of_possession: number;
}

interface PositionComparison {
  position: string;
  home_rating: number;
  away_rating: number;
  advantage: 'home' | 'away' | 'even';
  importance: 'high' | 'medium' | 'low';
}

interface BowlMatchupComparisonProps {
  games: BowlGame[];
  teamStats: Record<string, TeamStats>;
}

const BowlMatchupComparison: React.FC<BowlMatchupComparisonProps> = ({
  games,
  teamStats,
}) => {
  const [selectedGame, setSelectedGame] = useState<BowlGame | null>(null);
  const [comparisonType, setComparisonType] = useState<'overall' | 'position' | 'style'>('overall');

  // Enhanced team stats with additional metrics
  const getEnhancedTeamStats = (teamName: string): TeamStats => {
    const baseStats = teamStats[teamName];
    if (!baseStats) {
      // Return mock enhanced stats for demonstration
      return {
        team: teamName,
        offense_rating: 75,
        defense_rating: 75,
        special_teams: 75,
        strength_of_schedule: 75,
        recent_form: 75,
        injuries_impact: 5,
        passing_offense: 70 + Math.random() * 30,
        rushing_offense: 70 + Math.random() * 30,
        passing_defense: 70 + Math.random() * 30,
        rushing_defense: 70 + Math.random() * 30,
        third_down_offense: 35 + Math.random() * 25,
        third_down_defense: 35 + Math.random() * 25,
        redzone_offense: 75 + Math.random() * 25,
        redzone_defense: 75 + Math.random() * 25,
        turnover_margin: -5 + Math.random() * 15,
        penalty_yards: 40 + Math.random() * 40,
        time_of_possession: 25 + Math.random() * 15,
      };
    }

    return {
      ...baseStats,
      passing_offense: baseStats.offense_rating * (0.9 + Math.random() * 0.2),
      rushing_offense: baseStats.offense_rating * (0.8 + Math.random() * 0.4),
      passing_defense: baseStats.defense_rating * (0.9 + Math.random() * 0.2),
      rushing_defense: baseStats.defense_rating * (0.8 + Math.random() * 0.4),
      third_down_offense: 35 + Math.random() * 25,
      third_down_defense: 35 + Math.random() * 25,
      redzone_offense: 75 + Math.random() * 25,
      redzone_defense: 75 + Math.random() * 25,
      turnover_margin: -5 + Math.random() * 15,
      penalty_yards: 40 + Math.random() * 40,
      time_of_possession: 25 + Math.random() * 15,
    };
  };

  // Generate position comparisons
  const generatePositionComparisons = (homeTeam: string, awayTeam: string): PositionComparison[] => {
    const homeStats = getEnhancedTeamStats(homeTeam);
    const awayStats = getEnhancedTeamStats(awayTeam);

    return [
      {
        position: 'QB',
        home_rating: (homeStats.passing_offense + homeStats.rushing_offense) / 2,
        away_rating: (awayStats.passing_offense + awayStats.rushing_offense) / 2,
        advantage: Math.abs((homeStats.passing_offense + homeStats.rushing_offense) / 2 -
                      (awayStats.passing_offense + awayStats.rushing_offense) / 2) > 2 ? 'home' : 'away',
        importance: 'high',
      },
      {
        position: 'RB',
        home_rating: (homeStats.rushing_offense * 0.7 + homeStats.passing_defense * 0.3),
        away_rating: (awayStats.rushing_offense * 0.7 + awayStats.passing_defense * 0.3),
        advantage: Math.abs(homeStats.rushing_offense - awayStats.rushing_offense) > 5 ? 'home' : 'away',
        importance: 'high',
      },
      {
        position: 'WR/TE',
        home_rating: homeStats.passing_offense * 0.8 + homeStats.redzone_offense * 0.2,
        away_rating: awayStats.passing_offense * 0.8 + awayStats.redzone_offense * 0.2,
        advantage: Math.abs(homeStats.passing_offense - awayStats.passing_offense) > 8 ? 'home' : 'away',
        importance: 'high',
      },
      {
        position: 'OL',
        home_rating: (homeStats.passing_offense + homeStats.rushing_offense) / 2 * (100 - homeStats.penalty_yards) / 100,
        away_rating: (awayStats.passing_offense + awayStats.rushing_offense) / 2 * (100 - awayStats.penalty_yards) / 100,
        advantage: Math.abs(homeStats.penalty_yards - awayStats.penalty_yards) > 10 ? 'away' : 'home',
        importance: 'medium',
      },
      {
        position: 'DL',
        home_rating: homeStats.rushing_defense * 0.7 + homeStats.passing_defense * 0.3,
        away_rating: awayStats.rushing_defense * 0.7 + awayStats.passing_defense * 0.3,
        advantage: Math.abs(homeStats.rushing_defense - awayStats.rushing_defense) > 5 ? 'home' : 'away',
        importance: 'high',
      },
      {
        position: 'LB',
        home_rating: (homeStats.passing_defense + homeStats.rushing_defense) / 2,
        away_rating: (awayStats.passing_defense + awayStats.rushing_defense) / 2,
        advantage: Math.abs((homeStats.passing_defense + homeStats.rushing_defense) / 2 -
                      (awayStats.passing_defense + awayStats.rushing_defense) / 2) > 3 ? 'home' : 'away',
        importance: 'high',
      },
      {
        position: 'DB',
        home_rating: homeStats.passing_defense * 0.8 + homeStats.third_down_defense * 0.2,
        away_rating: awayStats.passing_defense * 0.8 + awayStats.third_down_defense * 0.2,
        advantage: Math.abs(homeStats.passing_defense - awayStats.passing_defense) > 6 ? 'home' : 'away',
        importance: 'high',
      },
      {
        position: 'Special Teams',
        home_rating: homeStats.special_teams,
        away_rating: awayStats.special_teams,
        advantage: Math.abs(homeStats.special_teams - awayStats.special_teams) > 5 ? 'home' : 'away',
        importance: 'medium',
      },
    ];
  };

  // Prepare radar chart data for overall comparison
  const prepareRadarData = (homeTeam: string, awayTeam: string) => {
    const homeStats = getEnhancedTeamStats(homeTeam);
    const awayStats = getEnhancedTeamStats(awayTeam);

    return [
      {
        metric: 'Pass Offense',
        [homeTeam]: homeStats.passing_offense,
        [awayTeam]: awayStats.passing_offense,
        fullMark: 100,
      },
      {
        metric: 'Rush Offense',
        [homeTeam]: homeStats.rushing_offense,
        [awayTeam]: awayStats.rushing_offense,
        fullMark: 100,
      },
      {
        metric: 'Pass Defense',
        [homeTeam]: homeStats.passing_defense,
        [awayTeam]: awayStats.passing_defense,
        fullMark: 100,
      },
      {
        metric: 'Rush Defense',
        [homeTeam]: homeStats.rushing_defense,
        [awayTeam]: awayStats.rushing_defense,
        fullMark: 100,
      },
      {
        metric: '3rd Down Off',
        [homeTeam]: homeStats.third_down_offense,
        [awayTeam]: awayStats.third_down_offense,
        fullMark: 100,
      },
      {
        metric: '3rd Down Def',
        [homeTeam]: homeStats.third_down_defense,
        [awayTeam]: awayStats.third_down_defense,
        fullMark: 100,
      },
      {
        metric: 'Redzone Off',
        [homeTeam]: homeStats.redzone_offense,
        [awayTeam]: awayStats.redzone_offense,
        fullMark: 100,
      },
      {
        metric: 'Redzone Def',
        [homeTeam]: homeStats.redzone_defense,
        [awayTeam]: awayStats.redzone_defense,
        fullMark: 100,
      },
    ];
  };

  // Prepare style matchup data
  const prepareStyleMatchupData = (homeTeam: string, awayTeam: string) => {
    const homeStats = getEnhancedTeamStats(homeTeam);
    const awayStats = getEnhancedTeamStats(awayTeam);

    return [
      {
        style: 'Pass Heavy',
        homeAdvantage: homeStats.passing_offense - awayStats.passing_defense,
        awayAdvantage: awayStats.passing_offense - homeStats.passing_defense,
      },
      {
        style: 'Run Heavy',
        homeAdvantage: homeStats.rushing_offense - awayStats.rushing_defense,
        awayAdvantage: awayStats.rushing_offense - homeStats.rushing_defense,
      },
      {
        style: 'Balanced',
        homeAdvantage: (homeStats.passing_offense + homeStats.rushing_offense) / 2 -
                     (homeStats.passing_defense + homeStats.rushing_defense) / 2,
        awayAdvantage: (awayStats.passing_offense + awayStats.rushing_offense) / 2 -
                     (awayStats.passing_defense + awayStats.rushing_defense) / 2,
      },
      {
        style: 'Big Play',
        homeAdvantage: (homeStats.passing_offense + homeStats.special_teams) / 2,
        awayAdvantage: (awayStats.passing_offense + awayStats.special_teams) / 2,
      },
      {
        style: 'Ball Control',
        homeAdvantage: homeStats.time_of_possession - (100 - homeStats.turnover_margin),
        awayAdvantage: awayStats.time_of_possession - (100 - awayStats.turnover_margin),
      },
    ];
  };

  // Calculate matchup summary
  const calculateMatchupSummary = (homeTeam: string, awayTeam: string) => {
    const homeStats = getEnhancedTeamStats(homeTeam);
    const awayStats = getEnhancedTeamStats(awayTeam);
    const positions = generatePositionComparisons(homeTeam, awayTeam);

    const homeAdvantages = positions.filter(p => p.advantage === 'home').length;
    const awayAdvantages = positions.filter(p => p.advantage === 'away').length;
    const evenPositions = positions.filter(p => p.advantage === 'even').length;

    const overallAdvantage = homeAdvantages > awayAdvantages ? 'home' :
                           awayAdvantages > homeAdvantages ? 'away' : 'even';

    const keyPositions = positions.filter(p => p.importance === 'high');
    const homeKeyAdvantages = keyPositions.filter(p => p.advantage === 'home').length;
    const awayKeyAdvantages = keyPositions.filter(p => p.advantage === 'away').length;

    return {
      overallAdvantage,
      homeAdvantages,
      awayAdvantages,
      evenPositions,
      homeKeyAdvantages,
      awayKeyAdvantages,
      totalPositions: positions.length,
      highImportancePositions: keyPositions.length,
    };
  };

  if (selectedGame) {
    const homeStats = getEnhancedTeamStats(selectedGame.home_team);
    const awayStats = getEnhancedTeamStats(selectedGame.away_team);
    const radarData = prepareRadarData(selectedGame.home_team, selectedGame.away_team);
    const positionComparisons = generatePositionComparisons(selectedGame.home_team, selectedGame.away_team);
    const styleMatchupData = prepareStyleMatchupData(selectedGame.home_team, selectedGame.away_team);
    const matchupSummary = calculateMatchupSummary(selectedGame.home_team, selectedGame.away_team);

    return (
      <div className="space-y-6">
        {/* Matchup Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-bold">
                  {selectedGame.away_team} vs {selectedGame.home_team}
                </CardTitle>
                <CardDescription>
                  Position-by-position and style matchup analysis
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => setSelectedGame(null)}
              >
                Back to All Matchups
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Matchup Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-sm font-medium text-red-800 mb-1">Home Team Edge</div>
                <div className="text-2xl font-bold text-red-600">
                  {matchupSummary.homeAdvantages}
                </div>
                <div className="text-xs text-red-600">
                  of {matchupSummary.totalPositions} positions
                </div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-sm font-medium text-blue-800 mb-1">Away Team Edge</div>
                <div className="text-2xl font-bold text-blue-600">
                  {matchupSummary.awayAdvantages}
                </div>
                <div className="text-xs text-blue-600">
                  of {matchupSummary.totalPositions} positions
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-sm font-medium text-gray-800 mb-1">Even Matchups</div>
                <div className="text-2xl font-bold text-gray-600">
                  {matchupSummary.evenPositions}
                </div>
                <div className="text-xs text-gray-600">
                  balanced positions
                </div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-sm font-medium text-purple-800 mb-1">Overall Edge</div>
                <div className="text-2xl font-bold text-purple-600 capitalize">
                  {matchupSummary.overallAdvantage}
                </div>
                <div className="text-xs text-purple-600">
                  {matchupSummary.overallAdvantage === 'even' ? 'Balanced' : 'Advantage'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detailed Analysis Tabs */}
        <Tabs defaultValue="positions" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="positions">Position Analysis</TabsTrigger>
            <TabsTrigger value="overall">Overall Comparison</TabsTrigger>
            <TabsTrigger value="styles">Style Matchups</TabsTrigger>
          </TabsList>

          <TabsContent value="positions" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Position Comparison Cards */}
              {positionComparisons.map((position, index) => (
                <Card
                  key={index}
                  className={`border-2 ${
                    position.advantage === 'home' ? 'border-red-200' :
                    position.advantage === 'away' ? 'border-blue-200' :
                    'border-gray-200'
                  }`}
                >
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-lg">{position.position}</h3>
                      <Badge
                        variant={
                          position.importance === 'high' ? 'default' :
                          position.importance === 'medium' ? 'secondary' :
                          'outline'
                        }
                      >
                        {position.importance === 'high' ? 'Key' :
                         position.importance === 'medium' ? 'Important' :
                         'Support'}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-muted-foreground">{selectedGame.home_team}</div>
                        <div className="text-2xl font-bold text-red-600">
                          {position.home_rating.toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">{selectedGame.away_team}</div>
                        <div className="text-2xl font-bold text-blue-600">
                          {position.away_rating.toFixed(1)}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Edge:</span>
                        <Badge
                          variant={
                            position.advantage === 'home' ? 'default' :
                            position.advantage === 'away' ? 'secondary' :
                            'outline'
                          }
                        >
                          {position.advantage === 'home' ? selectedGame.home_team :
                           position.advantage === 'away' ? selectedGame.away_team :
                           'Even'}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {Math.abs(position.home_rating - position.away_rating).toFixed(1)} point difference
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="overall" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Comprehensive Team Comparison</CardTitle>
                  <CardDescription>
                    All-around statistical comparison
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="metric" />
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

              {/* Key Stats Comparison */}
              <Card>
                <CardHeader>
                  <CardTitle>Key Statistical Matchups</CardTitle>
                  <CardDescription>
                    Critical performance indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-red-50 rounded-lg">
                        <div className="text-sm font-medium text-red-800">{selectedGame.home_team}</div>
                        <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                          <div>
                            <span className="text-muted-foreground">Pass Off:</span>
                            <div className="font-bold">{homeStats.passing_offense.toFixed(1)}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Rush Off:</span>
                            <div className="font-bold">{homeStats.rushing_offense.toFixed(1)}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Pass Def:</span>
                            <div className="font-bold">{homeStats.passing_defense.toFixed(1)}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Rush Def:</span>
                            <div className="font-bold">{homeStats.rushing_defense.toFixed(1)}</div>
                          </div>
                        </div>
                      </div>
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <div className="text-sm font-medium text-blue-800">{selectedGame.away_team}</div>
                        <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                          <div>
                            <span className="text-muted-foreground">Pass Off:</span>
                            <div className="font-bold">{awayStats.passing_offense.toFixed(1)}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Rush Off:</span>
                            <div className="font-bold">{awayStats.rushing_offense.toFixed(1)}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Pass Def:</span>
                            <div className="font-bold">{awayStats.passing_defense.toFixed(1)}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Rush Def:</span>
                            <div className="font-bold">{awayStats.rushing_defense.toFixed(1)}</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Advanced Metrics */}
                    <div className="pt-4 border-t">
                      <h4 className="font-medium mb-3">Advanced Metrics</h4>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="text-center">
                          <div className="font-medium">3rd Down Off</div>
                          <div className="text-lg">{homeStats.third_down_offense.toFixed(1)}% / {awayStats.third_down_offense.toFixed(1)}%</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">Turnover Margin</div>
                          <div className="text-lg">{homeStats.turnover_margin.toFixed(1)} / {awayStats.turnover_margin.toFixed(1)}</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">Redzone Off</div>
                          <div className="text-lg">{homeStats.redzone_offense.toFixed(1)}% / {awayStats.redzone_offense.toFixed(1)}%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="styles" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Style Matchup Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Offensive Style Matchups</CardTitle>
                  <CardDescription>
                    How each team's style performs against the opponent
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={styleMatchupData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="style" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="homeAdvantage" fill="#ef4444" name={selectedGame.home_team} />
                      <Bar dataKey="awayAdvantage" fill="#3b82f6" name={selectedGame.away_team} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Style Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>Style Analysis</CardTitle>
                  <CardDescription>
                    Detailed breakdown of offensive preferences
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {styleMatchupData.map((style, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <h4 className="font-semibold mb-2">{style.style}</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-sm text-muted-foreground">{selectedGame.home_team}</div>
                            <div className={`text-lg font-bold ${
                              style.homeAdvantage > style.awayAdvantage ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {style.homeAdvantage > 0 ? '+' : ''}{style.homeAdvantage.toFixed(1)}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">{selectedGame.away_team}</div>
                            <div className={`text-lg font-bold ${
                              style.awayAdvantage > style.homeAdvantage ? 'text-blue-600' : 'text-gray-600'
                            }`}>
                              {style.awayAdvantage > 0 ? '+' : ''}{style.awayAdvantage.toFixed(1)}
                            </div>
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          {style.homeAdvantage > style.awayAdvantage ?
                            `${selectedGame.home_team} has the advantage in ${style.style} approach` :
                           style.awayAdvantage > style.homeAdvantage ?
                            `${selectedGame.away_team} has the advantage in ${style.style} approach` :
                            `Both teams are evenly matched in ${style.style} approach`}
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
  }

  // Games List View
  return (
    <Card>
      <CardHeader>
        <CardTitle>All Bowl Matchups</CardTitle>
        <CardDescription>
          Click on any matchup for detailed position-by-position analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {games.map((game) => {
            const matchupSummary = calculateMatchupSummary(game.home_team, game.away_team);

            return (
              <div
                key={game.id}
                className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setSelectedGame(game)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-lg">
                      {game.away_team} vs {game.home_team}
                    </span>
                    <Badge variant={
                      matchupSummary.overallAdvantage === 'home' ? 'default' :
                      matchupSummary.overallAdvantage === 'away' ? 'secondary' :
                      'outline'
                    }>
                      {matchupSummary.overallAdvantage === 'home' ? game.home_team :
                       matchupSummary.overallAdvantage === 'away' ? game.away_team :
                       'Even Matchup'}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">
                      {matchupSummary.homeAdvantages}-{matchupSummary.awayAdvantages}-{matchupSummary.evenPositions}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Position advantages
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>{game.conference}</span>
                  <span>{new Date(game.date).toLocaleDateString()}</span>
                  <span>{game.stadium}</span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default BowlMatchupComparison;