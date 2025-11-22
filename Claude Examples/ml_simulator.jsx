import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Simplified ML simulation
const trainModel = (data, modelType) => {
  // Simulate different model behaviors
  const baseAccuracy = {
    'Ridge Regression': 0.68,
    'XGBoost': 0.72,
    'FastAI Neural Net': 0.70,
    'Ensemble': 0.75
  };
  
  return {
    accuracy: baseAccuracy[modelType] + (Math.random() * 0.05 - 0.025),
    mae: 8.5 + (Math.random() * 2 - 1),
    rmse: 11.2 + (Math.random() * 2 - 1),
    r2: 0.45 + (Math.random() * 0.1 - 0.05)
  };
};

const predictGame = (homeTeam, awayTeam, modelWeights) => {
  // Simulate prediction based on historical data patterns
  const eloWeight = modelWeights.elo / 100;
  const talentWeight = modelWeights.talent / 100;
  const epaWeight = modelWeights.epa / 100;
  
  // Mock calculation
  const homeFactor = (homeTeam.elo * eloWeight + homeTeam.talent * talentWeight + homeTeam.epa * 1000 * epaWeight);
  const awayFactor = (awayTeam.elo * eloWeight + awayTeam.talent * talentWeight + awayTeam.epa * 1000 * epaWeight);
  
  const predictedMargin = (homeFactor - awayFactor) / 50;
  const confidence = Math.min(95, Math.abs(predictedMargin) * 3 + 50);
  
  return {
    predictedMargin: predictedMargin.toFixed(1),
    confidence: confidence.toFixed(1),
    winner: predictedMargin > 0 ? homeTeam.name : awayTeam.name
  };
};

const games = [
  {
    id: 1,
    home: { name: "Ohio State", elo: 1903, talent: 975.62, epa: 0.2509 },
    away: { name: "Indiana", elo: 1797, talent: 752.31, epa: 0.2113 },
    spread: -10.5
  },
  {
    id: 2,
    home: { name: "Oregon", elo: 1940, talent: 934.95, epa: 0.2818 },
    away: { name: "Washington", elo: 1754, talent: 720.56, epa: 0.0851 },
    spread: -19.5
  },
  {
    id: 3,
    home: { name: "Texas", elo: 1917, talent: 978.67, epa: 0.2456 },
    away: { name: "Kentucky", elo: 1532, talent: 697.03, epa: -0.0326 },
    spread: -20.5
  },
  {
    id: 4,
    home: { name: "Alabama", elo: 1838, talent: 948.46, epa: 0.1968 },
    away: { name: "Auburn", elo: 1697, talent: 650.86, epa: 0.0438 },
    spread: -10.5
  },
  {
    id: 5,
    home: { name: "Notre Dame", elo: 1834, talent: 828.32, epa: 0.2179 },
    away: { name: "Army", elo: 1651, talent: 509.49, epa: 0.1142 },
    spread: -14.5
  }
];

export default function MLSimulator() {
  const [selectedModel, setSelectedModel] = useState('Ensemble');
  const [modelWeights, setModelWeights] = useState({
    elo: 40,
    talent: 35,
    epa: 25
  });
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [isTraining, setIsTraining] = useState(false);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [trainingHistory, setTrainingHistory] = useState([]);

  const handleTrain = () => {
    setIsTraining(true);
    setTrainingProgress(0);
    
    const history = [];
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        const next = prev + 1;
        
        // Simulate training metrics over epochs
        if (next <= 100) {
          history.push({
            epoch: next,
            loss: 12 * Math.exp(-next / 30) + 2 + Math.random() * 0.5,
            val_loss: 13 * Math.exp(-next / 28) + 2.5 + Math.random() * 0.7,
            accuracy: 50 + (25 * (1 - Math.exp(-next / 25))) + Math.random() * 2
          });
        }
        
        if (next >= 100) {
          clearInterval(interval);
          setIsTraining(false);
          
          const metrics = trainModel([], selectedModel);
          setModelMetrics(metrics);
          setTrainingHistory(history);
          
          // Generate predictions for all games
          const newPredictions = games.map(game => ({
            ...game,
            prediction: predictGame(game.home, game.away, modelWeights)
          }));
          setPredictions(newPredictions);
        }
        
        return next;
      });
    }, 20);
  };

  const handleWeightChange = (metric, value) => {
    const newWeights = { ...modelWeights, [metric]: value };
    const total = newWeights.elo + newWeights.talent + newWeights.epa;
    
    // Normalize to 100
    if (total !== 100) {
      const scale = 100 / total;
      newWeights.elo = Math.round(newWeights.elo * scale);
      newWeights.talent = Math.round(newWeights.talent * scale);
      newWeights.epa = 100 - newWeights.elo - newWeights.talent;
    }
    
    setModelWeights(newWeights);
  };

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            🤖 ML Prediction Simulator
          </h1>
          <p className="text-xl text-blue-300">Interactive Model Training & Prediction</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Model Selection */}
          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Select Model</h3>
            <div className="space-y-3">
              {['Ridge Regression', 'XGBoost', 'FastAI Neural Net', 'Ensemble'].map(model => (
                <button
                  key={model}
                  onClick={() => setSelectedModel(model)}
                  className={`w-full p-3 rounded-lg font-semibold transition ${
                    selectedModel === model
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {model}
                </button>
              ))}
            </div>
          </div>

          {/* Feature Weights */}
          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Feature Weights</h3>
            <div className="space-y-4">
              <div>
                <label className="text-white font-semibold mb-2 block">
                  ELO Rating: {modelWeights.elo}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={modelWeights.elo}
                  onChange={(e) => handleWeightChange('elo', parseInt(e.target.value))}
                  className="w-full"
                  disabled={isTraining}
                />
              </div>
              <div>
                <label className="text-white font-semibold mb-2 block">
                  Talent Composite: {modelWeights.talent}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={modelWeights.talent}
                  onChange={(e) => handleWeightChange('talent', parseInt(e.target.value))}
                  className="w-full"
                  disabled={isTraining}
                />
              </div>
              <div>
                <label className="text-white font-semibold mb-2 block">
                  EPA Performance: {modelWeights.epa}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={modelWeights.epa}
                  onChange={(e) => handleWeightChange('epa', parseInt(e.target.value))}
                  className="w-full"
                  disabled={isTraining}
                />
              </div>
              <div className="text-sm text-slate-400 text-center">
                Total: {modelWeights.elo + modelWeights.talent + modelWeights.epa}%
              </div>
            </div>
          </div>

          {/* Training Control */}
          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Training Control</h3>
            <button
              onClick={handleTrain}
              disabled={isTraining}
              className={`w-full py-4 rounded-lg font-bold text-xl transition ${
                isTraining
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              {isTraining ? '🔄 Training...' : '🚀 Train Model'}
            </button>
            
            {isTraining && (
              <div className="mt-4">
                <div className="w-full bg-slate-700 rounded-full h-4 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-green-500 h-full transition-all duration-300"
                    style={{ width: `${trainingProgress}%` }}
                  />
                </div>
                <p className="text-center text-white mt-2">{trainingProgress}% Complete</p>
              </div>
            )}
            
            {modelMetrics && !isTraining && (
              <div className="mt-4 space-y-2 text-white">
                <div className="flex justify-between p-2 bg-slate-700 rounded">
                  <span>Accuracy:</span>
                  <span className="font-bold">{(modelMetrics.accuracy * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-700 rounded">
                  <span>MAE:</span>
                  <span className="font-bold">{modelMetrics.mae.toFixed(2)}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-700 rounded">
                  <span>RMSE:</span>
                  <span className="font-bold">{modelMetrics.rmse.toFixed(2)}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-700 rounded">
                  <span>R² Score:</span>
                  <span className="font-bold">{modelMetrics.r2.toFixed(3)}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Training Progress Chart */}
        {trainingHistory.length > 0 && (
          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl mb-6">
            <h3 className="text-2xl font-bold text-white mb-4">Training Progress</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trainingHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="epoch" stroke="#9ca3af" label={{ value: 'Epoch', position: 'bottom', fill: '#9ca3af' }} />
                <YAxis stroke="#9ca3af" label={{ value: 'Loss', angle: -90, position: 'left', fill: '#9ca3af' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Legend />
                <Line type="monotone" dataKey="loss" stroke="#3b82f6" strokeWidth={2} name="Training Loss" dot={false} />
                <Line type="monotone" dataKey="val_loss" stroke="#ef4444" strokeWidth={2} name="Validation Loss" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Predictions */}
        {predictions.length > 0 && (
          <div className="bg-slate-800 rounded-xl p-6 shadow-2xl">
            <h3 className="text-2xl font-bold text-white mb-6">🎯 Model Predictions</h3>
            <div className="space-y-4">
              {predictions.map(game => (
                <div key={game.id} className="bg-slate-700 rounded-lg p-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                    <div className="text-center">
                      <div className="text-xl font-bold text-blue-400">{game.home.name}</div>
                      <div className="text-sm text-slate-400">ELO: {game.home.elo}</div>
                      <div className="text-sm text-slate-400">EPA: {game.home.epa.toFixed(3)}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white">VS</div>
                      <div className="text-sm text-slate-400 mt-1">Line: {game.spread}</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-xl font-bold text-red-400">{game.away.name}</div>
                      <div className="text-sm text-slate-400">ELO: {game.away.elo}</div>
                      <div className="text-sm text-slate-400">EPA: {game.away.epa.toFixed(3)}</div>
                    </div>
                    
                    <div className="bg-slate-800 rounded-lg p-4">
                      <div className="text-green-400 font-bold text-lg mb-1">
                        Winner: {game.prediction.winner}
                      </div>
                      <div className="text-white text-sm">
                        Predicted Margin: {game.prediction.predictedMargin}
                      </div>
                      <div className="text-white text-sm">
                        Model Spread: {(parseFloat(game.prediction.predictedMargin) - game.spread).toFixed(1)}
                      </div>
                      <div className="mt-2">
                        <div className="text-xs text-slate-400 mb-1">Confidence</div>
                        <div className="w-full bg-slate-600 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-yellow-500 to-green-500 h-2 rounded-full"
                            style={{ width: `${game.prediction.confidence}%` }}
                          />
                        </div>
                        <div className="text-xs text-slate-300 mt-1 text-center">
                          {game.prediction.confidence}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
