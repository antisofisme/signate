/**
 * PMS Config State Management Hook
 * Manages state and handlers for PMS configuration page
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import {
  usePMSConfig,
  useCreatePMSConfig,
  useUpdatePMSConfig,
  useDeletePMSConfig,
  usePMSStats,
} from './usePMS';
import type { PMSProvider, PMSConnectionConfig, PMSSyncConfig } from '../types/pms.types';

export function usePMSConfigState() {
  const { data: config, isLoading } = usePMSConfig();
  const { data: stats } = usePMSStats();
  const createConfig = useCreatePMSConfig();
  const updateConfig = useUpdatePMSConfig();
  const deleteConfig = useDeletePMSConfig();

  // Get available devices for room mapping
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/devices');
      return response.data;
    },
  });

  const [activeTab, setActiveTab] = useState<'config' | 'guests' | 'rooms'>('config');
  const [provider, setProvider] = useState<PMSProvider>('opera');
  const [connectionConfig, setConnectionConfig] = useState<PMSConnectionConfig>({
    host: '',
    port: 443,
    protocol: 'https',
    timeout: 30,
    retry_attempts: 3,
    ssl_verify: true,
  });
  const [syncConfig, setSyncConfig] = useState<PMSSyncConfig>({
    auto_sync_enabled: true,
    sync_interval_minutes: 30,
    sync_guests: true,
    sync_rooms: true,
    sync_reservations: false,
  });

  // Initialize state from config
  useEffect(() => {
    if (config) {
      setProvider(config.provider);
      setConnectionConfig(config.connection_config);
      setSyncConfig(config.sync_config);
    }
  }, [config]);

  const handleSave = () => {
    const data = {
      provider,
      connection_config: connectionConfig,
      sync_config: syncConfig,
    };

    if (config) {
      updateConfig.mutate(data);
    } else {
      createConfig.mutate(data);
    }
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete the PMS configuration? This cannot be undone.')) {
      deleteConfig.mutate();
    }
  };

  return {
    // Data
    config,
    stats,
    devices: devicesData?.devices || [],
    isLoading,

    // State
    activeTab,
    provider,
    connectionConfig,
    syncConfig,

    // Setters
    setActiveTab,
    setProvider,
    setConnectionConfig,
    setSyncConfig,

    // Handlers
    handleSave,
    handleDelete,

    // Mutation states
    isSaving: createConfig.isPending || updateConfig.isPending,
    isDeleting: deleteConfig.isPending,
  };
}
