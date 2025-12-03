/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 *
 * Features:
 * - Catches render errors, lifecycle errors, and errors in constructors
 * - Displays user-friendly error message
 * - Option to retry/reload
 * - Logs errors for debugging
 *
 * @usage
 * <ErrorBoundary fallback={<CustomErrorUI />}>
 *   <ComponentThatMightError />
 * </ErrorBoundary>
 */

import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import Button from './common/Button';

// ============================================================================
// TYPES
// ============================================================================

interface ErrorBoundaryProps {
  /** Child components to render */
  children: ReactNode;
  /** Custom fallback UI (optional) */
  fallback?: ReactNode;
  /** Callback when error occurs */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Show reset button */
  showReset?: boolean;
  /** Custom reset handler */
  onReset?: () => void;
  /** Error boundary name for logging */
  name?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

// ============================================================================
// DEFAULT FALLBACK UI
// ============================================================================

interface DefaultFallbackProps {
  error: Error | null;
  onReset?: () => void;
  showReset?: boolean;
}

function DefaultFallback({ error, onReset, showReset = true }: DefaultFallbackProps) {
  const handleReload = () => {
    window.location.reload();
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-[400px] flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
        {/* Error Icon */}
        <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
          <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" aria-hidden="true" />
        </div>

        {/* Error Title */}
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Something went wrong
        </h2>

        {/* Error Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          An unexpected error occurred. Please try again or contact support if the problem persists.
        </p>

        {/* Error Details (Development) */}
        {import.meta.env.DEV && error && (
          <details className="mb-4 text-left">
            <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
              Error Details
            </summary>
            <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-900 rounded text-xs text-red-600 dark:text-red-400 overflow-auto max-h-40">
              {error.message}
              {error.stack && `\n\n${error.stack}`}
            </pre>
          </details>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {showReset && onReset && (
            <Button
              onClick={onReset}
              leftIcon={<RefreshCw className="w-4 h-4" aria-hidden="true" />}
              aria-label="Try again"
            >
              Try Again
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={handleReload}
            leftIcon={<RefreshCw className="w-4 h-4" aria-hidden="true" />}
            aria-label="Reload page"
          >
            Reload Page
          </Button>
          <Button
            variant="secondary"
            onClick={handleGoHome}
            leftIcon={<Home className="w-4 h-4" aria-hidden="true" />}
            aria-label="Go to home page"
          >
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// ERROR BOUNDARY CLASS
// ============================================================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error
    const boundaryName = this.props.name || 'ErrorBoundary';
    console.error(`[${boundaryName}] Caught error:`, error);
    console.error(`[${boundaryName}] Error info:`, errorInfo);

    // Update state with error info
    this.setState({ errorInfo });

    // Call optional error callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to send to error tracking service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  handleReset = (): void => {
    // Reset error state
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    // Call custom reset handler if provided
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback, showReset = true } = this.props;

    if (hasError) {
      // Render custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Render default fallback
      return (
        <DefaultFallback
          error={error}
          onReset={this.handleReset}
          showReset={showReset}
        />
      );
    }

    return children;
  }
}

// ============================================================================
// PAGE ERROR BOUNDARY (Full page error)
// ============================================================================

interface PageErrorBoundaryProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

/**
 * Page-level error boundary with full-page fallback UI
 */
export function PageErrorBoundary({ children, onError }: PageErrorBoundaryProps) {
  return (
    <ErrorBoundary
      name="PageErrorBoundary"
      onError={onError}
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <DefaultFallback error={null} showReset={false} />
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// ============================================================================
// COMPONENT ERROR BOUNDARY (Inline error)
// ============================================================================

interface ComponentErrorBoundaryProps {
  children: ReactNode;
  fallbackMessage?: string;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

/**
 * Component-level error boundary with minimal inline fallback
 */
export function ComponentErrorBoundary({
  children,
  fallbackMessage = 'Failed to load component',
  onError,
}: ComponentErrorBoundaryProps) {
  return (
    <ErrorBoundary
      name="ComponentErrorBoundary"
      onError={onError}
      fallback={
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
            <AlertTriangle className="w-4 h-4" aria-hidden="true" />
            <span className="text-sm font-medium">{fallbackMessage}</span>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default ErrorBoundary;
