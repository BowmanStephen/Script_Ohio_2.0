import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ModelMetricsState } from '../../types';

interface TrainingControlProps {
    isTraining: boolean;
    trainingProgress: number;
    onTrain: () => void;
    modelMetrics: ModelMetricsState | null;
}

export const TrainingControl: React.FC<TrainingControlProps> = ({ isTraining, trainingProgress, onTrain, modelMetrics }) => {
    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">Training Control</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-6">
                    <Button
                        onClick={onTrain}
                        disabled={isTraining}
                        className={`w-full py-6 font-bold text-lg transition-all ${isTraining
                            ? 'bg-muted text-muted-foreground cursor-not-allowed'
                            : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md'
                            }`}
                    >
                        {isTraining ? 'Training in Progress...' : 'Train Model'}
                    </Button>

                    {isTraining && (
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm text-muted-foreground">
                                <span>Progress</span>
                                <span>{trainingProgress}%</span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary transition-all duration-500"
                                    style={{ width: `${trainingProgress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {modelMetrics && !isTraining && (
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-muted/50 rounded-lg border border-border">
                                <div className="text-xs text-muted-foreground mb-1">Accuracy</div>
                                <div className="text-xl font-bold text-foreground">
                                    {(modelMetrics.accuracy * 100).toFixed(1)}%
                                </div>
                            </div>
                            <div className="p-3 bg-muted/50 rounded-lg border border-border">
                                <div className="text-xs text-muted-foreground mb-1">MAE</div>
                                <div className="text-xl font-bold text-foreground">
                                    {modelMetrics.mae.toFixed(2)}
                                </div>
                            </div>
                            <div className="p-3 bg-muted/50 rounded-lg border border-border">
                                <div className="text-xs text-muted-foreground mb-1">RMSE</div>
                                <div className="text-xl font-bold text-foreground">
                                    {modelMetrics.rmse.toFixed(2)}
                                </div>
                            </div>
                            <div className="p-3 bg-muted/50 rounded-lg border border-border">
                                <div className="text-xs text-muted-foreground mb-1">R² Score</div>
                                <div className="text-xl font-bold text-foreground">
                                    {modelMetrics.r2.toFixed(3)}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};
