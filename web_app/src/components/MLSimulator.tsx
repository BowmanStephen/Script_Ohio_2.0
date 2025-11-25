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
import { PredictionsTableView } from './simulator/PredictionsTableView';
import { ATSView } from './simulator/ATSView';
import { ErrorBoundary } from './ErrorBoundary';
import { week14Games } from '../data/week14Games';
import { predictGame, calculateWCFLPoints, modelPerformance } from '../utils/predictionLogic';
import { loadPredictionsData, checkApiHealth } from '../utils/apiClient';
import { loadLiveATSData } from '../utils/apiClient';
import { Game, FeatureWeights as FeatureWeightsType, TrainingHistory, ModelMetricsState, ATSAnalysis } from '../types';
import { APP_CONSTANTS } from '../config/constants';

// Helper function to format percentages consistently
const formatPercent = (value: string | number | undefined): string => {
    const parsed = typeof value === 'number' ? value : parseFloat(value || '0');
    const clamped = Math.min(100, Math.max(0, parsed));
    return clamped.toFixed(1);
};

const MLSimulator: React.FC = () => {
    const [selectedModel, setSelectedModel] = useState<string>(APP_CONSTANTS.UI.DEFAULT_MODEL);
    const [featureWeights, setFeatureWeights] = useState<FeatureWeightsType>(
        APP_CONSTANTS.FEATURE_WEIGHTS.DEFAULT
    );
    const [tempoAdjusted, setTempoAdjusted] = useState<boolean>(true);
    const [trainingProgress, setTrainingProgress] = useState<number>(0);
    const [isTraining, setIsTraining] = useState<boolean>(false);
    const [modelMetrics, setModelMetrics] = useState<ModelMetricsState | null>(null);
    const [predictions, setPredictions] = useState<Game[]>([]);
    const [wcflPicks, setWcflPicks] = useState<Game[]>([]);
    const [gameCount, setGameCount] = useState<number>(week14Games.length);
    const [trainingHistory, setTrainingHistory] = useState<TrainingHistory[]>([]);
    const [selectedView, setSelectedView] = useState<string>('predictions');
    const [error, setError] = useState<string | null>(null);
    const [atsData, setAtsData] = useState<ATSAnalysis[]>([]);
    const [atsLoading, setAtsLoading] = useState<boolean>(false);
    const [atsError, setAtsError] = useState<string | null>(null);

    // API integration state
    const [isApiAvailable, setIsApiAvailable] = useState<boolean>(false);
    const [apiLoading, setApiLoading] = useState<boolean>(false);
    const [apiError, setApiError] = useState<string | null>(null);
    const [dataSource, setDataSource] = useState<'live' | 'static'>('static');

    // Check API availability on mount
    React.useEffect(() => {
        const checkApi = async () => {
            setApiLoading(true);
            setApiError(null);

            try {
                const available = await checkApiHealth();
                setIsApiAvailable(available);

                if (available) {
                    setDataSource('live');
                    console.log('✅ Live API server available');
                } else {
                    setDataSource('static');
                    console.log('📊 Using static data (API not available)');
                }
            } catch (err) {
                console.warn('API health check failed:', err);
                setIsApiAvailable(false);
                setDataSource('static');
                setApiError('API server not available');
            } finally {
                setApiLoading(false);
            }
        };

        checkApi();
    }, []);

    // Load real prediction outputs on mount
    React.useEffect(() => {
        const loadPredictions = async () => {
            try {
                const loadedGames = await loadPredictionsData();
                setPredictions(loadedGames);
                setWcflPicks(calculateWCFLPoints(loadedGames));
                setGameCount(loadedGames.length);
                setModelMetrics({
                    accuracy: modelPerformance.consensus.accuracy,
                    mae: modelPerformance.consensus.mae,
                    rmse: modelPerformance.consensus.mae * 1.3,
                    r2: 0.5
                });
                setError(null);
            } catch (loadErr) {
                console.error('Error loading predictions:', loadErr);
                setError('Failed to load predictions. You can still run the simulator to generate estimates.');
            }
        };

        loadPredictions();
    }, []);

    // Load ATS data on component mount (now uses live API with fallback)
    React.useEffect(() => {
        const loadATS = async () => {
            setAtsLoading(true);
            setAtsError(null);
            try {
                // The loadLiveATSData function handles API fallback to static data automatically
                const data = await loadLiveATSData();
                setAtsData(data);
                if (dataSource === 'live') {
                    console.log('✅ ATS data loaded from live API');
                } else {
                    console.log('📊 ATS data loaded from static files');
                }
            } catch (error) {
                console.error('Error loading ATS data:', error);
                setAtsError(error instanceof Error ? error.message : 'Failed to load ATS data. Please try again later.');
            } finally {
                setAtsLoading(false);
            }
        };
        loadATS();
    }, [dataSource]);

    const handleTrain = () => {
        try {
            setError(null);
            setIsTraining(true);
            setTrainingProgress(0);

            const history: TrainingHistory[] = [];
            let interval: NodeJS.Timeout | null = null;

            interval = setInterval(() => {
                try {
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
                            if (interval) {
                                clearInterval(interval);
                                interval = null;
                            }
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
                            let newPredictions: Game[] = [];
                            try {
                                newPredictions = week14Games.map(game => ({
                                    ...game,
                                    week: game.week ?? APP_CONSTANTS.CURRENT_WEEK,
                                    prediction: predictGame(game, selectedModel, featureWeights, tempoAdjusted),
                                    id: game.id
                                }));
                                setPredictions(newPredictions);
                                setGameCount(newPredictions.length);
                            } catch (err) {
                                console.error('Error generating predictions:', err);
                                setError('Failed to generate predictions. Please try again.');
                            }

                            // Calculate WCFL picks
                            if (newPredictions.length > 0) {
                                try {
                                    const picks = calculateWCFLPoints(newPredictions);
                                    setWcflPicks(picks);
                                } catch (err) {
                                    console.error('Error calculating WCFL points:', err);
                                    setError('Failed to calculate WCFL points. Please try again.');
                                }
                            }
                        }

                        return next;
                    });
                } catch (err) {
                    // Catch any errors in the interval callback
                    console.error('Error in training interval callback:', err);
                    if (interval) {
                        clearInterval(interval);
                        interval = null;
                    }
                    setIsTraining(false);
                    setTrainingProgress(0);
                    setError('Training simulation encountered an error. Please try again.');
                }
            }, APP_CONSTANTS.UI.TRAINING_INTERVAL);
        } catch (err) {
            console.error('Error in training simulation:', err);
            setError('Training simulation failed. Please try again.');
            setIsTraining(false);
            setTrainingProgress(0);
        }
    };

    const handleWeightChange = (metric: string, value: number) => {
        try {
            // Validate input - value is normalized (0-1) from FeatureWeights slider
            if (isNaN(value) || value < 0 || value > 1) {
                setError(`Invalid weight value: ${(value * 100).toFixed(1)}%. Must be between 0% and 100%.`);
                return;
            }

            const newWeights = { ...featureWeights, [metric]: value };
            const total = Object.values(newWeights).reduce((a, b) => a + b, 0);

        // Normalize weights to sum to 1.0 (100%)
        if (Math.abs(total - 1.0) > 0.001) {
            const scale = 1.0 / total;
            Object.keys(newWeights).forEach(key => {
                newWeights[key] = newWeights[key] * scale;
            });
            // Adjust last item to ensure exactly 1.0
            const keys = Object.keys(newWeights);
            const currentTotal = Object.values(newWeights).reduce((a, b) => a + b, 0);
            newWeights[keys[keys.length - 1]] += 1.0 - currentTotal;
        }

        setFeatureWeights(newWeights);
        setError(null);
        } catch (err) {
            console.error('Error updating feature weights:', err);
            setError('Failed to update feature weights. Please try again.');
        }
    };

    // Value opportunities analysis
    const valueOpportunities = useMemo(() => {
        return predictions
            .filter(p => Math.abs(parseFloat(p.prediction?.lineValue || '0')) > 3)
            .sort((a, b) => Math.abs(parseFloat(b.prediction?.lineValue || '0')) - Math.abs(parseFloat(a.prediction?.lineValue || '0')))
            .slice(0, 10);
    }, [predictions]);

    return (
        <main className="dark w-full min-h-screen bg-background p-8 text-foreground">
            <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded">
                Skip to main content
            </a>
            <div id="main-content" className="max-w-7xl mx-auto">
                <Header
                    gameCount={gameCount}
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
                        gameCount={gameCount}
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

                {(predictions.length > 0 || atsData.length > 0) && (
                    <ErrorBoundary>
                        {selectedView === 'ats' && (
                            <ATSView
                                atsData={atsData}
                                isLoading={atsLoading}
                                error={atsError || undefined}
                            />
                        )}
                        {selectedView === 'wcfl' && <WCFLStrategyView wcflPicks={wcflPicks} />}
                        {selectedView === 'value' && <ValueOpportunitiesView valueOpportunities={valueOpportunities} />}
                        {selectedView === 'performance' && <ModelPerformanceView modelPerformance={modelPerformance} />}
                        {selectedView === 'predictions' && <PredictionsTableView predictions={predictions} />}
                    </ErrorBoundary>
                )}

                {predictions.length > 0 && (
                    <div className="mt-6 text-center">
                        <button
                            type="button"
                            onClick={() => {
                                try {
                                    const csvContent = "data:text/csv;charset=utf-8," +
                                        "Home,Away,Spread,Model Prediction,Line Value,Win Prob (%),WCFL Points\n" +
                                        wcflPicks.map(p => {
                                            const spread = Number.isInteger(p.spread) ? p.spread.toString() : p.spread.toFixed(1);
                                            const winProb = formatPercent(p.prediction?.confidence || '0');
                                            return `${p.home_team},${p.away_team},${spread},${p.prediction?.predictedMargin},${p.prediction?.lineValue},${winProb},${p.wcflPoints}`;
                                        }).join("\n");
                                    const encodedUri = encodeURI(csvContent);
                                    const link = document.createElement("a");
                                    link.setAttribute("href", encodedUri);
                                    link.setAttribute("download", APP_CONSTANTS.FILE_NAMES.WCFL_EXPORT(APP_CONSTANTS.CURRENT_WEEK));
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                } catch (err) {
                                    console.error('Error exporting CSV:', err);
                                    setError('Failed to export CSV. Please try again.');
                                }
                            }}
                            aria-label="Export WCFL picks to CSV file"
                            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-all shadow-lg shadow-blue-900/20 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                        >
                            📥 Export WCFL Picks to CSV
                        </button>
                    </div>
                )}

                {error && (
                    <div className="mt-4 p-4 bg-destructive/10 border border-destructive/50 rounded-lg text-destructive">
                        <p className="font-semibold">Error:</p>
                        <p>{error}</p>
                        <button
                            type="button"
                            onClick={() => setError(null)}
                            className="mt-2 text-sm underline"
                        >
                            Dismiss
                        </button>
                    </div>
                )}
            </div>
        </main>
    );
};

export default MLSimulator;
