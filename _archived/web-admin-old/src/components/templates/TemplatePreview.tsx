import { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle, Monitor, CheckCircle } from 'lucide-react';
import templatesAPI from '../../services/api/templates';
import type { TemplatePreviewResponse } from '../../types/template';

interface TemplatePreviewProps {
  templateId?: string;
  content?: string;
  deviceId?: string;
  onDeviceChange?: (deviceId: string) => void;
  className?: string;
}

export default function TemplatePreview({
  templateId,
  content,
  deviceId,
  onDeviceChange,
  className = '',
}: TemplatePreviewProps) {
  const [preview, setPreview] = useState<TemplatePreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDevice, setSelectedDevice] = useState(deviceId || '');

  // Auto-refresh preview when content changes
  useEffect(() => {
    if (content || templateId) {
      handleRefresh();
    }
  }, [content, templateId, selectedDevice]);

  const handleRefresh = async () => {
    if (!content && !templateId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await templatesAPI.preview({
        template_id: templateId,
        content: content,
        device_id: selectedDevice || undefined,
        sample_data: getSampleData(),
      });

      setPreview(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate preview');
      setPreview(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDeviceChange = (newDeviceId: string) => {
    setSelectedDevice(newDeviceId);
    onDeviceChange?.(newDeviceId);
  };

  const getSampleData = () => {
    return {
      current_date: new Date().toISOString().split('T')[0],
      current_time: new Date().toLocaleTimeString(),
      current_datetime: new Date().toISOString(),
      day_name: new Date().toLocaleDateString('en-US', { weekday: 'long' }),
      month_name: new Date().toLocaleDateString('en-US', { month: 'long' }),
      year: new Date().getFullYear(),
      weather: {
        temperature: 28,
        condition: 'Sunny',
        humidity: 65,
        wind_speed: 12,
        location: 'Jakarta',
        icon: 'https://openweathermap.org/img/w/01d.png',
      },
      device: {
        name: 'Reception Display',
        location: 'Main Lobby',
        ip_address: '192.168.1.100',
        tags: ['lobby', 'main'],
      },
      firebird: {
        query_result: [
          { id: 1, name: 'Sample Item 1', value: 100 },
          { id: 2, name: 'Sample Item 2', value: 200 },
        ],
        connection_status: 'connected',
      },
    };
  };

  return (
    <div className={`flex flex-col h-full bg-white dark:bg-gray-800 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Monitor className="w-4 h-4" />
            Live Preview
          </h3>
          <button
            onClick={handleRefresh}
            disabled={loading || (!content && !templateId)}
            className="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Device Selector */}
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Preview Context (Optional)
          </label>
          <select
            value={selectedDevice}
            onChange={(e) => handleDeviceChange(e.target.value)}
            className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
          >
            <option value="">Sample Data</option>
            <option value="device-1">Device 1 - Lobby Display</option>
            <option value="device-2">Device 2 - Conference Room</option>
            <option value="device-3">Device 3 - Reception</option>
          </select>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400">Rendering preview...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-800 dark:text-red-400 mb-1">
                  Preview Error
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        {!loading && !error && preview && (
          <div className="space-y-4">
            {/* Rendered Output */}
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div
                className="prose prose-sm dark:prose-invert max-w-none"
                dangerouslySetInnerHTML={{ __html: preview.rendered }}
              />
            </div>

            {/* Variables Used */}
            {preview.variables_used && preview.variables_used.length > 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-green-800 dark:text-green-400 mb-2">
                      Variables Used ({preview.variables_used.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {preview.variables_used.map((variable) => (
                        <code
                          key={variable}
                          className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-400 rounded font-mono"
                        >
                          {variable}
                        </code>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Warnings */}
            {preview.warnings && preview.warnings.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-400 mb-2">
                      Warnings
                    </h4>
                    <ul className="list-disc list-inside space-y-1">
                      {preview.warnings.map((warning, index) => (
                        <li key={index} className="text-sm text-yellow-700 dark:text-yellow-300">
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Errors */}
            {preview.errors && preview.errors.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-red-800 dark:text-red-400 mb-2">
                      Errors
                    </h4>
                    <ul className="list-disc list-inside space-y-1">
                      {preview.errors.map((error, index) => (
                        <li key={index} className="text-sm text-red-700 dark:text-red-300">
                          {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {!loading && !error && !preview && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <Monitor className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">Start typing to see preview</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
