/**
 * Model Comparison Dashboard
 *
 * Displays detailed comparisons between all ML models:
 * - Ridge Regression
 * - XGBoost Classifier
 * - FastAI Neural Network
 * - Ensemble Method
 *
 * Shows individual predictions, confidence scores, and model agreement analysis.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LineChart,
  Line,
  ScatterChart,
  Scatter
} from 'recharts';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  Zap,
  Cpu,
  Network,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';

interface ModelPrediction {
  margin: number;
  home_win_probability: number;
}

interface ModelComparison {
  game_id: number;
  bowl_name: string;
  home_team: string;
  away_team: string;
  ridge_prediction: ModelPrediction;
  xgb_prediction: ModelPrediction;
  fastai_prediction: ModelPrediction;
  ensemble_prediction: ModelPrediction;
}

interface ModelMetrics {
  model: string;
  icon: React.ElementType;
  color: string;
  avg_confidence: number;
  avg_margin: number;
  agreement_with_ensemble: number;
  predictions: number;
}

const MODEL_CONFIG = {
  ridge: {
    name: 'Ridge Regression',
    icon: TrendingUp,
    color: '#3b82f6',
    description: 'Linear regression with L2 regularization'
  },
  xgb: {
    name: 'XGBoost Classifier',
    icon: Cpu,
    color: '#10b981',
    description: 'Gradient boosting decision trees'
  },
  fastai: {
    name: 'FastAI Neural Network',
    icon: Network,
    color: '#f59e0b',
    description: 'Deep learning neural network model'
  },
  ensemble: {
    name: 'Ensemble Method',
    icon: Brain,
    color: '#8b5cf6',
    description: 'Weighted combination of all models'
  }
};

const COLORS = {
  ridge: '#3b82f6',
  xgb: '#10b981',
  fastai: '#f59e0b',
  ensemble: '#8b5cf6',
  agreement: '#06b6d4',
  disagreement: '#f43f5e'
};

export function ModelComparisonDashboard() {
  const [comparisons, setComparisons] = useState<ModelComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedGame, setSelectedGame] = useState<ModelComparison | null>(null);

  // Fetch model comparison data
  useEffect(() => {
    const fetchModelComparisons = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('http://localhost:5002/api/model-comparisons');
        const data = await response.json();

        if (data.success) {
          setComparisons(data.data.comparisons);
        } else {
          setError(data.error || 'Failed to fetch model comparisons');
        }
      } catch (err) {
        setError('Network error while fetching model comparisons');
        console.error('Error fetching model comparisons:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchModelComparisons();
  }, []);

  // Calculate model metrics
  const modelMetrics = useMemo((): ModelMetrics[] => {
    if (comparisons.length === 0) return [];

    const metrics: ModelMetrics[] = Object.entries(MODEL_CONFIG).map(([key, config]) => {
      const predictions = comparisons.map(comp => (comp as any)[`${key}_prediction`] as ModelPrediction);

      const avgConfidence = predictions.reduce((sum, p) => sum + p.home_win_probability, 0) / predictions.length;
      const avgMargin = predictions.reduce((sum, p) => sum + Math.abs(p.margin), 0) / predictions.length;

      // Calculate agreement with ensemble
      let agreementCount = 0;
      comparisons.forEach(comp => {
        const modelPred = (comp as any)[`${key}_prediction`] as ModelPrediction;
        const ensemblePred = comp.ensemble_prediction;

        // Agreement if both predict same winner (probability > 0.5)
        if ((modelPred.home_win_probability > 0.5 && ensemblePred.home_win_probability > 0.5) ||
            (modelPred.home_win_probability < 0.5 && ensemblePred.home_win_probability < 0.5)) {
          agreementCount++;
        }
      });

      return {
        model: config.name,
        icon: config.icon,
        color: config.color,
        avg_confidence: avgConfidence,
        avg_margin: avgMargin,
        agreement_with_ensemble: agreementCount / comparisons.length,
        predictions: predictions.length
      };
    });

    return metrics;
  }, [comparisons]);

  // Calculate consensus analysis
  const consensusAnalysis = useMemo(() => {
    if (comparisons.length === 0) return { highConsensus: 0, lowConsensus: 0, average: 0 };

    let highConsensus = 0;
    let lowConsensus = 0;

    comparisons.forEach(comp => {
      const predictions = [
        comp.ridge_prediction.home_win_probability,
        comp.xgb_prediction.home_win_probability,
        comp.fastai_prediction.home_win_probability
      ];

      const stdDev = Math.sqrt(
        predictions.reduce((sum, p) => sum + Math.pow(p - 0.5, 2), 0) / predictions.length
      );

      if (stdDev < 0.1) highConsensus++;
      else if (stdDev > 0.2) lowConsensus++;
    });

    return {
      highConsensus,
      lowConsensus,
      average: comparisons.length - highConsensus - lowConsensus
    };
  }, [comparisons]);

  // Prepare data for charts
  const confidenceData = modelMetrics.map(metric => ({
    name: metric.model,
    confidence: (metric.avg_confidence * 100).toFixed(1),
    agreement: (metric.agreement_with_ensemble * 100).toFixed(1)
  }));

  const radarData = modelMetrics.map(metric => ({
    model: metric.model,
    confidence: metric.avg_confidence * 100,
    agreement: metric.agreement_with_ensemble * 100,
    accuracy: 100 - (metric.avg_margin / 20 * 100), // Normalized accuracy estimate
    predictions: metric.predictions
  }));

  // Scatter plot data for model agreement
  const scatterData = comparisons.map(comp => ({
    ridge: comp.ridge_prediction.home_win_probability * 100,
    xgb: comp.xgb_prediction.home_win_probability * 100,
    fastai: comp.fastai_prediction.home_win_probability * 100,
    ensemble: comp.ensemble_prediction.home_win_probability * 100,
    game: `${comp.away_team} vs ${comp.home_team}`
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Activity className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2">Loading model comparisons...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="p-6">
          <div className="flex items-center text-red-600">
            <AlertTriangle className="h-5 w-5 mr-2" />
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {modelMetrics.map((metric) => (
          <Card key={metric.model} className="border-l-4" style={{ borderLeftColor: metric.color }}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center">
                <metric.icon className="h-4 w-4 mr-2" style={{ color: metric.color }} />
                {metric.model}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Confidence:</span>
                  <span className="font-medium">{(metric.avg_confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Agreement:</span>
                  <span className="font-medium">{(metric.agreement_with_ensemble * 100).toFixed(1)}%</span>
                </div>
                <Progress value={metric.avg_confidence * 100} className="h-2" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Model Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confidence & Agreement Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Model Confidence & Agreement</CardTitle>
            <CardDescription>
              Average confidence scores and agreement with ensemble method
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={confidenceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="confidence" fill={COLORS.ensemble} name="Confidence %" />
                <Bar dataKey="agreement" fill={COLORS.agreement} name="Agreement %" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Radar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Model Performance Radar</CardTitle>
            <CardDescription>
              Multi-dimensional comparison of all models
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="model" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="Confidence"
                  dataKey="confidence"
                  stroke={COLORS.ensemble}
                  fill={COLORS.ensemble}
                  fillOpacity={0.3}
                />
                <Radar
                  name="Agreement"
                  dataKey="agreement"
                  stroke={COLORS.agreement}
                  fill={COLORS.agreement}
                  fillOpacity={0.3}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Consensus Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Model Consensus Analysis</CardTitle>
          <CardDescription>
            How often the individual models agree with each other
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{consensusAnalysis.highConsensus}</div>
              <div className="text-sm text-green-600">High Consensus Games</div>
              <div className="text-xs text-gray-600 mt-1">All models agree</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{consensusAnalysis.average}</div>
              <div className="text-sm text-yellow-600">Medium Consensus Games</div>
              <div className="text-xs text-gray-600 mt-1">Some disagreement</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{consensusAnalysis.lowConsensus}</div>
              <div className="text-sm text-red-600">Low Consensus Games</div>
              <div className="text-xs text-gray-600 mt-1">Major disagreement</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{comparisons.length}</div>
              <div className="text-sm text-blue-600">Total Games Analyzed</div>
              <div className="text-xs text-gray-600 mt-1">FBS bowl games only</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Game Comparisons */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Game Comparisons</CardTitle>
          <CardDescription>
            Individual predictions for each model across all games
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Bowl Game</th>
                  <th className="text-left p-2">Matchup</th>
                  <th className="text-center p-2">Ridge</th>
                  <th className="text-center p-2">XGBoost</th>
                  <th className="text-center p-2">FastAI</th>
                  <th className="text-center p-2">Ensemble</th>
                  <th className="text-center p-2">Consensus</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((comp, index) => (
                  <tr key={comp.game_id} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-medium">{comp.bowl_name}</td>
                    <td className="p-2">
                      <div className="text-sm">{comp.away_team} vs</div>
                      <div className="text-sm font-medium">{comp.home_team}</div>
                    </td>
                    <td className="p-2 text-center">
                      <div className="text-xs text-gray-600">
                        {comp.ridge_prediction.margin > 0 ? comp.home_team : comp.away_team}
                      </div>
                      <div className="font-medium">
                        {comp.ridge_prediction.margin > 0 ? '+' : ''}{comp.ridge_prediction.margin.toFixed(1)}
                      </div>
                      <Badge variant="outline" className="mt-1">
                        {(comp.ridge_prediction.home_win_probability * 100).toFixed(0)}%
                      </Badge>
                    </td>
                    <td className="p-2 text-center">
                      <div className="text-xs text-gray-600">
                        {comp.xgb_prediction.margin > 0 ? comp.home_team : comp.away_team}
                      </div>
                      <div className="font-medium">
                        {comp.xgb_prediction.margin > 0 ? '+' : ''}{comp.xgb_prediction.margin.toFixed(1)}
                      </div>
                      <Badge variant="outline" className="mt-1">
                        {(comp.xgb_prediction.home_win_probability * 100).toFixed(0)}%
                      </Badge>
                    </td>
                    <td className="p-2 text-center">
                      <div className="text-xs text-gray-600">
                        {comp.fastai_prediction.margin > 0 ? comp.home_team : comp.away_team}
                      </div>
                      <div className="font-medium">
                        {comp.fastai_prediction.margin > 0 ? '+' : ''}{comp.fastai_prediction.margin.toFixed(1)}
                      </div>
                      <Badge variant="outline" className="mt-1">
                        {(comp.fastai_prediction.home_win_probability * 100).toFixed(0)}%
                      </Badge>
                    </td>
                    <td className="p-2 text-center bg-purple-50">
                      <div className="text-xs text-purple-600 font-medium">
                        {comp.ensemble_prediction.margin > 0 ? comp.home_team : comp.away_team}
                      </div>
                      <div className="font-bold text-purple-600">
                        {comp.ensemble_prediction.margin > 0 ? '+' : ''}{comp.ensemble_prediction.margin.toFixed(1)}
                      </div>
                      <Badge className="mt-1 bg-purple-600">
                        {(comp.ensemble_prediction.home_win_probability * 100).toFixed(0)}%
                      </Badge>
                    </td>
                    <td className="p-2 text-center">
                      {(() => {
                        const predictions = [
                          comp.ridge_prediction.home_win_probability,
                          comp.xgb_prediction.home_win_probability,
                          comp.fastai_prediction.home_win_probability
                        ];
                        const avgProb = predictions.reduce((a, b) => a + b, 0) / predictions.length;
                        const stdDev = Math.sqrt(
                          predictions.reduce((sum, p) => sum + Math.pow(p - avgProb, 2), 0) / predictions.length
                        );

                        return (
                          <Badge
                            variant={stdDev < 0.1 ? "default" : stdDev < 0.2 ? "secondary" : "destructive"}
                          >
                            {stdDev < 0.1 ? 'High' : stdDev < 0.2 ? 'Med' : 'Low'}
                          </Badge>
                        );
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}