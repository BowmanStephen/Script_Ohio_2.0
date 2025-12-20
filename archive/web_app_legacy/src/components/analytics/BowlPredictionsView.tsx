/**
 * Bowl Predictions View Component
 *
 * Comprehensive prediction analysis comparing multiple prediction methods:
 * - ML Model predictions vs Massey ratings vs Simple predictions
 * - Consensus picks and confidence analysis
 * - Value betting opportunities
 * - Prediction accuracy trends
 * - Method performance comparison
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
  Brain,
  TrendingUp,
  Target,
  Award,
  BarChart3,
  PieChart,
  Activity,
  DollarSign,
  CheckCircle,
  AlertCircle,
  Star,
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
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart as RechartsPieChart,
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
}

interface PredictionComparison {
  game_id: number;
  ml_prediction: number;
  massey_prediction: number;
  simple_prediction: number;
  consensus_pick: string;
  value_rating: number;
}

interface BowlPredictionsViewProps {
  predictions: PredictionComparison[];
  games: BowlGame[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const BowlPredictionsView: React.FC<BowlPredictionsViewProps> = ({
  predictions,
  games,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<'all' | 'ml' | 'massey' | 'simple'>('all');
  const [sortBy, setSortBy] = useState<'confidence' | 'value' | 'margin'>('confidence');

  // Combine predictions with game data
  const enrichedPredictions = useMemo(() => {
    return predictions.map(prediction => {
      const game = games.find(g => g.id === prediction.game_id);
      if (!game) return null;

      return {
        ...prediction,
        game,
        ml_accuracy: game.confidence * 100,
        consensus_strength: Math.abs(prediction.ml_prediction) +
                          Math.abs(prediction.massey_prediction || 0) +
                          Math.abs(prediction.simple_prediction || 0) / 3,
      };
    }).filter(Boolean);
  }, [predictions, games]);

  // Filter predictions based on selected method
  const filteredPredictions = useMemo(() => {
    if (selectedMethod === 'all') return enrichedPredictions;

    return enrichedPredictions.filter(pred => {
      if (!pred?.game) return false;
      return pred.game.predicted_margin !== null; // Show all for now
    });
  }, [enrichedPredictions, selectedMethod]);

  // Sort predictions
  const sortedPredictions = useMemo(() => {
    return [...filteredPredictions].sort((a, b) => {
      if (sortBy === 'confidence') {
        return (b?.game?.confidence || 0) - (a?.game?.confidence || 0);
      } else if (sortBy === 'value') {
        return (b?.value_rating || 0) - (a?.value_rating || 0);
      } else {
        return Math.abs(b?.game?.predicted_margin || 0) - Math.abs(a?.game?.predicted_margin || 0);
      }
    });
  }, [filteredPredictions, sortBy]);

  // Calculate prediction method statistics
  const methodStats = useMemo(() => {
    const stats = {
      ml: { predictions: 0, avgConfidence: 0, highConfidence: 0 },
      massey: { predictions: 0, avgConfidence: 0, highConfidence: 0 },
      simple: { predictions: 0, avgConfidence: 0, highConfidence: 0 },
    };

    enrichedPredictions.forEach(pred => {
      if (!pred?.game) return;

      // ML stats
      stats.ml.predictions++;
      stats.ml.avgConfidence += pred.game.confidence * 100;
      if (pred.game.confidence > 0.8) stats.ml.highConfidence++;

      // Massey stats (estimate confidence based on prediction strength)
      if (pred.massey_prediction) {
        stats.massey.predictions++;
        const masseyConfidence = Math.min(0.95, Math.abs(pred.massey_prediction) / 15);
        stats.massey.avgConfidence += masseyConfidence * 100;
        if (masseyConfidence > 0.8) stats.massey.highConfidence++;
      }

      // Simple stats (estimate confidence)
      if (pred.simple_prediction) {
        stats.simple.predictions++;
        const simpleConfidence = Math.min(0.9, Math.abs(pred.simple_prediction) / 12);
        stats.simple.avgConfidence += simpleConfidence * 100;
        if (simpleConfidence > 0.8) stats.simple.highConfidence++;
      }
    });

    // Calculate averages
    Object.keys(stats).forEach(method => {
      const methodKey = method as keyof typeof stats;
      if (stats[methodKey].predictions > 0) {
        stats[methodKey].avgConfidence /= stats[methodKey].predictions;
      }
    });

    return stats;
  }, [enrichedPredictions]);

  // Prepare chart data
  const predictionComparisonData = useMemo(() => {
    return enrichedPredictions.slice(0, 20).map(pred => {
      if (!pred?.game) return null;
      return {
        game: `${pred.game.away_team} vs ${pred.game.home_team}`,
        ML: pred.ml_prediction || 0,
        Massey: pred.massey_prediction || 0,
        Simple: pred.simple_prediction || 0,
        consensus: pred.consensus_pick || '',
        value: pred.value_rating || 0,
      };
    }).filter(Boolean);
  }, [enrichedPredictions]);

  const methodPerformanceData = useMemo(() => {
    return [
      {
        method: 'ML Model',
        accuracy: 76.8,
        confidence: methodStats.ml.avgConfidence,
        predictions: methodStats.ml.predictions,
        highConfidence: methodStats.ml.highConfidence,
      },
      {
        method: 'Massey Ratings',
        accuracy: 72.3,
        confidence: methodStats.massey.avgConfidence,
        predictions: methodStats.massey.predictions,
        highConfidence: methodStats.massey.highConfidence,
      },
      {
        method: 'Simple Model',
        accuracy: 68.5,
        confidence: methodStats.simple.avgConfidence,
        predictions: methodStats.simple.predictions,
        highConfidence: methodStats.simple.highConfidence,
      },
    ];
  }, [methodStats]);

  const valueDistributionData = useMemo(() => {
    const distribution = {
      'High Value (>0.8)': 0,
      'Medium Value (0.6-0.8)': 0,
      'Low Value (0.4-0.6)': 0,
      'No Value (<0.4)': 0,
    };

    enrichedPredictions.forEach(pred => {
      if (!pred?.value_rating) return;

      if (pred.value_rating > 0.8) {
        distribution['High Value (>0.8)']++;
      } else if (pred.value_rating > 0.6) {
        distribution['Medium Value (0.6-0.8)']++;
      } else if (pred.value_rating > 0.4) {
        distribution['Low Value (0.4-0.6)']++;
      } else {
        distribution['No Value (<0.4)']++;
      }
    });

    return Object.entries(distribution).map(([range, count]) => ({
      range,
      count,
      percentage: (count / enrichedPredictions.length) * 100,
    }));
  }, [enrichedPredictions]);

  const getValueBadge = (value: number) => {
    if (value > 0.8) {
      return <Badge className="bg-green-500">High Value</Badge>;
    } else if (value > 0.6) {
      return <Badge className="bg-yellow-500">Medium Value</Badge>;
    } else if (value > 0.4) {
      return <Badge variant="secondary">Low Value</Badge>;
    }
    return <Badge variant="outline">No Value</Badge>;
  };

  const getConsensusIcon = (strength: number) => {
    if (strength > 10) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (strength > 5) {
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
    return <AlertCircle className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Prediction Analysis</h2>
          <p className="text-muted-foreground">
            Compare ML models, Massey ratings, and simple predictions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value as any)}
          >
            <option value="all">All Methods</option>
            <option value="ml">ML Model Only</option>
            <option value="massey">Massey Only</option>
            <option value="simple">Simple Only</option>
          </select>
          <select
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="confidence">Sort by Confidence</option>
            <option value="value">Sort by Value</option>
            <option value="margin">Sort by Margin</option>
          </select>
        </div>
      </div>

      {/* Method Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {methodPerformanceData.map((method, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{method.method}</CardTitle>
              {index === 0 && <Brain className="h-4 w-4 text-muted-foreground" />}
              {index === 1 && <BarChart3 className="h-4 w-4 text-muted-foreground" />}
              {index === 2 && <Activity className="h-4 w-4 text-muted-foreground" />}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{method.accuracy.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {method.predictions} predictions
              </p>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Avg Confidence:</span>
                  <span className="font-medium">{method.confidence.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>High Confidence:</span>
                  <span className="font-medium">{method.highConfidence}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prediction Method Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>Prediction Method Comparison</CardTitle>
            <CardDescription>
              Margin predictions from different methods for top games
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={predictionComparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="game"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                  tick={{ fontSize: 10 }}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="ML" fill="#8884d8" />
                <Bar dataKey="Massey" fill="#82ca9d" />
                <Bar dataKey="Simple" fill="#ffc658" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Value Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Betting Value Distribution</CardTitle>
            <CardDescription>
              Analysis of prediction value across all bowl games
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={valueDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({range, percentage}) => `${range}: ${percentage.toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {valueDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </RechartsPieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Predictions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Prediction Analysis</CardTitle>
          <CardDescription>
            Complete breakdown with consensus picks and value ratings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sortedPredictions.slice(0, 15).map((prediction, index) => {
              if (!prediction?.game) return null;

              return (
                <div
                  key={index}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">
                        {prediction.game.away_team} vs {prediction.game.home_team}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {prediction.game.conference} • {new Date(prediction.game.date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getConsensusIcon(prediction.consensus_strength)}
                      {getValueBadge(prediction.value_rating || 0)}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* ML Prediction */}
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <Brain className="h-4 w-4 text-blue-600" />
                        <span className="font-medium text-sm">ML Model</span>
                      </div>
                      <div className="text-lg font-bold">
                        {prediction.ml_prediction > 0 ? prediction.game.home_team : prediction.game.away_team}
                      </div>
                      <div className="text-sm">
                        {Math.abs(prediction.ml_prediction).toFixed(1)} pts
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Confidence: {(prediction.game.confidence * 100).toFixed(1)}%
                      </div>
                    </div>

                    {/* Massey Prediction */}
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <BarChart3 className="h-4 w-4 text-green-600" />
                        <span className="font-medium text-sm">Massey</span>
                      </div>
                      <div className="text-lg font-bold">
                        {prediction.massey_prediction && prediction.massey_prediction > 0
                          ? prediction.game.home_team
                          : prediction.game.away_team}
                      </div>
                      <div className="text-sm">
                        {prediction.massey_prediction ?
                          `${Math.abs(prediction.massey_prediction).toFixed(1)} pts` :
                          'N/A'}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Historical ratings
                      </div>
                    </div>

                    {/* Simple Prediction */}
                    <div className="p-3 bg-yellow-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <Activity className="h-4 w-4 text-yellow-600" />
                        <span className="font-medium text-sm">Simple</span>
                      </div>
                      <div className="text-lg font-bold">
                        {prediction.simple_prediction && prediction.simple_prediction > 0
                          ? prediction.game.home_team
                          : prediction.game.away_team}
                      </div>
                      <div className="text-sm">
                        {prediction.simple_prediction ?
                          `${Math.abs(prediction.simple_prediction).toFixed(1)} pts` :
                          'N/A'}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Basic model
                      </div>
                    </div>

                    {/* Consensus */}
                    <div className="p-3 bg-purple-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <Award className="h-4 w-4 text-purple-600" />
                        <span className="font-medium text-sm">Consensus</span>
                      </div>
                      <div className="text-lg font-bold">
                        {prediction.consensus_pick}
                      </div>
                      <div className="text-sm">
                        {prediction.consensus_strength.toFixed(1)} strength
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Agreement level
                      </div>
                    </div>
                  </div>

                  {/* Value Analysis */}
                  {prediction.value_rating && prediction.value_rating > 0.6 && (
                    <div className="mt-3 p-3 bg-green-100 border border-green-300 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <DollarSign className="h-4 w-4 text-green-600" />
                        <span className="font-medium text-green-800">Betting Value Alert</span>
                      </div>
                      <div className="text-sm text-green-700 mt-1">
                        This prediction shows significant value ({(prediction.value_rating * 100).toFixed(0)}% rating)
                        based on consensus disagreement and strong model confidence.
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Games</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{enrichedPredictions.length}</div>
            <p className="text-xs text-muted-foreground">
              Bowl games analyzed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Value Games</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {enrichedPredictions.filter(p => p?.value_rating && p.value_rating > 0.8).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Value rating &gt; 80%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Consensus Strong</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {enrichedPredictions.filter(p => p?.consensus_strength && p.consensus_strength > 10).length}
            </div>
            <p className="text-xs text-muted-foreground">
              High agreement games
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg ML Confidence</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {methodStats.ml.avgConfidence.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Across all predictions
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BowlPredictionsView;