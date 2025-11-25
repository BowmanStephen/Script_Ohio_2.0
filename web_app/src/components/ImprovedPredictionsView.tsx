import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { AlertCircle, CheckCircle, TrendingUp, Users } from 'lucide-react';

interface ImprovedPrediction {
  game_id: string;
  season: number;
  week: number;
  home_team: string;
  away_team: string;
  start_date: string;
  spread: number;
  predicted_margin: number;
  home_win_probability: number;
  away_win_probability: number;
  confidence: number;
  confidence_level: string;
  model_agreement: string;
  prediction_valid: boolean;
  predicted_winner: string;
}

interface ImprovedPredictionsViewProps {
  week?: number;
}

export default function ImprovedPredictionsView({ week = 14 }: ImprovedPredictionsViewProps) {
  const [predictions, setPredictions] = useState<ImprovedPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'valid' | 'high-confidence'>('valid');

  useEffect(() => {
    loadImprovedPredictions();
  }, [week]);

  const loadImprovedPredictions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/week14_improved_predictions.json`);
      if (response.ok) {
        const data = await response.json();
        setPredictions(data);
      }
    } catch (error) {
      console.error('Error loading improved predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-green-500';
      case 'moderate': return 'bg-yellow-500';
      case 'low': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getAgreementColor = (agreement: string) => {
    switch (agreement) {
      case 'high': return 'text-green-600';
      case 'moderate': return 'text-yellow-600';
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getFilteredPredictions = () => {
    switch (filter) {
      case 'valid':
        return predictions.filter(p => p.prediction_valid);
      case 'high-confidence':
        return predictions.filter(p => p.prediction_valid && p.confidence_level === 'high');
      default:
        return predictions;
    }
  };

  const filteredPredictions = getFilteredPredictions();

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading improved predictions...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Improvement Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Improved Week {week} Predictions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {filteredPredictions.length}
              </div>
              <div className="text-sm text-gray-600">Reliable Predictions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {predictions.filter(p => p.confidence_level === 'high').length}
              </div>
              <div className="text-sm text-gray-600">High Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {predictions.filter(p => p.model_agreement === 'high').length}
              </div>
              <div className="text-sm text-gray-600">Model Agreement</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.round(filteredPredictions.reduce((sum, p) => sum + Math.abs(p.predicted_margin), 0) / filteredPredictions.length)}
              </div>
              <div className="text-sm text-gray-600">Avg Margin</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded ${filter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              All Predictions ({predictions.length})
            </button>
            <button
              onClick={() => setFilter('valid')}
              className={`px-4 py-2 rounded ${filter === 'valid' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              Valid Only ({predictions.filter(p => p.prediction_valid).length})
            </button>
            <button
              onClick={() => setFilter('high-confidence')}
              className={`px-4 py-2 rounded ${filter === 'high-confidence' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              High Confidence ({predictions.filter(p => p.confidence_level === 'high').length})
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Predictions List */}
      <div className="grid gap-4">
        {filteredPredictions.map((prediction) => (
          <Card key={prediction.game_id} className={`relative ${!prediction.prediction_valid ? 'opacity-75' : ''}`}>
            {!prediction.prediction_valid && (
              <div className="absolute top-2 right-2">
                <Badge variant="outline" className="text-orange-600 border-orange-600">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Low Confidence
                </Badge>
              </div>
            )}

            <CardContent className="pt-6">
              {/* Match Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">
                    {prediction.away_team} @ {prediction.home_team}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {new Date(prediction.start_date).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600">
                    {prediction.predicted_winner}
                  </div>
                  <div className="text-sm text-gray-600">
                    Predicted Winner
                  </div>
                </div>
              </div>

              {/* Prediction Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Win Probability */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Win Probability</span>
                    <span className="text-sm text-gray-600">
                      {Math.round(prediction.home_win_probability * 100)}% / {Math.round(prediction.away_win_probability * 100)}%
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>{prediction.home_team}</span>
                      <span>{Math.round(prediction.home_win_probability * 100)}%</span>
                    </div>
                    <Progress
                      value={prediction.home_win_probability * 100}
                      className="h-2"
                    />
                    <div className="flex justify-between text-xs">
                      <span>{prediction.away_team}</span>
                      <span>{Math.round(prediction.away_win_probability * 100)}%</span>
                    </div>
                  </div>
                </div>

                {/* Margin Prediction */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Predicted Margin</span>
                    <span className="text-sm font-bold">
                      {prediction.predicted_margin > 0 ? '+' : ''}{prediction.predicted_margin.toFixed(1)}
                    </span>
                  </div>
                  {prediction.spread && (
                    <div className="text-xs text-gray-600">
                      Vegas Spread: {prediction.spread > 0 ? '+' : ''}{prediction.spread}
                    </div>
                  )}
                  {prediction.spread && Math.abs(prediction.predicted_margin - prediction.spread) > 10 && (
                    <Badge variant="outline" className="text-xs text-orange-600 border-orange-600">
                      Large vs Spread
                    </Badge>
                  )}
                </div>

                {/* Confidence & Agreement */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Confidence</span>
                    <Badge className={getConfidenceColor(prediction.confidence_level)}>
                      {prediction.confidence_level}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Confidence Score</span>
                      <span>{Math.round(prediction.confidence * 100)}%</span>
                    </div>
                    <Progress
                      value={prediction.confidence * 100}
                      className="h-2"
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Model Agreement</span>
                    <span className={`text-sm font-medium ${getAgreementColor(prediction.model_agreement)}`}>
                      {prediction.model_agreement}
                    </span>
                  </div>
                </div>
              </div>

              {/* Validation Status */}
              {prediction.prediction_valid && (
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center gap-2 text-sm text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span>Prediction passed all validation checks</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredPredictions.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No predictions found</h3>
            <p className="text-gray-600">
              {filter === 'high-confidence'
                ? 'No high confidence predictions available for this week.'
                : 'Try adjusting the filter to see more predictions.'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}