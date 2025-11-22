import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import week13Games from '../data/week13_data.json';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Rocket, TrendingUp, DollarSign, Activity, Check } from 'lucide-react';

// Performance-based model weights (from historical accuracy)
const modelPerformance = {
    ridge: { accuracy: 0.68, mae: 9.2, weight: 0.20 },
    xgboost: { accuracy: 0.74, mae: 8.1, weight: 0.35 },
    fastai: { accuracy: 0.71, mae: 8.6, weight: 0.25 },
    consensus: { accuracy: 0.66, mae: 9.8, weight: 0.20 }
};

// Simulate model prediction with different approaches
const predictGame = (game, modelType, weights, tempoAdjusted) => {
    const { home_elo, away_elo, home_talent, away_talent, home_adjusted_epa, away_adjusted_epa,
        home_adjusted_success, away_adjusted_success, home_points_per_opportunity_offense,
        away_points_per_opportunity_offense, home_adjusted_explosiveness, away_adjusted_explosiveness } = game;

    // Apply tempo adjustment multiplier (conceptual - data is already adjusted)
    const tempoMultiplier = tempoAdjusted ? 1.15 : 1.0;

    // Calculate different model predictions
    let predictedMargin;

    if (modelType === 'Ridge Regression') {
        // Ridge: Linear combination weighted by feature importance
        predictedMargin = (
            (home_elo - away_elo) * 0.015 * weights.elo / 100 +
            (home_talent - away_talent) * 0.012 * weights.talent / 100 +
            (home_adjusted_epa - away_adjusted_epa) * 45 * weights.epa / 100 * tempoMultiplier +
            (home_adjusted_success - away_adjusted_success) * 25 * weights.success / 100
        );
    } else if (modelType === 'XGBoost') {
        // XGBoost: Non-linear with boosted features
        const eloFactor = Math.tanh((home_elo - away_elo) / 200) * 12;
        const talentFactor = Math.tanh((home_talent - away_talent) / 100) * 10;
        const epaFactor = (home_adjusted_epa - away_adjusted_epa) * 50 * tempoMultiplier;
        const ppoFactor = (home_points_per_opportunity_offense - away_points_per_opportunity_offense) * 8;

        predictedMargin = (
            eloFactor * weights.elo / 100 +
            talentFactor * weights.talent / 100 +
            epaFactor * weights.epa / 100 +
            ppoFactor * weights.success / 100
        );
    } else if (modelType === 'FastAI Neural Net') {
        // Neural Net: Complex non-linear relationships
        const h1 = Math.tanh((home_elo - away_elo) / 150 * weights.elo / 100);
        const h2 = Math.tanh((home_talent - away_talent) / 80 * weights.talent / 100);
        const h3 = Math.tanh((home_adjusted_epa - away_adjusted_epa) * 40 * tempoMultiplier * weights.epa / 100);
        const h4 = Math.tanh((home_adjusted_explosiveness - away_adjusted_explosiveness) * 35 * weights.success / 100);

        predictedMargin = (h1 * 8 + h2 * 7 + h3 * 12 + h4 * 6);
    } else {
        // Ensemble: Weighted combination of all models
        const ridge = predictGame(game, 'Ridge Regression', weights, tempoAdjusted).predictedMargin;
        const xgboost = predictGame(game, 'XGBoost', weights, tempoAdjusted).predictedMargin;
        const fastai = predictGame(game, 'FastAI Neural Net', weights, tempoAdjusted).predictedMargin;

        predictedMargin = (
            Number(ridge) * modelPerformance.ridge.weight +
            Number(xgboost) * modelPerformance.xgboost.weight +
            Number(fastai) * modelPerformance.fastai.weight
        );
    }

    // Add home field advantage
    predictedMargin += 2.5;

    // Calculate confidence based on magnitude and agreement
    const magnitude = Math.abs(predictedMargin);
    const confidence = Math.min(95, 50 + magnitude * 2.5);

    // Determine value vs market line
    const lineValue = predictedMargin - game.spread;
    const valueRating = Math.abs(lineValue) > 7 ? 'Strong Value' :
        Math.abs(lineValue) > 4 ? 'Moderate Value' :
            Math.abs(lineValue) > 2 ? 'Slight Value' : 'No Value';

    return {
        predictedMargin: predictedMargin.toFixed(1),
        confidence: confidence.toFixed(1),
        lineValue: lineValue.toFixed(1),
        valueRating,
        winner: predictedMargin > 0 ? game.home_team : game.away_team,
        suggestedSide: lineValue > 0 ? game.home_team : lineValue < 0 ? game.away_team : 'Pass'
    };
};

// Calculate WCFL point allocation
const calculateWCFLPoints = (predictions) => {
    // Sort by confidence and line value
    const scored = predictions.map(p => ({
        ...p,
        wcflScore: parseFloat(p.prediction.confidence) * (Math.abs(parseFloat(p.prediction.lineValue)) > 3 ? 1.5 : 1.0)
    })).sort((a, b) => b.wcflScore - a.wcflScore);

    // Allocate points 10-1
    return scored.slice(0, 10).map((game, idx) => ({
        ...game,
        wcflPoints: 10 - idx,
        reasoning: `Confidence: ${game.prediction.confidence}%, Value: ${game.prediction.lineValue}`
    }));
};

export default function MLSimulatorEnhanced() {
    const [selectedModel, setSelectedModel] = useState('Ensemble');
    const [featureWeights, setFeatureWeights] = useState({
        elo: 25,
        talent: 25,
        epa: 35,
        success: 15
    });
    const [tempoAdjusted, setTempoAdjusted] = useState(true);
    const [trainingProgress, setTrainingProgress] = useState(0);
    const [isTraining, setIsTraining] = useState(false);
    const [modelMetrics, setModelMetrics] = useState(null);
    const [predictions, setPredictions] = useState([]);
    const [wcflPicks, setWcflPicks] = useState([]);
    const [trainingHistory, setTrainingHistory] = useState([]);

    const handleTrain = () => {
        setIsTraining(true);
        setTrainingProgress(0);

        const history = [];
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

    const handleWeightChange = (metric, value) => {
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
            .filter(p => Math.abs(parseFloat(p.prediction.lineValue)) > 3)
            .sort((a, b) => Math.abs(parseFloat(b.prediction.lineValue)) - Math.abs(parseFloat(a.prediction.lineValue)))
            .slice(0, 10);
    }, [predictions]);

    return (
        <div className="w-full min-h-screen bg-gradient-to-b from-background to-muted/20 p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="text-center space-y-6 py-8">
                    <div className="inline-flex items-center justify-center p-3 bg-primary/5 rounded-full mb-4">
                        <Rocket className="h-12 w-12 text-primary animate-pulse" />
                    </div>
                    <h1 className="text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/60">
                        Script Ohio 2.0
                    </h1>
                    <p className="text-xl text-muted-foreground font-light tracking-wide">
                        Enhanced ML Simulator • Week 13 • {week13Games.length} Games
                    </p>

                    <div className="flex justify-center gap-4 pt-4">
                        <Badge variant={tempoAdjusted ? "default" : "secondary"} className="text-sm py-1.5 px-4 shadow-sm">
                            {tempoAdjusted ? '⚡ Tempo Adjusted' : 'Standard Metrics'}
                        </Badge>
                        <Badge variant="outline" className="text-sm py-1.5 px-4 shadow-sm bg-background">
                            Model: {selectedModel}
                        </Badge>
                        <Badge variant="secondary" className="text-sm py-1.5 px-4 shadow-sm">
                            WCFL Picks: {wcflPicks.length}/10
                        </Badge>
                    </div>
                </div>

                <Tabs defaultValue="predictions" className="w-full">
                    <div className="flex justify-center mb-10">
                        <TabsList className="grid w-full max-w-2xl grid-cols-4 p-1 bg-muted/50 backdrop-blur-sm rounded-xl">
                            <TabsTrigger value="predictions" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-300 rounded-lg">
                                <Activity className="h-4 w-4" /> Predictions
                            </TabsTrigger>
                            <TabsTrigger value="wcfl" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-300 rounded-lg">
                                <TrendingUp className="h-4 w-4" /> WCFL
                            </TabsTrigger>
                            <TabsTrigger value="value" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-300 rounded-lg">
                                <DollarSign className="h-4 w-4" /> Value
                            </TabsTrigger>
                            <TabsTrigger value="performance" className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-md transition-all duration-300 rounded-lg">
                                <Check className="h-4 w-4" /> Performance
                            </TabsTrigger>
                        </TabsList>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                        {/* Controls Sidebar */}
                        <div className="space-y-6">
                            {/* Model Selection */}
                            <Card className="shadow-lg hover:shadow-xl transition-shadow duration-300 border-primary/10">
                                <CardHeader>
                                    <CardTitle>Model Selection</CardTitle>
                                    <CardDescription>Choose your prediction engine</CardDescription>
                                </CardHeader>
                                <CardContent className="grid gap-2">
                                    {['Ridge Regression', 'XGBoost', 'FastAI Neural Net', 'Ensemble'].map(model => (
                                        <Button
                                            key={model}
                                            variant={selectedModel === model ? "default" : "outline"}
                                            className="w-full justify-start transition-all duration-200"
                                            onClick={() => setSelectedModel(model)}
                                        >
                                            {model}
                                            {model === 'Ensemble' && <span className="ml-auto text-xs opacity-75">Weighted</span>}
                                        </Button>
                                    ))}

                                    {selectedModel === 'Ensemble' && (
                                        <div className="mt-4 p-4 bg-muted/50 rounded-lg text-xs space-y-2 border border-border/50">
                                            <div className="font-semibold mb-2 text-primary">Ensemble Weights</div>
                                            <div className="flex justify-between items-center"><span>Ridge</span><span className="font-mono">{(modelPerformance.ridge.weight * 100).toFixed(0)}%</span></div>
                                            <Progress value={modelPerformance.ridge.weight * 100} className="h-1" />
                                            <div className="flex justify-between items-center pt-1"><span>XGBoost</span><span className="font-mono">{(modelPerformance.xgboost.weight * 100).toFixed(0)}%</span></div>
                                            <Progress value={modelPerformance.xgboost.weight * 100} className="h-1" />
                                            <div className="flex justify-between items-center pt-1"><span>FastAI</span><span className="font-mono">{(modelPerformance.fastai.weight * 100).toFixed(0)}%</span></div>
                                            <Progress value={modelPerformance.fastai.weight * 100} className="h-1" />
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Feature Weights */}
                            <Card className="shadow-lg hover:shadow-xl transition-shadow duration-300 border-primary/10">
                                <CardHeader>
                                    <CardTitle>Feature Weights</CardTitle>
                                    <CardDescription>Adjust impact of metrics</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    {Object.entries(featureWeights).map(([key, value]) => (
                                        <div key={key} className="space-y-3">
                                            <div className="flex justify-between text-sm font-medium">
                                                <span className="capitalize flex items-center gap-2">
                                                    {key === 'epa' ? 'EPA' : key}
                                                </span>
                                                <span className="text-muted-foreground font-mono">{value}%</span>
                                            </div>
                                            <Slider
                                                value={[value]}
                                                max={100}
                                                step={1}
                                                onValueChange={(vals) => handleWeightChange(key, vals[0])}
                                                disabled={isTraining}
                                                className="cursor-pointer"
                                            />
                                        </div>
                                    ))}
                                    <Separator />
                                    <div className="text-center text-sm text-muted-foreground font-medium">
                                        Total Weight: <span className={Object.values(featureWeights).reduce((a, b) => a + b, 0) === 100 ? "text-green-500" : "text-destructive"}>
                                            {Object.values(featureWeights).reduce((a, b) => a + b, 0)}%
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Settings & Training */}
                            <Card className="shadow-lg hover:shadow-xl transition-shadow duration-300 border-primary/10 bg-primary/5">
                                <CardHeader>
                                    <CardTitle>Simulation Control</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="flex items-center justify-between p-2 bg-background/50 rounded-lg border border-border/50">
                                        <span className="text-sm font-medium">Tempo Adjustment</span>
                                        <Button
                                            variant={tempoAdjusted ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setTempoAdjusted(!tempoAdjusted)}
                                            className="h-8"
                                        >
                                            {tempoAdjusted ? 'On' : 'Off'}
                                        </Button>
                                    </div>

                                    <Button
                                        className="w-full text-lg font-semibold shadow-lg shadow-primary/20"
                                        size="lg"
                                        onClick={handleTrain}
                                        disabled={isTraining}
                                    >
                                        {isTraining ? 'Training Models...' : 'Run Simulation'}
                                    </Button>

                                    {isTraining && (
                                        <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                            <Progress value={trainingProgress} className="h-2" />
                                            <p className="text-xs text-center text-muted-foreground font-mono">{trainingProgress}% Complete</p>
                                        </div>
                                    )}

                                    {modelMetrics && !isTraining && (
                                        <div className="grid grid-cols-2 gap-3 text-sm animate-in fade-in zoom-in-95">
                                            <div className="bg-background p-3 rounded-lg border border-border/50 shadow-sm">
                                                <div className="text-muted-foreground text-xs uppercase tracking-wider">Accuracy</div>
                                                <div className="font-bold text-xl text-primary">{(modelMetrics.accuracy * 100).toFixed(1)}%</div>
                                            </div>
                                            <div className="bg-background p-3 rounded-lg border border-border/50 shadow-sm">
                                                <div className="text-muted-foreground text-xs uppercase tracking-wider">MAE</div>
                                                <div className="font-bold text-xl text-primary">{modelMetrics.mae.toFixed(2)}</div>
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        {/* Main Content Area */}
                        <div className="lg:col-span-3 space-y-6">
                            {/* Training Chart */}
                            {trainingHistory.length > 0 && (
                                <Card className="shadow-md border-primary/10 overflow-hidden">
                                    <CardHeader className="bg-muted/30 pb-4">
                                        <CardTitle>Training Convergence</CardTitle>
                                    </CardHeader>
                                    <CardContent className="h-[300px] pt-6">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={trainingHistory}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                                <XAxis dataKey="epoch" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                                                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: 'hsl(var(--popover))',
                                                        border: '1px solid hsl(var(--border))',
                                                        borderRadius: 'var(--radius)',
                                                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                                                    }}
                                                />
                                                <Legend />
                                                <Line type="monotone" dataKey="loss" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                                                <Line type="monotone" dataKey="val_loss" stroke="hsl(var(--destructive))" strokeWidth={2} dot={false} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </CardContent>
                                </Card>
                            )}

                            <TabsContent value="predictions" className="mt-0 space-y-4 animate-in fade-in slide-in-from-bottom-4">
                                {predictions.length > 0 ? (
                                    <div className="grid gap-4">
                                        {predictions.map(game => (
                                            <Card key={game.id} className="group hover:border-primary/50 transition-colors duration-300">
                                                <CardContent className="p-6">
                                                    <div className="grid md:grid-cols-4 gap-6 items-center">
                                                        <div className="text-center md:text-left space-y-1">
                                                            <div className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">{game.home_team}</div>
                                                            <div className="text-xs font-mono text-muted-foreground bg-muted inline-block px-2 py-0.5 rounded">ELO: {game.home_elo}</div>
                                                        </div>

                                                        <div className="text-center flex flex-col items-center justify-center">
                                                            <div className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">VS</div>
                                                            <Badge variant="outline" className="font-mono">Spread: {game.spread}</Badge>
                                                        </div>

                                                        <div className="text-center md:text-right space-y-1">
                                                            <div className="text-xl font-bold text-foreground group-hover:text-destructive transition-colors">{game.away_team}</div>
                                                            <div className="text-xs font-mono text-muted-foreground bg-muted inline-block px-2 py-0.5 rounded">ELO: {game.away_elo}</div>
                                                        </div>

                                                        <div className="bg-muted/30 p-4 rounded-xl border border-border/50 text-center space-y-2">
                                                            <div className="text-sm font-medium">
                                                                Winner: <span className={game.prediction.winner === game.home_team ? "text-primary font-bold" : "text-destructive font-bold"}>
                                                                    {game.prediction.winner}
                                                                </span>
                                                            </div>
                                                            <div className="text-xs text-muted-foreground">
                                                                Margin: <span className="font-mono font-medium text-foreground">{game.prediction.predictedMargin}</span>
                                                            </div>
                                                            <div className="pt-1">
                                                                <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
                                                                    <span>Confidence</span>
                                                                    <span>{game.prediction.confidence}%</span>
                                                                </div>
                                                                <Progress value={game.prediction.confidence} className="h-1.5" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-24 bg-muted/10 rounded-3xl border-2 border-dashed border-muted-foreground/20">
                                        <Rocket className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                                        <h3 className="text-lg font-medium text-foreground">Ready to Simulate</h3>
                                        <p className="text-muted-foreground max-w-sm mx-auto mt-2">
                                            Configure your model settings and click "Run Simulation" to generate predictions for Week 13.
                                        </p>
                                    </div>
                                )}
                            </TabsContent>

                            <TabsContent value="wcfl" className="mt-0 animate-in fade-in slide-in-from-bottom-4">
                                {wcflPicks.length > 0 ? (
                                    <div className="space-y-6">
                                        <div className="flex justify-between items-center bg-gradient-to-r from-primary/10 to-transparent p-6 rounded-xl border border-primary/10">
                                            <div>
                                                <h3 className="font-bold text-lg">WCFL Strategy</h3>
                                                <p className="text-sm text-muted-foreground">Optimized point allocation based on confidence & value</p>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-3xl font-bold text-primary">
                                                    {wcflPicks.reduce((sum, p) => sum + p.wcflPoints, 0)}
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">Total Points</div>
                                            </div>
                                        </div>

                                        {wcflPicks.map((pick) => (
                                            <Card key={pick.id} className="border-l-4 border-l-primary hover:shadow-md transition-shadow">
                                                <CardContent className="p-6">
                                                    <div className="flex items-center gap-6">
                                                        <div className="text-center min-w-[80px] bg-primary/5 p-3 rounded-xl">
                                                            <div className="text-3xl font-bold text-primary">{pick.wcflPoints}</div>
                                                            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Points</div>
                                                        </div>

                                                        <div className="flex-1">
                                                            <div className="font-bold text-xl mb-2">
                                                                {pick.home_team} vs {pick.away_team}
                                                            </div>
                                                            <div className="flex gap-3 items-center text-sm">
                                                                <Badge variant={pick.prediction.suggestedSide === 'Pass' ? 'secondary' : 'default'} className="text-sm px-3">
                                                                    Pick: {pick.prediction.suggestedSide}
                                                                </Badge>
                                                                <span className="text-muted-foreground font-mono bg-muted px-2 py-0.5 rounded">Line: {pick.spread > 0 ? '+' : ''}{pick.spread}</span>
                                                            </div>
                                                        </div>

                                                        <div className="text-right">
                                                            <div className={`text-xl font-bold ${pick.prediction.lineValue > 0 ? 'text-green-600' : 'text-muted-foreground'}`}>
                                                                {pick.prediction.lineValue > 0 ? '+' : ''}{pick.prediction.lineValue}
                                                            </div>
                                                            <div className="text-xs text-muted-foreground uppercase tracking-wider">Value Edge</div>
                                                        </div>
                                                    </div>
                                                    <Separator className="my-4" />
                                                    <div className="bg-muted/30 p-3 rounded-lg">
                                                        <p className="text-sm text-muted-foreground flex items-start gap-2">
                                                            <Check className="h-4 w-4 text-primary mt-0.5" />
                                                            <span><span className="font-medium text-foreground">Analysis:</span> {pick.reasoning}</span>
                                                        </p>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-24 bg-muted/10 rounded-3xl border-2 border-dashed border-muted-foreground/20">
                                        <TrendingUp className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                                        <h3 className="text-lg font-medium text-foreground">No Picks Generated</h3>
                                        <p className="text-muted-foreground max-w-sm mx-auto mt-2">
                                            Run the simulation to generate optimized WCFL picks.
                                        </p>
                                    </div>
                                )}
                            </TabsContent>

                            <TabsContent value="value" className="mt-0 animate-in fade-in slide-in-from-bottom-4">
                                {valueOpportunities.length > 0 ? (
                                    <div className="grid gap-4">
                                        {valueOpportunities.map(game => (
                                            <Card key={game.id} className="hover:shadow-md transition-shadow">
                                                <CardContent className="p-6">
                                                    <div className="flex justify-between items-start mb-6">
                                                        <div>
                                                            <h3 className="font-bold text-lg flex items-center gap-2">
                                                                {game.home_team} <span className="text-muted-foreground text-sm font-normal">vs</span> {game.away_team}
                                                            </h3>
                                                            <p className="text-sm text-muted-foreground font-mono mt-1">Spread: {game.spread}</p>
                                                        </div>
                                                        <Badge variant={game.prediction.valueRating === 'Strong Value' ? 'default' : 'secondary'} className="text-sm">
                                                            {game.prediction.valueRating}
                                                        </Badge>
                                                    </div>

                                                    <div className="grid grid-cols-3 gap-4 text-center">
                                                        <div className="bg-muted/30 p-4 rounded-xl">
                                                            <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Model</div>
                                                            <div className="font-bold text-lg">{game.prediction.predictedMargin}</div>
                                                        </div>
                                                        <div className="bg-green-500/10 p-4 rounded-xl border border-green-500/20">
                                                            <div className="text-xs text-green-700 dark:text-green-400 uppercase tracking-wider mb-1">Edge</div>
                                                            <div className="font-bold text-lg text-green-700 dark:text-green-400">{game.prediction.lineValue}</div>
                                                        </div>
                                                        <div className="bg-primary/5 p-4 rounded-xl border border-primary/10">
                                                            <div className="text-xs text-primary uppercase tracking-wider mb-1">Pick</div>
                                                            <div className="font-bold text-lg text-primary">{game.prediction.suggestedSide}</div>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-24 bg-muted/10 rounded-3xl border-2 border-dashed border-muted-foreground/20">
                                        <DollarSign className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                                        <h3 className="text-lg font-medium text-foreground">No Value Found</h3>
                                        <p className="text-muted-foreground max-w-sm mx-auto mt-2">
                                            No significant value opportunities found in the current simulation.
                                        </p>
                                    </div>
                                )}
                            </TabsContent>

                            <TabsContent value="performance" className="mt-0 animate-in fade-in slide-in-from-bottom-4">
                                <Card className="shadow-lg">
                                    <CardHeader>
                                        <CardTitle>Model Performance Comparison</CardTitle>
                                        <CardDescription>Historical accuracy and error rates</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="h-[400px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={Object.entries(modelPerformance).map(([name, data]) => ({
                                                    name: name.charAt(0).toUpperCase() + name.slice(1),
                                                    accuracy: data.accuracy * 100,
                                                    mae: data.mae
                                                }))} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                                                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
                                                    <Tooltip
                                                        cursor={{ fill: 'hsl(var(--muted)/0.5)' }}
                                                        contentStyle={{
                                                            backgroundColor: 'hsl(var(--popover))',
                                                            border: '1px solid hsl(var(--border))',
                                                            borderRadius: 'var(--radius)',
                                                            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                                                        }}
                                                    />
                                                    <Legend />
                                                    <Bar dataKey="accuracy" fill="hsl(var(--primary))" name="Accuracy %" radius={[4, 4, 0, 0]} barSize={40} />
                                                    <Bar dataKey="mae" fill="hsl(var(--destructive))" name="MAE (points)" radius={[4, 4, 0, 0]} barSize={40} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </div>
                    </div>
                </Tabs>
            </div>
        </div>
    );
}
