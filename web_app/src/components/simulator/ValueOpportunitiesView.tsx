import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Game } from '../../types';

interface ValueOpportunitiesViewProps {
    valueOpportunities: Game[];
}

export const ValueOpportunitiesView: React.FC<ValueOpportunitiesViewProps> = ({ valueOpportunities }) => {
    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">Value Opportunities</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-4">
                    {valueOpportunities.length > 0 ? (
                        valueOpportunities.map((game) => (
                            <div key={game.id} className="p-4 bg-muted/30 rounded-lg border border-border">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <div className="font-bold text-foreground">{game.home_team} vs {game.away_team}</div>
                                        <div className="text-xs text-muted-foreground">Spread: {game.spread}</div>
                                    </div>
                                    <Badge variant="outline" className="border-border text-foreground">
                                        {game.prediction?.valueRating} Value
                                    </Badge>
                                </div>
                                <div className="flex justify-between items-center mt-3 p-2 bg-background rounded border border-border">
                                    <span className="text-sm text-muted-foreground">Model Edge</span>
                                    {(() => {
                                        const lineValue = parseFloat(game.prediction?.lineValue || '0');
                                        const sign = lineValue >= 0 ? '+' : '';
                                        return (
                                            <span className="font-bold text-primary">{sign}{lineValue.toFixed(1)} pts</span>
                                        );
                                    })()}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <div className="text-4xl mb-2 opacity-20">🎯</div>
                            <p>No significant value opportunities detected</p>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};
