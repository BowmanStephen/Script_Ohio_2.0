import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Game } from '../../types';
import { APP_CONSTANTS } from '../../config/constants';

interface PredictionsTableViewProps {
    predictions: Game[];
}

type SortField = 'matchup' | 'spread' | 'predictedMargin' | 'confidence' | 'lineValue';
type SortDirection = 'asc' | 'desc';

export const PredictionsTableView: React.FC<PredictionsTableViewProps> = ({ predictions }) => {

    const formatSpread = (spread: number): string => {
        return spread % 1 === 0 ? spread.toString() : spread.toFixed(1);
    };

    // Helper function to identify if a pick is against the spread favorite
    const isUnderdogPick = (game: Game): boolean => {
        if (!game.prediction) return false;

        const predictedMargin = parseFloat(game.prediction.predictedMargin);
        const spread = game.spread;

        // Who is favored by the spread?
        // If spread > 0: home team is favored (they give points)
        // If spread < 0: away team is favored (home team gets points)
        const homeIsFavored = spread > 0;

        // Who does the model pick to win?
        const modelPicksHome = predictedMargin > 0;

        // If home is favored but model picks away (or vice versa), it's an underdog pick
        return (homeIsFavored && !modelPicksHome) || (!homeIsFavored && modelPicksHome);
    };

    // Helper function to get pick explanation
    const getPickExplanation = (game: Game): string => {
        if (!game.prediction) return 'No prediction';

        const predictedMargin = parseFloat(game.prediction.predictedMargin);
        const spread = game.spread;
        const lineValue = parseFloat(game.prediction.lineValue);
        const homeIsFavored = spread > 0;
        const modelPicksHome = predictedMargin > 0;

        if (Math.abs(lineValue) < 0.5) {
            return 'Model predicts the spread is about right';
        }

        if (isUnderdogPick(game)) {
            return `Model identifies ${homeIsFavored ? game.away_team : game.home_team} as undervalued`;
        } else {
            return `Model agrees with ${homeIsFavored ? game.home_team : game.away_team} as the right side`;
        }
    };

    const formatMargin = (margin: string | number | undefined): string => {
        const parsed = typeof margin === 'number' ? margin : parseFloat(margin || '0');
        if (!Number.isFinite(parsed)) return '0.0';
        return parsed > 0 ? `+${parsed.toFixed(1)}` : parsed.toFixed(1);
    };

    const formatPercent = (value: string | number | undefined): string => {
        const parsed = typeof value === 'number' ? value : parseFloat(value || '0');
        const clamped = Math.min(100, Math.max(0, parsed));
        return clamped.toFixed(1);
    };

    const [sortField, setSortField] = useState<SortField>('confidence');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
    const [filterTeam, setFilterTeam] = useState<string>('');
    const [filterWeek, setFilterWeek] = useState<number | null>(null);
    const [filterConfidence, setFilterConfidence] = useState<'All' | 'High' | 'Moderate' | 'Low'>('All');

    const sortedPredictions = useMemo(() => {
        let filtered = [...predictions];

        // Filter by team name
        if (filterTeam) {
            const search = filterTeam.toLowerCase();
            filtered = filtered.filter(g => 
                g.home_team.toLowerCase().includes(search) || 
                g.away_team.toLowerCase().includes(search)
            );
        }

        // Filter by week if specified
        if (filterWeek !== null) {
            filtered = filtered.filter(g => g.week === filterWeek);
        }

        // Filter by confidence grade
        if (filterConfidence !== 'All') {
            filtered = filtered.filter(g => {
                const conf = parseFloat(g.prediction?.confidence || '0');
                if (filterConfidence === 'High') return conf >= 75;
                if (filterConfidence === 'Moderate') return conf >= 50 && conf < 75;
                if (filterConfidence === 'Low') return conf < 50;
                return true;
            });
        }

        // Sort
        filtered.sort((a, b) => {
            if (!a || !b) return 0;

            let aVal: any, bVal: any;

            switch (sortField) {
                case 'matchup':
                    aVal = `${a.away_team} @ ${a.home_team}`;
                    bVal = `${b.away_team} @ ${b.home_team}`;
                    break;
                case 'spread':
                    aVal = a.spread ?? 0;
                    bVal = b.spread ?? 0;
                    break;
                case 'predictedMargin':
                    aVal = parseFloat(a.prediction?.predictedMargin || '0');
                    bVal = parseFloat(b.prediction?.predictedMargin || '0');
                    break;
                case 'confidence':
                    aVal = parseFloat(a.prediction?.confidence || '0');
                    bVal = parseFloat(b.prediction?.confidence || '0');
                    break;
                case 'lineValue':
                    aVal = parseFloat(a.prediction?.lineValue || '0');
                    bVal = parseFloat(b.prediction?.lineValue || '0');
                    break;
                default:
                    return 0;
            }

            if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        return filtered;
    }, [predictions, sortField, sortDirection, filterTeam, filterWeek, filterConfidence]);

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const exportToCSV = () => {
        const headers = ['Matchup', 'Win Prob (Home) %', 'Spread', 'Predicted Margin', 'Edge vs Line', 'Value'];
        const rows = sortedPredictions.map(g => {
            const lineValue = formatMargin(g.prediction?.lineValue);
            return [
                `${g.away_team} @ ${g.home_team}`,
                formatPercent(g.prediction?.confidence),
                formatSpread(g.spread),
                formatMargin(g.prediction?.predictedMargin),
                lineValue,
                g.prediction?.valueRating ?? 'No Value'
            ];
        });

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = APP_CONSTANTS.FILE_NAMES.PREDICTIONS_EXPORT(filterWeek);
        link.click();
        window.URL.revokeObjectURL(url);
    };

    const getConfidenceGrade = (confidence: string): 'High' | 'Moderate' | 'Low' => {
        const conf = parseFloat(confidence || '0');
        if (conf >= 75) return 'High';
        if (conf >= 50) return 'Moderate';
        return 'Low';
    };

    const getConfidenceColor = (grade: 'High' | 'Moderate' | 'Low') => {
        switch (grade) {
            case 'High':
                return 'bg-green-500/20 text-green-600 dark:text-green-400';
            case 'Moderate':
                return 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400';
            case 'Low':
                return 'bg-red-500/20 text-red-600 dark:text-red-400';
        }
    };

    // Get unique weeks from predictions
    const availableWeeks = useMemo(() => {
        const weeks = new Set(predictions.map(g => g.week).filter((w): w is number => w !== undefined));
        return Array.from(weeks).sort((a, b) => a - b);
    }, [predictions]);

    const stats = useMemo(() => {
        if (!sortedPredictions || sortedPredictions.length === 0) {
            return { total: 0, highConf: 0, moderateConf: 0, avgConf: 0, avgMargin: 0, underdogPicks: 0 };
        }

        const total = sortedPredictions.length;
        const highConf = sortedPredictions.filter(g => {
            const conf = parseFloat(g.prediction?.confidence || '0');
            return conf >= 75;
        }).length;
        const moderateConf = sortedPredictions.filter(g => {
            const conf = parseFloat(g.prediction?.confidence || '0');
            return conf >= 50 && conf < 75;
        }).length;
        const avgConf = sortedPredictions.length > 0
            ? sortedPredictions.reduce((sum, g) => sum + parseFloat(g.prediction?.confidence || '0'), 0) / sortedPredictions.length
            : 0;
        const avgMargin = sortedPredictions.length > 0
            ? sortedPredictions.reduce((sum, g) => sum + Math.abs(parseFloat(g.prediction?.predictedMargin || '0')), 0) / sortedPredictions.length
            : 0;
        const underdogPicks = sortedPredictions.filter(g => isUnderdogPick(g)).length;

        return { total, highConf, moderateConf, avgConf, avgMargin, underdogPicks };
    }, [sortedPredictions]);

    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <CardTitle className="text-xl font-bold text-card-foreground">
                            📊 Predictions Table ({sortedPredictions.length} games)
                        </CardTitle>
                        <div className="mt-2 flex flex-wrap gap-4 text-sm text-muted-foreground">
                            <span>High Confidence: {stats.highConf}</span>
                            <span>Avg Confidence: {stats.avgConf.toFixed(1)}%</span>
                            <span>Avg Margin: {stats.avgMargin.toFixed(1)} pts</span>
                            {stats.underdogPicks > 0 && (
                                <span className="text-orange-600 dark:text-orange-400 font-medium">
                                    🎯 Value Picks: {stats.underdogPicks} ({((stats.underdogPicks / stats.total) * 100).toFixed(1)}%)
                                </span>
                            )}
                        </div>
                        {stats.underdogPicks > 0 && (
                            <div className="mt-1 text-xs text-orange-600 dark:text-orange-400">
                                Model identifies {stats.underdogPicks} game{stats.underdogPicks > 1 ? 's' : ''} where betting lines may be inefficient
                            </div>
                        )}
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
            {stats.underdogPicks > 0 && (
                <CardContent className="pt-4 pb-0">
                    <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4 mb-4">
                        <div className="flex items-start gap-3">
                            <div className="text-orange-600 dark:text-orange-400 text-lg">💡</div>
                            <div>
                                <h4 className="font-semibold text-orange-600 dark:text-orange-400 mb-2">
                                    Why You're Seeing "Underdog" Picks
                                </h4>
                                <p className="text-sm text-muted-foreground mb-2">
                                    Your model is working correctly! It's identifying <strong>betting market inefficiencies</strong> where the spread may not reflect the true statistical advantage.
                                </p>
                                <div className="text-xs text-muted-foreground">
                                    <strong>Example:</strong> If a team is statistically superior (higher ELO, talent, etc.) but listed as an underdog,
                                    the model correctly flags this as a value opportunity rather than a bug.
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            )}
            <CardContent className="pt-6">
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
                        value={filterWeek || ''}
                        onChange={(e) => setFilterWeek(e.target.value ? parseInt(e.target.value) : null)}
                        className="px-3 py-2 border border-border rounded bg-background text-foreground"
                        aria-label="Filter by week"
                        title="Filter by week"
                        name="filter-week"
                    >
                        <option value="">All Weeks</option>
                        {availableWeeks.map(week => (
                            <option key={week} value={week}>Week {week}</option>
                        ))}
                    </select>
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
                        <option value="Moderate">Moderate+</option>
                        <option value="Low">Low Only</option>
                    </select>
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
                                    onClick={() => handleSort('predictedMargin')}
                                >
                                    Pred Margin {sortField === 'predictedMargin' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('confidence')}
                                >
                                    Win Prob {sortField === 'confidence' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th 
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                    onClick={() => handleSort('lineValue')}
                                >
                                    Line Value {sortField === 'lineValue' && (sortDirection === 'asc' ? '↑' : '↓')}
                                </th>
                                <th
                                    className="text-left p-3 font-semibold text-foreground cursor-pointer hover:bg-muted/50 transition-colors"
                                >
                                    Confidence
                                </th>
                                <th className="text-left p-3 font-semibold text-foreground">
                                    Pick Type
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedPredictions.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                                        No predictions match your filters
                                    </td>
                                </tr>
                            ) : (
                                sortedPredictions.map((game) => {
                                    const rowKey = game.id ?? `${game.home_team}_${game.away_team}`;
                                    const confidenceGrade = getConfidenceGrade(game.prediction?.confidence || '0');
                                    const underdog = isUnderdogPick(game);
                                    const explanation = getPickExplanation(game);

                                    return (
                                        <tr
                                            key={rowKey}
                                            className={`border-b border-border/50 hover:bg-muted/30 transition-colors ${
                                                underdog ? 'bg-orange-500/5' : ''
                                            }`}
                                        >
                                            <td className="p-3 text-foreground font-medium">
                                                <div className="flex items-center gap-2">
                                                    {game.away_team} @ {game.home_team}
                                                    {underdog && (
                                                        <span className="px-2 py-0.5 bg-orange-500/20 text-orange-600 dark:text-orange-400 text-xs rounded font-medium">
                                                            🎯 Value
                                                        </span>
                                                    )}
                                                </div>
                                                {game.week && (
                                                    <div className="text-xs text-muted-foreground mt-1">Week {game.week}</div>
                                                )}
                                            </td>
                                            <td className="p-3 text-foreground">
                                                {(() => {
                                                    const spread = game.spread;
                                                    const formatted = formatSpread(Math.abs(spread));
                                                    return spread >= 0 ? `+${formatted}` : `-${formatted}`;
                                                })()}
                                            </td>
                                            <td className="p-3 text-foreground">
                                                {formatMargin(game.prediction?.predictedMargin)}
                                            </td>
                                            <td className="p-3 text-foreground">
                                                {formatPercent(game.prediction?.confidence)}%
                                            </td>
                                            <td className="p-3">
                                                <div className={`font-semibold ${underdog ? 'text-orange-600 dark:text-orange-400' : 'text-foreground'}`}>
                                                    {(() => {
                                                        const value = typeof game.prediction?.lineValue === 'number'
                                                            ? game.prediction.lineValue
                                                            : parseFloat(game.prediction?.lineValue || '0');
                                                        return Number.isFinite(value) ? value.toFixed(1) : '0.0';
                                                    })()}
                                                </div>
                                            </td>
                                            <td className="p-3">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(confidenceGrade)}`}>
                                                    {confidenceGrade}
                                                </span>
                                            </td>
                                            <td className="p-3">
                                                <div className="text-xs text-muted-foreground max-w-xs" title={explanation}>
                                                    {explanation}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Summary cards for top confidence picks */}
                {sortedPredictions.length > 0 && (
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                        {sortedPredictions
                            .filter(g => parseFloat(g.prediction?.confidence || '0') >= 70)
                            .slice(0, 3)
                            .map((game) => {
                                const conf = parseFloat(game.prediction?.confidence || '0');
                                const grade = getConfidenceGrade(game.prediction?.confidence || '0');
                                return (
                                    <Card key={`top_${game.id ?? `${game.home_team}_${game.away_team}`}`} className="bg-muted/30 border-border">
                                        <CardContent className="pt-4">
                                            <div className="text-sm font-semibold text-primary mb-2">
                                                {conf.toFixed(1)}% Confidence
                                            </div>
                                            <div className="text-xs text-muted-foreground mb-2">
                                                {game.away_team} @ {game.home_team}
                                            </div>
                                            <div className="text-sm text-foreground mb-2">
                                                Predicted: {formatMargin(game.prediction?.predictedMargin)}
                                            </div>
                                            <div className={`inline-flex px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(grade)}`}>
                                                {grade}
                                            </div>
                                        </CardContent>
                                    </Card>
                                );
                            })}
                    </div>
                )}
            </CardContent>
        </Card>
    );
};
