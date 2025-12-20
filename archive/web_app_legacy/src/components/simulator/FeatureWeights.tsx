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
    // Use tolerance-based comparison to handle floating-point precision issues
    // Matches the 0.001 tolerance used in MLSimulator normalization logic (0.001 * 100 = 0.1)
    const isTotalValid = Math.abs(totalWeight - 100) < 0.1;

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
                                <label 
                                    htmlFor={`weight-${feature}`}
                                    className="capitalize text-muted-foreground"
                                >
                                    {feature.replace('_', ' ')}
                                </label>
                                <span 
                                    className="font-mono text-foreground"
                                    aria-live="polite"
                                    aria-atomic="true"
                                >
                                    {(weight * 100).toFixed(0)}%
                                </span>
                            </div>
                            <Slider
                                id={`weight-${feature}`}
                                value={[weight * 100]}
                                min={0}
                                max={100}
                                step={5}
                                onValueChange={(val) => onWeightChange(feature, val[0] / 100)}
                                disabled={isTraining}
                                className="cursor-pointer"
                                aria-label={`Adjust ${feature.replace('_', ' ')} weight`}
                                aria-valuemin={0}
                                aria-valuemax={100}
                                aria-valuenow={weight * 100}
                                aria-valuetext={`${(weight * 100).toFixed(0)} percent`}
                            />
                        </div>
                    ))}
                    <div className={`pt-4 border-t border-border flex justify-between font-bold ${isTotalValid ? 'text-green-500' : 'text-destructive'
                        }`}>
                        <span>Total</span>
                        <span>{totalWeight.toFixed(1)}%</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
