import React from 'react';
import { Badge } from "@/components/ui/badge";
import { APP_CONSTANTS } from '../../config/constants';

interface HeaderProps {
    gameCount: number;
    tempoAdjusted: boolean;
    selectedModel: string;
    wcflPicksCount: number;
}

export const Header: React.FC<HeaderProps> = ({ gameCount, tempoAdjusted, selectedModel, wcflPicksCount }) => {
    return (
        <header className="text-center mb-8">
            <h1 className="text-5xl font-bold text-foreground mb-2 tracking-tight">
                Script Ohio 2.0
            </h1>
            <p className="text-xl text-muted-foreground font-light">
                Week {APP_CONSTANTS.CURRENT_WEEK} • {gameCount} games loaded
            </p>
            <div className="flex justify-center gap-4 mt-6" role="status" aria-live="polite" aria-atomic="true">
                <Badge 
                    variant={tempoAdjusted ? "default" : "outline"} 
                    className={`text-sm px-4 py-1 ${tempoAdjusted ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'border-border text-muted-foreground'}`}
                    aria-label={`Tempo adjustment is ${tempoAdjusted ? 'enabled' : 'disabled'}`}
                >
                    Tempo Adjusted: {tempoAdjusted ? 'ON' : 'OFF'}
                </Badge>
                <Badge 
                    variant="outline" 
                    className="text-sm px-4 py-1 border-border text-foreground font-medium"
                    aria-label={`Selected model: ${selectedModel}`}
                >
                    Model: {selectedModel}
                </Badge>
                <Badge 
                    variant="outline" 
                    className="text-sm px-4 py-1 border-border text-muted-foreground"
                    aria-label={`WCFL picks: ${wcflPicksCount} out of 10`}
                >
                    WCFL Picks: {wcflPicksCount}/10
                </Badge>
            </div>
        </header>
    );
};
