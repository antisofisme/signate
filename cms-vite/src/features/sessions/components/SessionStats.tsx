/**
 * Session Stats Component
 * Display session statistics by device type
 */

import { Shield, Monitor, Smartphone, Tablet } from 'lucide-react';

interface SessionStatsProps {
  total: number;
  desktop: number;
  mobile: number;
  tablet: number;
}

export function SessionStats({ total, desktop, mobile, tablet }: SessionStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {total}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Sessions</div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <Monitor className="w-5 h-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {desktop}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Desktop</div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Smartphone className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {mobile}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Mobile</div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
            <Tablet className="w-5 h-5 text-orange-600 dark:text-orange-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {tablet}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Tablet</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SessionStats;
