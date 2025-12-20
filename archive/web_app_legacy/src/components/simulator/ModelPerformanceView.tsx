import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ModelPerformance } from '../../types';

interface ModelPerformanceViewProps {
    modelPerformance: ModelPerformance;
}

export const ModelPerformanceView: React.FC<ModelPerformanceViewProps> = ({ modelPerformance }) => {
    return (
        <Card className="bg-card border-border shadow-lg mb-6">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-xl font-bold text-card-foreground">📈 Model Performance Comparison</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div>
                        <h4 className="text-lg font-bold text-foreground mb-4">Historical Accuracy</h4>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={Object.entries(modelPerformance).map(([name, data]) => ({
                                name: name.charAt(0).toUpperCase() + name.slice(1),
                                accuracy: data.accuracy * 100,
                                mae: data.mae
                            }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 12 }} />
                                <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--popover))',
                                        borderColor: 'hsl(var(--border))',
                                        color: 'hsl(var(--popover-foreground))',
                                        borderRadius: 'var(--radius)'
                                    }}
                                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    cursor={{ fill: 'hsl(var(--muted))' }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                <Bar dataKey="accuracy" fill="hsl(var(--primary))" name="Accuracy %" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    <div>
                        <h4 className="text-lg font-bold text-foreground mb-4">Mean Absolute Error</h4>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={Object.entries(modelPerformance).map(([name, data]) => ({
                                name: name.charAt(0).toUpperCase() + name.slice(1),
                                mae: data.mae
                            }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 12 }} />
                                <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'hsl(var(--popover))',
                                        borderColor: 'hsl(var(--border))',
                                        color: 'hsl(var(--popover-foreground))',
                                        borderRadius: 'var(--radius)'
                                    }}
                                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    cursor={{ fill: 'hsl(var(--muted))' }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                <Bar dataKey="mae" fill="hsl(var(--muted-foreground))" name="MAE (points)" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {Object.entries(modelPerformance).map(([name, data]) => (
                        <div key={name} className="bg-muted/30 rounded-lg p-4 border border-border">
                            <h5 className="text-foreground font-bold mb-3 capitalize">{name}</h5>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Accuracy</span>
                                    <span className="text-foreground font-bold font-mono">{(data.accuracy * 100).toFixed(1)}%</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">MAE</span>
                                    <span className="text-foreground font-bold font-mono">{data.mae.toFixed(1)}</span>
                                </div>
                                <div className="flex justify-between border-t border-border pt-2 mt-2">
                                    <span className="text-muted-foreground">Weight</span>
                                    <span className="text-foreground font-bold font-mono">{(data.weight * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};
