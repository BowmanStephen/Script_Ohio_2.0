import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  onReset?: () => void;
}

/**
 * Error fallback UI component
 * 
 * Displays a user-friendly error message when an error boundary catches an error.
 * Provides options to reset the error state or reload the page.
 */
export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, errorInfo, onReset }) => {
  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="max-w-2xl w-full border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive text-2xl">
            ⚠️ Something went wrong
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            We're sorry, but something unexpected happened. The error has been logged
            and we'll look into it.
          </p>

          {error && (
            <div className="bg-muted p-4 rounded-lg border border-border">
              <p className="font-semibold text-sm mb-2">Error Details:</p>
              <p className="text-sm font-mono text-destructive break-words">
                {error.message || 'Unknown error occurred'}
              </p>
            </div>
          )}

          {process.env.NODE_ENV === 'development' && errorInfo && (
            <details className="bg-muted p-4 rounded-lg border border-border">
              <summary className="cursor-pointer font-semibold text-sm mb-2">
                Component Stack (Development Only)
              </summary>
              <pre className="text-xs overflow-auto max-h-64 mt-2 font-mono">
                {errorInfo.componentStack}
              </pre>
            </details>
          )}

          <div className="flex gap-4 pt-4">
            {onReset && (
              <Button onClick={onReset} variant="default">
                Try Again
              </Button>
            )}
            <Button onClick={handleReload} variant="outline">
              Reload Page
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};


