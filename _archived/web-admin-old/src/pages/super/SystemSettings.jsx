import { Settings, Database, Server, HardDrive, Activity } from 'lucide-react'

/**
 * SystemSettings Component
 * System-wide settings and maintenance
 *
 * Uses mock data - ready to connect to API
 */
export default function SystemSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Configure system-wide settings and maintenance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Database */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Database</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Status</span>
              <span className="text-green-600 dark:text-green-400 font-medium">Healthy</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Connections</span>
              <span className="text-gray-900 dark:text-white font-medium">125/500</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Size</span>
              <span className="text-gray-900 dark:text-white font-medium">24.5 GB</span>
            </div>
          </div>
        </div>

        {/* Storage */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center gap-3 mb-4">
            <HardDrive className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Storage</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Status</span>
              <span className="text-yellow-600 dark:text-yellow-400 font-medium">Warning</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Used</span>
              <span className="text-gray-900 dark:text-white font-medium">850 GB / 1 TB</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="bg-yellow-500 h-2 rounded-full" style={{width: '85%'}}></div>
            </div>
          </div>
        </div>

        {/* Server */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Server className="w-6 h-6 text-green-600 dark:text-green-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Server</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Uptime</span>
              <span className="text-green-600 dark:text-green-400 font-medium">99.9%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">CPU Usage</span>
              <span className="text-gray-900 dark:text-white font-medium">45%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Memory</span>
              <span className="text-gray-900 dark:text-white font-medium">8.2/16 GB</span>
            </div>
          </div>
        </div>

        {/* Monitoring */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-300 dark:border-gray-600 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Monitoring</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Active Services</span>
              <span className="text-green-600 dark:text-green-400 font-medium">12/12</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Avg Response</span>
              <span className="text-gray-900 dark:text-white font-medium">245ms</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Last Check</span>
              <span className="text-gray-900 dark:text-white font-medium">30s ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
