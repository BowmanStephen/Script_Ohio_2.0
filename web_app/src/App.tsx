import React from 'react'
import MLSimulator from './components/MLSimulator'
import { ErrorBoundary } from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <MLSimulator />
    </ErrorBoundary>
  )
}

export default App
