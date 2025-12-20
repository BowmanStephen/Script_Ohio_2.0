import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Game } from '../../types';

interface PredictionsViewProps {
    predictions: Game[];
}

export const PredictionsView: React.FC<PredictionsViewProps> = ({ predictions }) => {
    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-xl font-bold text-card-foreground">🎯 All Model Predictions ({predictions.length} games)</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-4">
                    {predictions.map(game => (
                        <div key={game.id} className="bg-muted/30 rounded-lg p-6 border border-border">
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                                <div className="text-center">
                                    <div className="text-xl font-bold text-foreground">{game.home_team}</div>
                                    <div className="text-sm text-muted-foreground">ELO: {game.home_elo}</div>
                                    <div className="text-sm text-muted-foreground">EPA: {game.home_adjusted_epa.toFixed(3)}</div>
                                </div>

                                <div className="text-center">
                                    <div className="text-2xl font-bold text-muted-foreground/50">VS</div>
                                    <div className="text-sm text-muted-foreground mt-1">Line: {game.spread}</div>
                                </div>

                                <div className="text-center">
                                    <div className="text-xl font-bold text-foreground">{game.away_team}</div>
                                    <div className="text-sm text-muted-foreground">ELO: {game.away_elo}</div>
                                    <div className="text-sm text-muted-foreground">EPA: {game.away_adjusted_epa.toFixed(3)}</div>
                                </div>

                                <div className="bg-card rounded-lg p-4 border border-border shadow-sm">
                                    <div className="text-foreground font-bold text-lg mb-1">
                                        Winner: {game.prediction?.winner}
                                    </div>
                                    <div className="text-muted-foreground text-sm">
                                        Predicted: {game.prediction?.predictedMargin}
                                    </div>
                                    <div className="text-muted-foreground text-sm">
                                        Value: {game.prediction?.lineValue} ({game.prediction?.valueRating})
                                    </div>
                                    <div className="mt-2">
                                        <div className="text-xs text-muted-foreground mb-1">Confidence</div>
                                        <div className="w-full bg-muted rounded-full h-2 border border-border">
                                            <div
                                                className="bg-primary h-2 rounded-full"
                                                style={{ width: `${game.prediction?.confidence}%` }}
                                            />
                                        </div>
                                        <div className="text-xs text-muted-foreground mt-1 text-center font-mono">
                                            {game.prediction?.confidence}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};
