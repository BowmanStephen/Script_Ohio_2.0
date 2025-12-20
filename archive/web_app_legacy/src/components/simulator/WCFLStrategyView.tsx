import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Game } from '../../types';

interface WCFLStrategyViewProps {
    wcflPicks: Game[];
}

export const WCFLStrategyView: React.FC<WCFLStrategyViewProps> = ({ wcflPicks }) => {
    const totalPoints = wcflPicks.reduce((sum, p) => sum + (p.wcflPoints || 0), 0);

    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">WCFL Strategy</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-6">
                    <div className="flex justify-between items-center p-4 bg-muted/50 rounded-lg border border-border">
                        <span className="text-sm font-medium text-muted-foreground">Total Points Allocated</span>
                        <span className="text-2xl font-bold text-foreground">{totalPoints} <span className="text-muted-foreground text-lg">/ 55</span></span>
                    </div>

                    <div className="space-y-3">
                        {wcflPicks.map((pick) => (
                            <div key={pick.id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border border-l-4 border-l-primary">
                                <div>
                                    <div className="font-bold text-foreground">{pick.home_team} vs {pick.away_team}</div>
                                    <div className="text-xs text-muted-foreground">
                                        Pick: <span className="font-bold text-foreground">{pick.prediction?.suggestedSide}</span>
                                    </div>
                                    <div className="text-xs text-muted-foreground mt-1">
                                        Market Line: {pick.spread > 0 ? '+' : ''}{pick.spread}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="font-bold text-foreground">{pick.wcflPoints} pts</div>
                                    <div className="text-xs text-muted-foreground">Conf: {pick.prediction?.confidence}%</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="p-4 bg-muted/50 rounded-lg border border-border">
                        <div className="flex items-start gap-3">
                            <span className="text-xl">💡</span>
                            <div>
                                <h4 className="font-bold text-foreground text-sm mb-1">Strategy Note</h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Picks are allocated based on model confidence and value rating.
                                    Higher confidence + high value = larger point allocation.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
