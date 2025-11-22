import React from 'react';
import { Button } from "@/components/ui/button";

interface ViewSelectorProps {
    selectedView: string;
    onSelectView: (view: string) => void;
}

export const ViewSelector: React.FC<ViewSelectorProps> = ({ selectedView, onSelectView }) => {
    const views = [
        { id: 'predictions', label: '📊 All Predictions' },
        { id: 'wcfl', label: '🏈 WCFL Strategy' },
        { id: 'value', label: '💰 Value Opportunities' },
        { id: 'performance', label: '📈 Model Performance' },
    ];

    return (
        <div className="flex justify-center gap-4 mb-8 flex-wrap">
            {views.map(view => (
                <Button
                    key={view.id}
                    onClick={() => onSelectView(view.id)}
                    variant={selectedView === view.id ? "default" : "outline"}
                    className={`px-6 py-2 ${selectedView === view.id
                        ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md'
                        : 'bg-card text-muted-foreground border-border hover:bg-accent hover:text-accent-foreground'
                        }`}
                >
                    {view.label}
                </Button>
            ))}
        </div>
    );
};
