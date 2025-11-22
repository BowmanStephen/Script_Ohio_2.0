import React, { useState, useMemo } from 'react';
import { Header } from './simulator/Header';
import { ViewSelector } from './simulator/ViewSelector';
import { ModelSelection } from './simulator/ModelSelection';
import { FeatureWeights } from './simulator/FeatureWeights';
import { AdvancedSettings } from './simulator/AdvancedSettings';
import { TrainingControl } from './simulator/TrainingControl';
import { TrainingProgressChart } from './simulator/TrainingProgressChart';
import { WCFLStrategyView } from './simulator/WCFLStrategyView';
import { ValueOpportunitiesView } from './simulator/ValueOpportunitiesView';
import { ModelPerformanceView } from './simulator/ModelPerformanceView';
import { PredictionsView } from './simulator/PredictionsView';
import { week13Games } from '../data/week13Games';
import { predictGame, calculateWCFLPoints, modelPerformance } from '../utils/predictionLogic';
import { Game, FeatureWeights as FeatureWeightsType, TrainingHistory, ModelMetricsState } from '../types';

const MLSimulator: React.FC = () => {
    const [selectedModel, setSelectedModel] = useState<string>('Ensemble');
    const [featureWeights, setFeatureWeights] = useState<FeatureWeightsType>({
        elo: 25,
        talent: 25,
        epa: 35,
        success: 15
    });
    const [tempoAdjusted, setTempoAdjusted] = useState<boolean>(true);
    const [trainingProgress, setTrainingProgress] = useState<number>(0);
    const [isTraining, setIsTraining] = useState<boolean>(false);
    const [modelMetrics, setModelMetrics] = useState<ModelMetricsState | null>(null);
    const [predictions, setPredictions] = useState<Game[]>([]);
    const [wcflPicks, setWcflPicks] = useState<Game[]>([]);
    const [trainingHistory, setTrainingHistory] = useState<TrainingHistory[]>([]);
    const [selectedView, setSelectedView] = useState<string>('predictions');

    const handleTrain = () => {
        setIsTraining(true);
        setTrainingProgress(0);

        const history: TrainingHistory[] = [];
        const interval = setInterval(() => {
            setTrainingProgress(prev => {
                const next = prev + 1;

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

                    // Get model performance metrics
                    const perf = modelPerformance[selectedModel.toLowerCase().replace(/\s+/g, '')] || modelPerformance.xgboost;
                    setModelMetrics({
                        accuracy: perf.accuracy + (Math.random() * 0.04 - 0.02),
                        mae: perf.mae + (Math.random() * 1 - 0.5),
                        rmse: perf.mae * 1.3 + (Math.random() * 1 - 0.5),
                        r2: 0.45 + (Math.random() * 0.1 - 0.05)
                    });
                    setTrainingHistory(history);

                    // Generate predictions for all games
                    const newPredictions = week13Games.map(game => ({
                        ...game,
                        prediction: predictGame(game, selectedModel, featureWeights, tempoAdjusted)
                    }));
                    setPredictions(newPredictions);

                    // Calculate WCFL picks
                    const picks = calculateWCFLPoints(newPredictions);
                    setWcflPicks(picks);
                }

                return next;
            });
        }, 20);
    };

    const handleWeightChange = (metric: string, value: number) => {
        const newWeights = { ...featureWeights, [metric]: value };
        const total = Object.values(newWeights).reduce((a, b) => a + b, 0);

        if (total !== 100) {
            const scale = 100 / total;
            Object.keys(newWeights).forEach(key => {
                newWeights[key] = Math.round(newWeights[key] * scale);
            });
            // Adjust last item to ensure exactly 100
            const keys = Object.keys(newWeights);
            const currentTotal = Object.values(newWeights).reduce((a, b) => a + b, 0);
            newWeights[keys[keys.length - 1]] += 100 - currentTotal;
        }

        setFeatureWeights(newWeights);
    };

    // Value opportunities analysis
    const valueOpportunities = useMemo(() => {
        return predictions
            .filter(p => Math.abs(parseFloat(p.prediction?.lineValue || '0')) > 3)
            .sort((a, b) => Math.abs(parseFloat(b.prediction?.lineValue || '0')) - Math.abs(parseFloat(a.prediction?.lineValue || '0')))
            .slice(0, 10);
    }, [predictions]);

    return (
        <div className="dark w-full min-h-screen bg-background p-8 text-foreground">
            <div className="max-w-7xl mx-auto">
                <Header
                    gameCount={week13Games.length}
                    tempoAdjusted={tempoAdjusted}
                    selectedModel={selectedModel}
                    wcflPicksCount={wcflPicks.length}
                />

                <ViewSelector selectedView={selectedView} onSelectView={setSelectedView} />

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
                    <ModelSelection
                        selectedModel={selectedModel}
                        onSelectModel={setSelectedModel}
                        modelPerformance={modelPerformance}
                    />

                    <FeatureWeights
                        weights={featureWeights}
                        onWeightChange={handleWeightChange}
                        isTraining={isTraining}
                    />

                    <AdvancedSettings
                        tempoAdjusted={tempoAdjusted}
                        onToggleTempo={() => setTempoAdjusted(!tempoAdjusted)}
                        gameCount={week13Games.length}
                        featureCount={86}
                    />

                    <TrainingControl
                        isTraining={isTraining}
                        trainingProgress={trainingProgress}
                        onTrain={handleTrain}
                        modelMetrics={modelMetrics}
                    />
                </div>

                <TrainingProgressChart history={trainingHistory} />

                {predictions.length > 0 && (
                    <>
                        {selectedView === 'wcfl' && <WCFLStrategyView wcflPicks={wcflPicks} />}
                        {selectedView === 'value' && <ValueOpportunitiesView valueOpportunities={valueOpportunities} />}
                        {selectedView === 'performance' && <ModelPerformanceView modelPerformance={modelPerformance} />}
                        {selectedView === 'predictions' && <PredictionsView predictions={predictions} />}
                    </>
                )}

                {predictions.length > 0 && (
                    <div className="mt-6 text-center">
                        <button
                            onClick={() => {
                                const csvContent = "data:text/csv;charset=utf-8," +
                                    "Home,Away,Spread,Model Prediction,Line Value,Confidence,WCFL Points\n" +
                                    wcflPicks.map(p =>
                                        `${p.home_team},${p.away_team},${p.spread},${p.prediction?.predictedMargin},${p.prediction?.lineValue},${p.prediction?.confidence},${p.wcflPoints}`
                                    ).join("\n");
                                const encodedUri = encodeURI(csvContent);
                                const link = document.createElement("a");
                                link.setAttribute("href", encodedUri);
                                link.setAttribute("download", "wcfl_week13_picks.csv");
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                            }}
                            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-all shadow-lg shadow-blue-900/20"
                        >
                            📥 Export WCFL Picks to CSV
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MLSimulator;
