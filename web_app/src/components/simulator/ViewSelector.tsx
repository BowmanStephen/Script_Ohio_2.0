import React from 'react';
import { Button } from "@/components/ui/button";

interface ViewSelectorProps {
    selectedView: string;
    onSelectView: (view: string) => void;
}

export const ViewSelector: React.FC<ViewSelectorProps> = ({ selectedView, onSelectView }) => {
    const views = [
        { id: 'predictions', label: '📊 All Predictions', ariaLabel: 'View all game predictions' },
        { id: 'ats', label: '🎯 ATS Analysis', ariaLabel: 'View Against The Spread analysis and picks' },
        { id: 'wcfl', label: '🏈 WCFL Strategy', ariaLabel: 'View WCFL strategy and point allocation' },
        { id: 'value', label: '💰 Value Opportunities', ariaLabel: 'View betting value opportunities' },
        { id: 'performance', label: '📈 Model Performance', ariaLabel: 'View model performance metrics' },
    ];

    const handleKeyDown = (event: React.KeyboardEvent, viewId: string) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onSelectView(viewId);
        } else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
            event.preventDefault();
            const currentIndex = views.findIndex(v => v.id === selectedView);
            const direction = event.key === 'ArrowLeft' ? -1 : 1;
            const newIndex = (currentIndex + direction + views.length) % views.length;
            onSelectView(views[newIndex].id);
            // Focus the newly selected button
            const button = event.currentTarget.parentElement?.children[newIndex] as HTMLElement;
            button?.focus();
        }
    };

    return (
        <nav className="flex justify-center gap-4 mb-8 flex-wrap" role="tablist" aria-label="View selection">
            {views.map(view => (
                <Button
                    key={view.id}
                    onClick={() => onSelectView(view.id)}
                    onKeyDown={(e) => handleKeyDown(e, view.id)}
                    variant={selectedView === view.id ? "default" : "outline"}
                    role="tab"
                    aria-selected={selectedView === view.id}
                    aria-label={view.ariaLabel}
                    tabIndex={selectedView === view.id ? 0 : -1}
                    className={`px-6 py-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring ${selectedView === view.id
                        ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md'
                        : 'bg-card text-muted-foreground border-border hover:bg-accent hover:text-accent-foreground'
                        }`}
                >
                    {view.label}
                </Button>
            ))}
        </nav>
    );
};
