import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Info,
  HelpCircle,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  BookOpen,
  TrendingUp,
  Zap,
  Target
} from 'lucide-react';

interface ExplanationItem {
  id: string;
  title: string;
  description: string;
  detail: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  category: 'business' | 'technical' | 'data' | 'ml';
  icon?: React.ComponentType<any>;
  relatedItems?: string[];
}

interface ProgressiveExplanationProps {
  context?: string;
  items?: ExplanationItem[];
  showLevel?: boolean;
  className?: string;
}

const ProgressiveExplanation: React.FC<ProgressiveExplanationProps> = ({
  context,
  items,
  showLevel = true,
  className = ''
}) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [currentLevel, setCurrentLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [showAllLevels, setShowAllLevels] = useState(false);

  // Default explanations for different contexts
  const defaultExplanations: Record<string, ExplanationItem[]> = {
    dashboard: [
      {
        id: 'accuracy',
        title: 'Prediction Accuracy',
        description: 'How often our predictions are correct',
        detail: 'Our system correctly predicts game outcomes 73.8% of the time, which ranks us #4 among industry leaders. This accuracy is achieved through advanced machine learning models analyzing 86 unique features per game.',
        level: 'beginner',
        category: 'business',
        icon: Target,
        relatedItems: ['models', 'features']
      },
      {
        id: 'models',
        title: 'ML Models',
        description: 'Three AI systems working together',
        detail: 'We use three machine learning models: Ridge Regression (linear relationships), XGBoost (decision trees), and FastAI (neural networks). Each model specializes in different pattern recognition, and combining them improves overall accuracy.',
        level: 'intermediate',
        category: 'technical',
        icon: Zap,
        relatedItems: ['accuracy', 'ensemble']
      },
      {
        id: 'ensemble',
        title: 'Ensemble Method',
        description: 'Combining multiple models for better results',
        detail: 'Instead of relying on a single model, our ensemble system weighs predictions from all three models based on their historical performance. This approach reduces bias and increases reliability, similar to how a committee of experts makes better decisions than any single expert.',
        level: 'advanced',
        category: 'ml',
        icon: TrendingUp,
        relatedItems: ['models', 'accuracy']
      }
    ],
    agents: [
      {
        id: 'agents',
        title: 'AI Agents',
        description: 'Smart programs that handle specific tasks',
        detail: 'Our system uses 18+ specialized AI agents, each responsible for different tasks like data collection, analysis, or validation. They work together like a team, communicating and coordinating to process information efficiently.',
        level: 'beginner',
        category: 'technical',
        icon: HelpCircle,
        relatedItems: ['orchestration', 'coordination']
      },
      {
        id: 'orchestration',
        title: 'Agent Orchestration',
        description: 'Coordinating multiple AI agents',
        detail: 'The Meta Agent acts like a project manager, assigning tasks to specialized agents and ensuring they work together efficiently. This prevents conflicts and optimizes resource usage, similar to how a conductor leads an orchestra.',
        level: 'intermediate',
        category: 'technical',
        icon: BookOpen,
        relatedItems: ['agents', 'coordination']
      }
    ],
    predictions: [
      {
        id: 'confidence',
        title: 'Confidence Score',
        description: 'How sure we are about a prediction',
        detail: 'Our confidence scores range from 50% (completely uncertain) to 100% (completely certain). Higher confidence means the model has seen similar situations before and is more sure of the outcome. We use 73%+ confidence as our threshold for making predictions.',
        level: 'beginner',
        category: 'data',
        icon: Target,
        relatedItems: ['models', 'accuracy']
      },
      {
        id: 'features',
        title: 'Data Features',
        description: 'Information we analyze for predictions',
        detail: 'We analyze 86 different factors per game, including team statistics, player performance, weather conditions, injury reports, and historical matchups. More relevant features help the models make more accurate predictions, similar to how a doctor considers many factors when diagnosing a patient.',
        level: 'intermediate',
        category: 'data',
        icon: Lightbulb,
        relatedItems: ['accuracy', 'confidence']
      }
    ]
  };

  const explanations = items || (context ? defaultExplanations[context] || [] : []);

  const levelColors = {
    beginner: 'bg-green-100 text-green-800',
    intermediate: 'bg-yellow-100 text-yellow-800',
    advanced: 'bg-red-100 text-red-800'
  };

  const categoryColors = {
    business: 'border-blue-200 bg-blue-50',
    technical: 'border-purple-200 bg-purple-50',
    data: 'border-green-200 bg-green-50',
    ml: 'border-orange-200 bg-orange-50'
  };

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const expandAll = () => {
    setExpandedItems(new Set(explanations.map(item => item.id)));
  };

  const collapseAll = () => {
    setExpandedItems(new Set());
  };

  const getFilteredExplanations = () => {
    if (showAllLevels) {
      return explanations;
    }
    return explanations.filter(item => item.level === currentLevel);
  };

  const filteredExplanations = getFilteredExplanations();

  const renderExplanationItem = (item: ExplanationItem) => {
    const isExpanded = expandedItems.has(item.id);
    const Icon = item.icon || Info;

    return (
      <Card
        key={item.id}
        className={`transition-all duration-200 ${categoryColors[item.category]} ${
          isExpanded ? 'shadow-md' : 'shadow-sm'
        }`}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-5 h-5 text-gray-600" />
              <div>
                <CardTitle className="text-lg">{item.title}</CardTitle>
                <p className="text-sm text-gray-600 mt-1">{item.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {showLevel && (
                <Badge variant="secondary" className={levelColors[item.level]}>
                  {item.level}
                </Badge>
              )}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpanded(item.id)}
                    className="p-1"
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{isExpanded ? 'Show less' : 'Show more'}</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </CardHeader>

        {isExpanded && (
          <CardContent className="pt-0">
            <div className="space-y-3">
              <div className="text-sm text-gray-700 leading-relaxed">
                {item.detail}
              </div>

              {item.relatedItems && item.relatedItems.length > 0 && (
                <div className="pt-3 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-600 mb-2">Related topics:</p>
                  <div className="flex flex-wrap gap-2">
                    {item.relatedItems.map((relatedId, index) => {
                      const relatedItem = explanations.find(exp => exp.id === relatedId);
                      if (relatedItem) {
                        return (
                          <Tooltip key={index}>
                            <TooltipTrigger asChild>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  if (!expandedItems.has(relatedId)) {
                                    toggleExpanded(relatedId);
                                  }
                                }}
                                className="text-xs"
                              >
                                {relatedItem.title}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{relatedItem.description}</p>
                            </TooltipContent>
                          </Tooltip>
                        );
                      }
                      return null;
                    })}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <TooltipProvider>
      <div className={`progressive-explanation ${className}`}>
        {/* Controls */}
        <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-600" />
              <h3 className="font-semibold">Help & Explanations</h3>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={expandAll}
                disabled={expandedItems.size === explanations.length}
              >
                Expand All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={collapseAll}
                disabled={expandedItems.size === 0}
              >
                Collapse All
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Detail Level:</span>
              <div className="flex gap-1">
                {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                  <Button
                    key={level}
                    variant={currentLevel === level && !showAllLevels ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => {
                      setCurrentLevel(level);
                      setShowAllLevels(false);
                    }}
                    className="text-xs"
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </Button>
                ))}
                <Button
                  variant={showAllLevels ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setShowAllLevels(!showAllLevels)}
                  className="text-xs"
                >
                  All Levels
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                Showing {filteredExplanations.length} of {explanations.length} explanations
              </span>
            </div>
          </div>
        </div>

        {/* Explanations */}
        <div className="space-y-4">
          {filteredExplanations.length > 0 ? (
            filteredExplanations.map(renderExplanationItem)
          ) : (
            <Card className="p-8 text-center">
              <HelpCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No explanations available</h3>
              <p className="text-sm text-gray-600">
                {context
                  ? `No explanations found for context: ${context}`
                  : 'No explanations to display'
                }
              </p>
            </Card>
          )}
        </div>

        {/* Tips */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-semibold text-blue-900">Tips for Using Explanations</h4>
              <ul className="text-sm text-blue-700 mt-2 space-y-1">
                <li>• Start with "Beginner" level for simple explanations</li>
                <li>• Click the down arrow to expand detailed information</li>
                <li>• Use "Related topics" links to explore connected concepts</li>
                <li>• Adjust the detail level based on your familiarity with the topic</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default ProgressiveExplanation;