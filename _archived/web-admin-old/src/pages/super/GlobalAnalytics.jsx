import { TrendingUp, Building2, Monitor, Users, Activity } from 'lucide-react'

/**
 * GlobalAnalytics Component
 * Global analytics and insights across all tenants
 *
 * Uses mock data - ready to connect to API
 */
export default function GlobalAnalytics() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Global Analytics</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Insights and metrics across all organizations</p>
      </div>

      {/* Coming Soon */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border border-purple-200 dark:border-purple-800 p-12 text-center">
        <TrendingUp className="w-16 h-16 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Analytics Dashboard</h2>
        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Comprehensive analytics dashboard with charts, graphs, and insights will be available here.
        </p>
      </div>

      {/* Placeholder Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Organizations Growth</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">Chart placeholder</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Device Distribution</h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">Chart placeholder</p>
          </div>
        </div>
      </div>
    </div>
  )
}
