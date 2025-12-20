import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface AdvancedSettingsProps {
    tempoAdjusted: boolean;
    onToggleTempo: () => void;
    gameCount: number;
    featureCount: number;
}

export const AdvancedSettings: React.FC<AdvancedSettingsProps> = ({ tempoAdjusted, onToggleTempo, gameCount, featureCount }) => {
    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">Advanced Settings</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-6">
                    <div className="space-y-3">
                        <div className="text-sm font-medium text-muted-foreground">Tempo Adjustment</div>
                        <div className="flex gap-2">
                            <Button
                                variant={tempoAdjusted ? "default" : "outline"}
                                onClick={onToggleTempo}
                                className={`w-full ${tempoAdjusted
                                    ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md'
                                    : 'bg-card text-muted-foreground border-border hover:bg-accent hover:text-accent-foreground'
                                    }`}
                            >
                                {tempoAdjusted ? 'Enabled' : 'Disabled'}
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="text-sm font-medium text-muted-foreground">Simulation Parameters</div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-muted/50 rounded-lg border border-border">
                                <div className="text-xs text-muted-foreground mb-1">Games Analyzed</div>
                                <div className="text-xl font-bold text-foreground">{gameCount}</div>
                            </div>
                            <div className="p-3 bg-muted/50 rounded-lg border border-border">
                                <div className="text-xs text-muted-foreground mb-1">Features Used</div>
                                <div className="text-xl font-bold text-foreground">{featureCount}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
