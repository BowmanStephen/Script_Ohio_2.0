import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { FeatureWeights as FeatureWeightsType } from '../../types';

interface FeatureWeightsProps {
    weights: FeatureWeightsType;
    onWeightChange: (metric: string, value: number) => void;
    isTraining: boolean;
}

export const FeatureWeights: React.FC<FeatureWeightsProps> = ({ weights, onWeightChange, isTraining }) => {
    const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0) * 100;

    return (
        <Card className="bg-card border-border shadow-lg">
            <CardHeader className="border-b border-border pb-4">
                <CardTitle className="text-lg font-bold text-card-foreground">Feature Weights</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
                <div className="space-y-6">
                    {Object.entries(weights).map(([feature, weight]) => (
                        <div key={feature} className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="capitalize text-muted-foreground">{feature.replace('_', ' ')}</span>
                                <span className="font-mono text-foreground">{(weight * 100).toFixed(0)}%</span>
                            </div>
                            <Slider
                                value={[weight * 100]}
                                min={0}
                                max={100}
                                step={5}
                                onValueChange={(val) => onWeightChange(feature, val[0] / 100)}
                                disabled={isTraining}
                                className="cursor-pointer"
                            />
                        </div>
                    ))}
                    <div className={`pt-4 border-t border-border flex justify-between font-bold ${totalWeight === 100 ? 'text-green-500' : 'text-destructive'
                        }`}>
                        <span>Total</span>
                        <span>{totalWeight}%</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
