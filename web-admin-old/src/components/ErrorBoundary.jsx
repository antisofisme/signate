import { Component } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from './shared'

/**
 * ErrorBoundary Component
 * Catches JavaScript errors anywhere in child component tree
 *
 * Features:
 * - Catches errors during rendering, lifecycle methods, and constructors
 * - Logs error details to console
 * - Shows user-friendly fallback UI
 * - Provides error recovery actions (reload, go home)
 * - Does NOT catch errors in event handlers (use try-catch for those)
 *
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error) {
    // Update state so next render shows fallback UI
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error)
    console.error('Error details:', errorInfo)

    // Store error details in state
    this.setState({
      error,
      errorInfo
    })

    // You could send error to logging service here
    // Example: logErrorToService(error, errorInfo)
  }

  handleReload = () => {
    // Reset error state and reload page
    window.location.reload()
  }

  handleGoHome = () => {
    // Reset error state and navigate to home
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      // Render fallback UI
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-800 dark:bg-gray-900 flex items-center justify-center p-6">
          <div className="max-w-2xl w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-10 h-10 text-red-600" />
              </div>
            </div>

            {/* Error Title */}
            "<h1 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-4">
              Oops! Something went wrong
            </h1>

            {/* Error Description */}
            <p className="text-gray-600 text-center mb-6">
              We're sorry for the inconvenience. The application encountered an unexpected error.
            </p>

            {/* Error Details (Development Mode) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg border border-gray-200">
                <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Error Details:</h2>
                <pre className="text-xs text-red-600 overflow-auto max-h-48">
                  {this.state.error.toString()}
                </pre>
                {this.state.errorInfo && (
                  <>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mt-3 mb-2">Component Stack:</h3>
                    <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto max-h-48">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 justify-center">
              <Button
                variant="primary"
                leftIcon={<RefreshCw className="w-5 h-5" />}
                onClick={this.handleReload}
              >
                Reload Page
              </Button>
              <Button
                variant="secondary"
                leftIcon={<Home className="w-5 h-5" />}
                onClick={this.handleGoHome}
              >
                Go to Home
              </Button>
            </div>

            {/* Help Text */}
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center mt-6">
              If this problem persists, please contact support.
            </p>
          </div>
        </div>
      )
    }

    // No error, render children normally
    return this.props.children
  }
}

export default ErrorBoundary
