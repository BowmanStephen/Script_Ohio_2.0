import React from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ModelPerformance } from '../../types';

interface ModelSelectionProps {
    selectedModel: string;
    onSelectModel: (model: string) => void;
    modelPerformance: ModelPerformance;
}

export const ModelSelection: React.FC<ModelSelectionProps> = ({ selectedModel, onSelectModel, modelPerformance }) => {
    const models = ['Ridge Regression', 'XGBoost', 'FastAI Neural Net', 'Ensemble'];

    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">Model Selection</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-2">
                    {models.map(model => (
                        <Button
                            key={model}
                            onClick={() => onSelectModel(model)}
                            variant={selectedModel === model ? "default" : "outline"}
                            aria-label={`Select ${model} model`}
                            aria-pressed={selectedModel === model}
                            className={`w-full justify-start h-auto py-3 font-medium transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring ${selectedModel === model
                                ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md'
                                : 'bg-card text-muted-foreground border-border hover:bg-accent hover:text-accent-foreground'
                                }`}
                        >
                            <div className="flex flex-col items-start">
                                <span>{model}</span>
                                {model === 'Ensemble' && (
                                    <span className="text-xs opacity-75 font-normal">Performance-Weighted</span>
                                )}
                            </div>
                        </Button>
                    ))}
                </div>

                {selectedModel === 'Ensemble' && (
                    <div className="mt-6 p-4 bg-muted/50 rounded-lg border border-border">
                        <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mb-3">Ensemble Weights</div>
                        <div className="space-y-2 text-sm text-muted-foreground">
                            <div className="flex justify-between"><span>Ridge</span> <span className="font-mono text-foreground">{(modelPerformance.ridge.weight * 100).toFixed(0)}%</span></div>
                            <div className="flex justify-between"><span>XGBoost</span> <span className="font-mono text-foreground">{(modelPerformance.xgboost.weight * 100).toFixed(0)}%</span></div>
                            <div className="flex justify-between"><span>FastAI</span> <span className="font-mono text-foreground">{(modelPerformance.fastai.weight * 100).toFixed(0)}%</span></div>
                            <div className="flex justify-between border-t border-border pt-2 mt-2 font-medium text-foreground"><span>Consensus</span> <span className="font-mono text-primary">{(modelPerformance.consensus.weight * 100).toFixed(0)}%</span></div>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};
