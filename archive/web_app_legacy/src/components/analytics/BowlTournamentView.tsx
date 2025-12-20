/**
 * Bowl Tournament View Component
 *
 * Interactive tournament bracket visualization with:
 * - Visual bracket representation
 * - Championship probabilities
 * - Tournament simulation
 * - Round-by-round breakdown
 * - Upset predictions and analysis
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
  Trophy,
  Target,
  TrendingUp,
  Users,
  BarChart3,
  Activity,
  Play,
  RefreshCw,
  Zap,
} from 'lucide-react';

// Recharts components
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
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
}

interface PredictionComparison {
  game_id: number;
  ml_prediction: number;
  massey_prediction: number;
  simple_prediction: number;
  consensus_pick: string;
  value_rating: number;
}

interface TournamentBracket {
  round: number;
  games: BowlGame[];
}

interface SimulatedChampion {
  team: string;
  probability: number;
  conference: string;
  path: string[];
  upsetPotential: number;
}

interface BowlTournamentViewProps {
  games: BowlGame[];
  predictions: PredictionComparison[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const BowlTournamentView: React.FC<BowlTournamentViewProps> = ({
  games,
  predictions,
}) => {
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [simulationResults, setSimulationResults] = useState<SimulatedChampion[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);

  // Organize games by round (mock bowl hierarchy)
  const tournamentBracket = useMemo(() => {
    // In a real implementation, this would be based on actual bowl hierarchy
    const sortedGames = [...games].sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dateA - dateB;
    });

    // Mock bowl rounds
    const rounds: TournamentBracket[] = [
      {
        round: 1,
        games: sortedGames.slice(0, 8), // New Year's Six
      },
      {
        round: 2,
        games: sortedGames.slice(8, 20), // Major Bowls
      },
      {
        round: 3,
        games: sortedGames.slice(20, 35), // Mid-tier Bowls
      },
      {
        round: 4,
        games: sortedGames.slice(35), // Remaining Bowls
      },
    ].filter(r => r.games.length > 0);

    return rounds;
  }, [games]);

  // Simulate tournament outcomes
  const simulateTournament = () => {
    setIsSimulating(true);

    setTimeout(() => {
      const teams = Array.from(new Set(games.flatMap(g => [g.home_team, g.away_team])));
      const champions: SimulatedChampion[] = [];

      teams.forEach(team => {
        const teamGames = games.filter(g => g.home_team === team || g.away_team === team);
        const avgWinProb = teamGames.reduce((sum, game) => {
          const prob = game.home_team === team ? game.home_win_prob : game.away_win_prob;
          return sum + prob;
        }, 0) / teamGames.length;

        const conference = teamGames[0]?.conference || 'Unknown';
        const value = teamGames.reduce((sum, game) => {
          const pred = predictions.find(p => p.game_id === game.id);
          return sum + (pred?.value_rating || 0);
        }, 0) / teamGames.length;

        // Calculate upset potential (inverse of favorite status)
        const upsetPotential = teamGames.reduce((sum, game) => {
          const prob = game.home_team === team ? game.home_win_prob : game.away_win_prob;
          return sum + (1 - prob);
        }, 0) / teamGames.length;

        champions.push({
          team,
          probability: avgWinProb,
          conference,
          path: [`Round ${Math.floor(Math.random() * 4) + 1}`, `Round ${Math.floor(Math.random() * 4) + 1}`, 'Championship'],
          upsetPotential: upsetPotential * 100,
        });
      });

      // Sort by probability
      champions.sort((a, b) => b.probability - a.probability);

      setSimulationResults(champions);
      setIsSimulating(false);
    }, 2000);
  };

  // Conference distribution data
  const conferenceDistribution = useMemo(() => {
    const distribution: Record<string, number> = {};
    games.forEach(game => {
      if (game.conference) {
        distribution[game.conference] = (distribution[game.conference] || 0) + 1;
      }
    });

    return Object.entries(distribution).map(([conference, count]) => ({
      name: conference,
      value: count,
      percentage: (count / games.length) * 100,
    }));
  }, [games]);

  // Round distribution
  const roundDistribution = useMemo(() => {
    return tournamentBracket.map((round, index) => ({
      round: `Round ${round.round}`,
      games: round.games.length,
      percentage: (round.games.length / games.length) * 100,
    }));
  }, [tournamentBracket, games]);

  // Upset predictions
  const upsetPredictions = useMemo(() => {
    return predictions
      .filter(pred => {
        const game = games.find(g => g.id === pred.game_id);
        if (!game) return false;

        const highVariance = Math.abs(pred.ml_prediction) > 10;
        const lowConsensus = Math.abs(pred.ml_prediction - (pred.massey_prediction || 0)) > 5;
        const highValue = (pred.value_rating || 0) > 0.7;

        return highVariance || lowConsensus || highValue;
      })
      .map(pred => {
        const game = games.find(g => g.id === pred.game_id);
        if (!game) return null;

        return {
          game: `${game.away_team} vs ${game.home_team}`,
          upsetProbability: Math.min(0.5, Math.abs(game.predicted_margin) / 20),
          reason: Math.abs(pred.ml_prediction) > 10 ? 'High margin prediction' :
                  Math.abs(pred.ml_prediction - (pred.massey_prediction || 0)) > 5 ? 'Method disagreement' :
                  'High value rating',
        };
      })
      .filter(Boolean);
  }, [games, predictions]);

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'bg-green-500';
    if (confidence > 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getProbabilityColor = (probability: number) => {
    if (probability > 0.7) return 'text-green-600';
    if (probability > 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">🏆 Tournament Bracket</h2>
          <p className="text-muted-foreground">
            Interactive bracket with championship predictions and upset analysis
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={simulateTournament}
            disabled={isSimulating}
            className="flex items-center space-x-2"
          >
            {isSimulating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Simulating...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Simulate Tournament
              </>
            )}
          </Button>
          <Button variant="outline">
            <BarChart3 className="h-4 w-4 mr-2" />
            Export Bracket
          </Button>
        </div>
      </div>

      {/* Tournament Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Games</CardTitle>
            <Trophy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{games.length}</div>
            <p className="text-xs text-muted-foreground">
              Bowl games total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tournament Rounds</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tournamentBracket.length}</div>
            <p className="text-xs text-muted-foreground">
              Bracket rounds
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upset Predictions</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upsetPredictions.length}</div>
            <p className="text-xs text-muted-foreground">
              Potential upsets
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {games.length > 0 ?
                (games.reduce((sum, game) => sum + game.confidence, 0) / games.length * 100).toFixed(1) :
                '0'}
              %
            </div>
            <p className="text-xs text-muted-foreground">
              Prediction confidence
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="bracket" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="bracket">Bracket View</TabsTrigger>
          <TabsTrigger value="championship">Championship Odds</TabsTrigger>
          <TabsTrigger value="upsets">Upset Analysis</TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="bracket" className="space-y-4">
          {/* Tournament Bracket Visualization */}
          <div className="space-y-6">
            {tournamentBracket.map((round, roundIndex) => (
              <Card key={roundIndex}>
                <CardHeader>
                  <CardTitle>Round {round.round}</CardTitle>
                  <CardDescription>
                    {round.games.length} games • {round.percentage.toFixed(0)}% of tournament
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {round.games.map((game, gameIndex) => {
                      const prediction = predictions.find(p => p.game_id === game.id);
                      const consensus = prediction?.consensus_pick;
                      const value = prediction?.value_rating || 0;

                      return (
                        <div
                          key={game.id}
                          className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-sm">
                              {game.away_team}
                            </h4>
                            <span className="text-xs text-gray-500">vs</span>
                            <h4 className="font-semibold text-sm">
                              {game.home_team}
                            </h4>
                          </div>
                          <div className="text-center mb-2">
                            <div className="text-lg font-bold">
                              {game.predicted_margin > 0 ? game.home_team : game.away_team}
                            </div>
                            <div className="text-sm">
                              {Math.abs(game.predicted_margin).toFixed(1)} pts
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span>{game.bowl_name || 'Bowl Game'}</span>
                            <div className="flex items-center space-x-1">
                              <Badge className={getConfidenceColor(game.confidence)}>
                                {(game.confidence * 100).toFixed(0)}%
                              </Badge>
                              {consensus && (
                                <Badge variant="outline">
                                  {consensus}
                                </Badge>
                              )}
                            </div>
                          </div>
                          {value > 0.7 && (
                            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded">
                              <div className="text-xs text-green-800">
                                High Value: {(value * 100).toFixed(0)}%
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="championship" className="space-y-4">
          {/* Simulation Results */}
          {simulationResults.length > 0 ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Championship Simulation Results</CardTitle>
                  <CardDescription>
                    Probabilistic analysis based on team strengths and predictions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {simulationResults.slice(0, 10).map((champion, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="text-lg font-bold">
                            #{index + 1}
                          </div>
                          <div>
                            <h3 className="font-semibold">{champion.team}</h3>
                            <p className="text-sm text-muted-foreground">
                              {champion.conference}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${getProbabilityColor(champion.probability)}`}>
                            {(champion.probability * 100).toFixed(1)}%
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Championship probability
                          </p>
                        </div>
                        <div className="text-right">
                          <Badge
                            variant={champion.upsetPotential > 60 ? 'default' : 'secondary'}
                          >
                            {champion.upsetPotential > 60 ? 'Cinderella' : 'Favorite'}
                          </Badge>
                          <p className="text-xs text-muted-foreground mt-1">
                            Upset potential: {champion.upsetPotential.toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Conference Championship Odds */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Conference Championship Odds</CardTitle>
                    <CardDescription>
                      Which conferences are most likely to produce champions?
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

                <Card>
                  <CardHeader>
                    <CardTitle>Round Progression</CardTitle>
                    <CardDescription>
                      Distribution of games across tournament rounds
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={roundDistribution}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="round" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="games" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <Trophy className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Simulation Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Click "Simulate Tournament" to generate championship predictions
                  </p>
                  <Button onClick={simulateTournament} disabled={isSimulating}>
                    <Play className="h-4 w-4 mr-2" />
                    Run Simulation
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="upsets" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Potential Upsets</CardTitle>
              <CardDescription>
                Games with high upset probability based on model disagreements and value ratings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {upsetPredictions.map((upset, index) => (
                  <div
                    key={index}
                    className="p-4 border-2 border-orange-200 bg-orange-50 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-lg">{upset.game}</h3>
                      <Badge variant="outline" className="border-orange-300 text-orange-800">
                        {upset.upsetProbability > 0.3 ? 'High' : 'Medium'} Upset Risk
                      </Badge>
                    </div>
                    <div className="text-sm text-orange-800">
                      <strong>Reason:</strong> {upset.reason}
                    </div>
                    <div className="text-sm text-orange-700 mt-1">
                      Upset probability: {(upset.upsetProbability * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="statistics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confidence Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Confidence Distribution</CardTitle>
                <CardDescription>
                  Breakdown of prediction confidence levels
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={[
                      {
                        range: 'High (>80%)',
                        count: games.filter(g => g.confidence > 0.8).length,
                      },
                      {
                        range: 'Medium (60-80%)',
                        count: games.filter(g => g.confidence > 0.6 && g.confidence <= 0.8).length,
                      },
                      {
                        range: 'Low (40-60%)',
                        count: games.filter(g => g.confidence > 0.4 && g.confidence <= 0.6).length,
                      },
                      {
                        range: 'Very Low (<40%)',
                        count: games.filter(g => g.confidence <= 0.4).length,
                      },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Margin Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Predicted Margin Distribution</CardTitle>
                <CardDescription>
                  Range of predicted victory margins
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={[
                      {
                        margin: '0-3 pts',
                        count: games.filter(g => Math.abs(g.predicted_margin) <= 3).length,
                      },
                      {
                        margin: '4-7 pts',
                        count: games.filter(g => Math.abs(g.predicted_margin) > 3 && Math.abs(g.predicted_margin) <= 7).length,
                      },
                      {
                        margin: '8-14 pts',
                        count: games.filter(g => Math.abs(g.predicted_margin) > 7 && Math.abs(g.predicted_margin) <= 14).length,
                      },
                      {
                        margin: '15+ pts',
                        count: games.filter(g => Math.abs(g.predicted_margin) > 14).length,
                      },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="margin" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BowlTournamentView;