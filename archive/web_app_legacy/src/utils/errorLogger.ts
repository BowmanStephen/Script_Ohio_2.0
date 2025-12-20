/**
 * Error logging utility
 * 
 * Centralized error logging that can be extended to integrate with
 * error tracking services like Sentry, LogRocket, etc.
 */

interface ErrorContext {
  componentStack?: string;
  errorBoundary?: boolean;
  [key: string]: unknown;
}

/**
 * Log an error with optional context
 * 
 * @param error - The error object to log
 * @param context - Additional context about the error
 */
export function logError(error: Error, context?: ErrorContext): void {
  const errorData = {
    message: error.message,
    stack: error.stack,
    name: error.name,
    timestamp: new Date().toISOString(),
    ...context,
  };

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('Error logged:', errorData);
  }

  // TODO: Integrate with error tracking service (e.g., Sentry)
  // Example:
  // if (window.Sentry) {
  //   window.Sentry.captureException(error, {
  //     contexts: { custom: context },
  //   });
  // }

  // In production, you might want to send to a logging service
  // Example:
  // fetch('/api/log-error', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(errorData),
  // }).catch(() => {
  //   // Silently fail if logging service is unavailable
  // });
}

/**
 * Log a warning message
 * 
 * @param message - Warning message
 * @param context - Additional context
 */
export function logWarning(message: string, context?: Record<string, unknown>): void {
  if (process.env.NODE_ENV === 'development') {
    console.warn('Warning:', message, context);
  }

  // TODO: Integrate with error tracking service
}

/**
 * Log an info message
 * 
 * @param message - Info message
 * @param context - Additional context
 */
export function logInfo(message: string, context?: Record<string, unknown>): void {
  if (process.env.NODE_ENV === 'development') {
    console.info('Info:', message, context);
  }
}


