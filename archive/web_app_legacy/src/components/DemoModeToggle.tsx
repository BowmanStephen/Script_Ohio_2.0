import React, { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Play, Pause, Settings, Users } from 'lucide-react';

interface DemoModeProps {
  onDemoModeChange?: (enabled: boolean) => void;
  onAutoAdvanceChange?: (enabled: boolean) => void;
  className?: string;
}

export interface DemoState {
  mode: 'normal' | 'presentation';
  autoAdvance: boolean;
  currentPhase: number;
  showExplanations: boolean;
  isPlaying: boolean;
}

const DemoModeToggle: React.FC<DemoModeProps> = ({
  onDemoModeChange,
  onAutoAdvanceChange,
  className = ''
}) => {
  const [demoState, setDemoState] = useState<DemoState>({
    mode: 'normal',
    autoAdvance: false,
    currentPhase: 0,
    showExplanations: true,
    isPlaying: false
  });

  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const demoPhases = [
    'Welcome & Overview',
    'Data Ingestion',
    'Agent Intelligence',
    'ML Predictions',
    'Visual Analytics',
    'Summary & Q&A'
  ];

  useEffect(() => {
    // Save demo state to localStorage
    localStorage.setItem('demoState', JSON.stringify(demoState));
    onDemoModeChange?.(demoState.mode === 'presentation');
    onAutoAdvanceChange?.(demoState.autoAdvance);
  }, [demoState, onDemoModeChange, onAutoAdvanceChange]);

  useEffect(() => {
    // Load demo state from localStorage
    const savedState = localStorage.getItem('demoState');
    if (savedState) {
      try {
        setDemoState(JSON.parse(savedState));
      } catch (error) {
        console.warn('Failed to load demo state:', error);
      }
    }
  }, []);

  const toggleDemoMode = () => {
    setDemoState(prev => ({
      ...prev,
      mode: prev.mode === 'normal' ? 'presentation' : 'normal',
      currentPhase: prev.mode === 'normal' ? 0 : prev.currentPhase
    }));
  };

  const toggleAutoAdvance = () => {
    setDemoState(prev => ({
      ...prev,
      autoAdvance: !prev.autoAdvance
    }));
  };

  const toggleExplanations = () => {
    setDemoState(prev => ({
      ...prev,
      showExplanations: !prev.showExplanations
    }));
  };

  const startAutoPlay = () => {
    setDemoState(prev => ({
      ...prev,
      isPlaying: true,
      currentPhase: 0
    }));

    // Auto-advance through phases
    const advancePhase = () => {
      setDemoState(prev => {
        if (prev.currentPhase < demoPhases.length - 1) {
          return { ...prev, currentPhase: prev.currentPhase + 1 };
        } else {
          return { ...prev, isPlaying: false, currentPhase: 0 };
        }
      });
    };

    // Set up interval for auto-advancement
    const interval = setInterval(() => {
      setDemoState(current => {
        if (current.isPlaying && current.autoAdvance) {
          advancePhase();
        }
        if (!current.isPlaying) {
          clearInterval(interval);
        }
        return current;
      });
    }, 10000); // 10 seconds per phase
  };

  const stopAutoPlay = () => {
    setDemoState(prev => ({
      ...prev,
      isPlaying: false
    }));
  };

  const goToPhase = (phaseIndex: number) => {
    setDemoState(prev => ({
      ...prev,
      currentPhase: phaseIndex
    }));
  };

  return (
    <TooltipProvider>
      <div className={`demo-mode-toggle ${className}`}>
        {/* Main Toggle */}
        <div className="flex items-center gap-3 p-4 bg-white rounded-lg shadow-sm border">
          <Users className="w-5 h-5 text-blue-600" />
          <span className="font-medium">Stakeholder Mode</span>
          <Switch
            checked={demoState.mode === 'presentation'}
            onCheckedChange={toggleDemoMode}
          />
          <Badge variant={demoState.mode === 'presentation' ? 'default' : 'secondary'}>
            {demoState.mode === 'presentation' ? 'DEMO MODE' : 'NORMAL'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsConfigOpen(!isConfigOpen)}
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>

        {/* Demo Configuration Panel */}
        {isConfigOpen && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <h3 className="font-semibold mb-3">Demo Configuration</h3>

            <div className="space-y-3">
              {/* Auto-Advance Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Auto-Advance</label>
                  <p className="text-xs text-gray-600">
                    Automatically move through demo phases
                  </p>
                </div>
                <Switch
                  checked={demoState.autoAdvance}
                  onCheckedChange={toggleAutoAdvance}
                />
              </div>

              {/* Explanations Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Show Explanations</label>
                  <p className="text-xs text-gray-600">
                    Display helpful tooltips and explanations
                  </p>
                </div>
                <Switch
                  checked={demoState.showExplanations}
                  onCheckedChange={toggleExplanations}
                />
              </div>

              {/* Playback Controls */}
              {demoState.mode === 'presentation' && (
                <div className="flex items-center gap-2 pt-2 border-t">
                  <Button
                    size="sm"
                    onClick={demoState.isPlaying ? stopAutoPlay : startAutoPlay}
                    variant={demoState.isPlaying ? 'secondary' : 'default'}
                  >
                    {demoState.isPlaying ? (
                      <>
                        <Pause className="w-4 h-4 mr-2" />
                        Pause Demo
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Start Demo
                      </>
                    )}
                  </Button>
                </div>
              )}

              {/* Phase Navigation */}
              {demoState.mode === 'presentation' && (
                <div className="pt-2 border-t">
                  <label className="text-sm font-medium mb-2 block">Demo Phases</label>
                  <div className="grid grid-cols-2 gap-2">
                    {demoPhases.map((phase, index) => (
                      <Button
                        key={index}
                        size="sm"
                        variant={demoState.currentPhase === index ? 'default' : 'outline'}
                        onClick={() => goToPhase(index)}
                        className="text-xs h-8"
                        disabled={demoState.isPlaying}
                      >
                        <span className="truncate">{phase}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Demo Status Indicator */}
        {demoState.mode === 'presentation' && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  demoState.isPlaying ? 'bg-green-500 animate-pulse' : 'bg-blue-500'
                }`} />
                <span className="text-sm font-medium text-blue-900">
                  Demo Active
                </span>
              </div>
              <Tooltip>
                <TooltipTrigger>
                  <Badge variant="outline" className="text-xs">
                    Phase {demoState.currentPhase + 1}/{demoPhases.length}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Current: {demoPhases[demoState.currentPhase]}</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {demoState.showExplanations && (
              <p className="text-xs text-blue-700 mt-2">
                💡 Tips and explanations are enabled to help non-technical users understand the system.
              </p>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  );
};

export default DemoModeToggle;