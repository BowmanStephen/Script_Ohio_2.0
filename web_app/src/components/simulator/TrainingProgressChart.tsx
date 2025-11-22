import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrainingHistory } from '../../types';

interface TrainingProgressChartProps {
    history: TrainingHistory[];
}

export const TrainingProgressChart: React.FC<TrainingProgressChartProps> = ({ history }) => {
    if (history.length === 0) return null;

    return (
        <Card className="bg-card border-border shadow-lg h-full">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">Training Convergence</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={history}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                            <XAxis
                                dataKey="epoch"
                                stroke="hsl(var(--muted-foreground))"
                                tick={{ fontSize: 12 }}
                            />
                            <YAxis
                                stroke="hsl(var(--muted-foreground))"
                                tick={{ fontSize: 12 }}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'hsl(var(--popover))',
                                    borderColor: 'hsl(var(--border))',
                                    color: 'hsl(var(--popover-foreground))',
                                    borderRadius: 'var(--radius)'
                                }}
                            />
                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                            <Line
                                type="monotone"
                                dataKey="loss"
                                stroke="hsl(var(--primary))"
                                strokeWidth={2}
                                dot={false}
                                name="Training Loss"
                            />
                            <Line
                                type="monotone"
                                dataKey="val_loss"
                                stroke="hsl(var(--muted-foreground))"
                                strokeWidth={2}
                                strokeDasharray="5 5"
                                dot={false}
                                name="Validation Loss"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
};
