import React from 'react';
import { Badge } from "@/components/ui/badge";

interface HeaderProps {
    gameCount: number;
    tempoAdjusted: boolean;
    selectedModel: string;
    wcflPicksCount: number;
}

export const Header: React.FC<HeaderProps> = ({ tempoAdjusted, selectedModel, wcflPicksCount }) => {
    return (
        <div className="text-center mb-8">
            <h1 className="text-5xl font-bold text-foreground mb-2 tracking-tight">
                Script Ohio 2.0
            </h1>
            <p className="text-xl text-muted-foreground font-light">Week 13 • Enhanced ML Simulator</p>
            <div className="flex justify-center gap-4 mt-6">
                <Badge variant={tempoAdjusted ? "default" : "outline"} className={`text-sm px-4 py-1 ${tempoAdjusted ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'border-border text-muted-foreground'}`}>
                    Tempo Adjusted: {tempoAdjusted ? 'ON' : 'OFF'}
                </Badge>
                <Badge variant="outline" className="text-sm px-4 py-1 border-border text-foreground font-medium">
                    Model: {selectedModel}
                </Badge>
                <Badge variant="outline" className="text-sm px-4 py-1 border-border text-muted-foreground">
                    WCFL Picks: {wcflPicksCount}/10
                </Badge>
            </div>
        </div>
    );
};
