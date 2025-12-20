import React, { useState } from 'react'
import MLSimulator from './components/MLSimulator'
import BowlAnalyticsDashboard from './components/analytics/BowlAnalyticsDashboard'
import UnifiedPostseasonDashboard from './components/UnifiedPostseasonDashboard'
import StakeholderDashboard from './components/StakeholderDashboard'
import DemoModeToggle from './components/DemoModeToggle'
import ProgressiveExplanation from './components/ProgressiveExplanation'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Button } from './components/ui/button'
import { Trophy, BarChart3, Calendar, Users } from 'lucide-react'

function App() {
  const [currentView, setCurrentView] = useState<'simulator' | 'bowl-analytics' | 'postseason' | 'stakeholder'>('postseason')
  const [demoMode, setDemoMode] = useState(false)
  const [showExplanations, setShowExplanations] = useState(true)

  return (
    <ErrorBoundary>
      {/* Navigation Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                🏈 Script Ohio 2.0 Analytics
              </h1>
              <div className="text-sm text-gray-600">
                College Football Prediction Platform • December 18, 2025
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant={currentView === 'postseason' ? 'default' : 'outline'}
                onClick={() => setCurrentView('postseason')}
                className="flex items-center space-x-2"
              >
                <Calendar className="h-4 w-4" />
                Postseason
              </Button>
              <Button
                variant={currentView === 'simulator' ? 'default' : 'outline'}
                onClick={() => setCurrentView('simulator')}
                className="flex items-center space-x-2"
              >
                <BarChart3 className="h-4 w-4" />
                Audit Dashboard
              </Button>
              <Button
                variant={currentView === 'bowl-analytics' ? 'default' : 'outline'}
                onClick={() => setCurrentView('bowl-analytics')}
                className="flex items-center space-x-2"
              >
                <Trophy className="h-4 w-4" />
                Bowl Analytics
              </Button>
              <Button
                variant={currentView === 'stakeholder' ? 'default' : 'outline'}
                onClick={() => setCurrentView('stakeholder')}
                className="flex items-center space-x-2"
              >
                <Users className="h-4 w-4" />
                Stakeholder View
              </Button>
            </div>
          </div>

          {/* Demo Mode Toggle */}
          <DemoModeToggle
            onDemoModeChange={setDemoMode}
            onAutoAdvanceChange={(autoAdvance) => {
              // Handle auto-advance if needed
              console.log('Auto-advance:', autoAdvance);
            }}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="min-h-screen">
        {demoMode ? (
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Stakeholder Dashboard in Demo Mode */}
            <StakeholderDashboard
              showExplanations={showExplanations}
              currentPhase={0} // This could be managed by demo state
            />

            {/* Progressive Explanations */}
            {showExplanations && (
              <div className="mt-8">
                <ProgressiveExplanation
                  context={currentView}
                  showLevel={true}
                />
              </div>
            )}
          </div>
        ) : (
          <>
            {currentView === 'postseason' ? (
              <UnifiedPostseasonDashboard />
            ) : currentView === 'simulator' ? (
              <MLSimulator />
            ) : currentView === 'stakeholder' ? (
              <div className="max-w-7xl mx-auto">
                <StakeholderDashboard showExplanations={showExplanations} />
              </div>
            ) : (
              <BowlAnalyticsDashboard />
            )}
          </>
        )}
      </div>
    </ErrorBoundary>
  )
}

export default App
