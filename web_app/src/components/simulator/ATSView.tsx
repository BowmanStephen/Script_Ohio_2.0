import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ATSAnalysis } from '../../types';
import { APP_CONSTANTS } from '../../config/constants';

interface ATSViewProps {
    atsData: ATSAnalysis[];
    isLoading?: boolean;
    error?: string;
}

type SortField = 'matchup' | 'spread' | 'predicted_margin' | 'model_edge_pts' | 'confidence_grade' | 'ensemble_confidence';
type SortDirection = 'asc' | 'desc';

export const ATSView: React.FC<ATSViewProps> = ({ atsData, isLoading = false, error }) => {
    const formatSpread = (spread: number): string => {
        return spread % 1 === 0 ? spread.toString() : spread.toFixed(1);
    };

    const [sortField, setSortField] = useState<SortField>('model_edge_pts');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
    const [filterTeam, setFilterTeam] = useState<string>('');
    const [filterConfidence, setFilterConfidence] = useState<'All' | 'High' | 'Medium' | 'Low'>('All');
    const [filterAgreement, setFilterAgreement] = useState<'All' | 'high' | 'moderate'>('All');
    const [minEdge, setMinEdge] = useState<number>(0);

    const sortedData = useMemo(() => {
        let filtered = [...atsData];

        // Filter by team name
        if (filterTeam) {
            const search = filterTeam.toLowerCase();
            filtered = filtered.filter(item => 
                item.matchup.toLowerCase().includes(search)
            );
        }

        // Filter by confidence grade
        if (filterConfidence !== 'All') {
            filtered = filtered.filter(item => item.confidence_grade === filterConfidence);
        }

        // Filter by model agreement
        if (filterAgreement !== 'All') {
            filtered = filtered.filter(item => item.model_agreement === filterAgreement);
        }

        // Filter by minimum edge
        if (minEdge > 0) {
            filtered = filtered.filter(item => item.model_edge_pts >= minEdge);
        }

        // Sort
        filtered.sort((a, b) => {
            let aVal: any, bVal: any;

            switch (sortField) {
                case 'matchup':
                    aVal = a.matchup;
                    bVal = b.matchup;
                    break;
                case 'spread':
                    aVal = a.spread;
                    bVal = b.spread;
                    break;
                case 'predicted_margin':
                    aVal = a.predicted_margin;
                    bVal = b.predicted_margin;
                    break;
                case 'model_edge_pts':
                    aVal = a.model_edge_pts;
                    bVal = b.model_edge_pts;
                    break;
                case 'confidence_grade':
                    const gradeOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
                    aVal = gradeOrder[a.confidence_grade];
                    bVal = gradeOrder[b.confidence_grade];
                    break;
                case 'ensemble_confidence':
                    aVal = a.ensemble_confidence;
                    bVal = b.ensemble_confidence;
                    break;
                default:
                    return 0;
            }

            if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        return filtered;
    }, [atsData, sortField, sortDirection, filterTeam, filterConfidence, filterAgreement, minEdge]);

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const exportToCSV = () => {
        const headers = [
            'Matchup', 'Spread', 'Predicted Margin', 'Home Win Prob', 
            'Away Win Prob', 'ATS Pick', 'Model Edge (pts)', 
            'Confidence Grade', 'Model Agreement', 'Ensemble Confidence', 
            'Model Summary'
        ];
        const rows = sortedData.map(item => [
            item.matchup,
            formatSpread(item.spread),
            item.predicted_margin.toFixed(2),
            (item.home_win_prob * 100).toFixed(1) + '%',
            (item.away_win_prob * 100).toFixed(1) + '%',
            item.ats_pick,
            item.model_edge_pts.toFixed(2),
            item.confidence_grade,
            item.model_agreement,
            (item.ensemble_confidence * 100).toFixed(1) + '%',
            `"${item.model_summary}"`
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = APP_CONSTANTS.FILE_NAMES.ATS_EXPORT();
        link.click();
        window.URL.revokeObjectURL(url);
    };

    const getConfidenceColor = (grade: 'High' | 'Medium' | 'Low') => {
        switch (grade) {
            case 'High':
                return 'bg-green-500/20 text-green-600 dark:text-green-400';
            case 'Medium':
                return 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400';
            case 'Low':
                return 'bg-red-500/20 text-red-600 dark:text-red-400';
        }
    };

    const getAgreementColor = (agreement: 'high' | 'moderate') => {
        return agreement === 'high' 
            ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
            : 'bg-purple-500/20 text-purple-600 dark:text-purple-400';
    };

    const stats = useMemo(() => {
        // Safety check: ensure sortedData exists and is not empty
        if (!sortedData || sortedData.length === 0) {
            return { total: 0, highConf: 0, mediumConf: 0, avgEdge: 0, highAgreement: 0 };
        }

        const total = sortedData.length;
        const highConf = sortedData.filter(item => item.confidence_grade === 'High').length;
        const mediumConf = sortedData.filter(item => item.confidence_grade === 'Medium').length;
        const avgEdge = sortedData.length > 0
            ? sortedData.reduce((sum, item) => sum + (item.model_edge_pts || 0), 0) / sortedData.length
            : 0;
        const highAgreement = sortedData.filter(item => item.model_agreement === 'high').length;

        return { total, highConf, mediumConf, avgEdge, highAgreement };
    }, [sortedData]);

    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <CardTitle className="text-xl font-bold text-card-foreground">
                            📊 ATS Analysis ({sortedData.length} games)
                        </CardTitle>
                        <div className="mt-2 flex flex-wrap gap-4 text-sm text-muted-foreground">
                            <span>High Confidence: {stats.highConf}</span>
                            <span>Avg Edge: {stats.avgEdge.toFixed(1)} pts</span>
                            <span>High Agreement: {stats.highAgreement}</span>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={exportToCSV}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                    >
                        Export CSV
                    </button>
                </div>
            </CardHeader>
            <CardContent className="pt-6">
                {/* Loading/Error States */}
                {isLoading && (
                    <div className="mb-4 p-4 bg-muted/50 border border-border rounded text-center text-muted-foreground">
                        Loading ATS data...
                    </div>
                )}
                {error && !isLoading && (
                    <div className="mb-4 p-4 bg-destructive/10 border border-destructive/50 rounded text-destructive">
                        {error}
                    </div>
                )}
                
                {/* Filters */}
                <div className="mb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <input
                        type="text"
                        placeholder="Filter by team..."
                        value={filterTeam}
                        onChange={(e) => setFilterTeam(e.target.value)}
                        className="px-3 py-2 border border-border rounded bg-background text-foreground"
                    />
                    <select
                        value={filterConfidence}
                        onChange={(e) => setFilterConfidence(e.target.value as any)}
                        className="px-3 py-2 border border-border rounded bg-background text-foreground"
                        aria-label="Filter by confidence grade"
                        title="Filter by confidence grade"
                        name="filter-confidence"
                    >
                        <option value="All">All Confidence</option>
                        <option value="High">High Only</option>
                        <option value="Medium">Medium+</option>
                        <option value="Low">Low Only</option>
                    </select>
                    <select
                        value={filterAgreement}
                        onChange={(e) => setFilterAgreement(e.target.value as any)}
                        className="px-3 py-2 border border-border rounded bg-background text-foreground"
                        aria-label="Filter by model agreement"
                        title="Filter by model agreement"
                        name="filter-agreement"
                    >
                        <option value="All">All Agreement</option>
                        <option value="high">High Agreement</option>
                        <option value="moderate">Moderate Agreement</option>
                    </select>
                    <input
                        type="number"
                        placeholder="Min edge (pts)"
                        value={minEdge || ''}
                        onChange={(e) => setMinEdge(parseFloat(e.target.value) || 0)}
                        min="0"
                        step="0.5"
                        className="px-3 py-2 border border-border rounded bg-background text-foreground"
                    />
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                        <thead>
                            <tr className="border-b border-border">
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('matchup')}
                                >
                                    Matchup {sortField === 'matchup' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('spread')}
                                >
                                    Spread {sortField === 'spread' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('predicted_margin')}
                                >
                                    Pred Margin {sortField === 'predicted_margin' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                >
                                    ATS Pick
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('model_edge_pts')}
                                >
                                    Edge (pts) {sortField === 'model_edge_pts' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('confidence_grade')}
                                >
                                    Confidence {sortField === 'confidence_grade' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                >
                                    Agreement
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('ensemble_confidence')}
                                >
                                    Model Conf {sortField === 'ensemble_confidence' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedData.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="p-8 text-center text-muted-foreground">
                                        No ATS picks match your filters
                                    </td>
                                </tr>
                            ) : (
                                sortedData.map((item) => {
                                    const rowKey = item.id ?? `${item.matchup}_${item.ats_pick}`;
                                    return (
                                    <tr
                                        key={rowKey}
                                        className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                                    >
                                        <td className="p-3 text-foreground font-medium">
                                            {item.matchup}
                                        </td>
                                        <td className="p-3 text-foreground">
                                            {(() => {
                                                const spread = item.spread;
                                                const formatted = formatSpread(Math.abs(spread));
                                                return spread >= 0 ? `+${formatted}` : `-${formatted}`;
                                            })()}
                                        </td>
                                        <td className="p-3 text-foreground">
                                            {item.predicted_margin > 0 ? '+' : ''}{item.predicted_margin.toFixed(1)}
                                        </td>
                                        <td className="p-3">
                                            <div className="font-semibold text-primary">
                                                {item.ats_pick}
                                            </div>
                                        </td>
                                        <td className="p-3">
                                            <div className="font-semibold text-foreground">
                                                {item.model_edge_pts.toFixed(1)}
                                            </div>
                                        </td>
                                        <td className="p-3">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(item.confidence_grade)}`}>
                                                {item.confidence_grade}
                                            </span>
                                        </td>
                                        <td className="p-3">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getAgreementColor(item.model_agreement)}`}>
                                                {item.model_agreement}
                                            </span>
                                        </td>
                                        <td className="p-3 text-foreground">
                                            {(item.ensemble_confidence * 100).toFixed(0)}%
                                        </td>
                                    </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Summary cards for top picks */}
                {sortedData.length > 0 && sortedData[0].model_edge_pts > 5 && (
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                        {sortedData.slice(0, 3).map((item) => (
                            <Card key={`top_${item.matchup}_${item.ats_pick}`} className="bg-muted/30 border-border">
                                <CardContent className="pt-4">
                                    <div className="text-sm font-semibold text-primary mb-2">
                                        {item.ats_pick}
                                    </div>
                                    <div className="text-xs text-muted-foreground mb-2">
                                        {item.matchup}
                                    </div>
                                    <div className="text-sm text-foreground">
                                        {item.model_summary}
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
};
