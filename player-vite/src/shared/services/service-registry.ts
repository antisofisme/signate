/**
 * Service Registry
 * Centralized service management to replace window.* global pollution
 *
 * @features
 * - Type-safe service registration
 * - Lazy initialization support
 * - Clear dependency management
 * - Easy testing and mocking
 */

import type {
  PlayerVideoJS,
  PlayerMediaCache,
  Heartbeat,
  PlaylistSync,
} from '@player/types/player.types';
import type {
  ShellRegistration,
  ShellActivationPoll,
  ShellBootstrap,
} from '@shell/types/shell.types';

type ServiceFactory<T> = () => T;

class ServiceRegistryClass {
  private services = new Map<string, any>();
  private factories = new Map<string, ServiceFactory<any>>();

  /**
   * Register a service instance
   */
  register<T>(name: string, service: T): void {
    this.services.set(name, service);
  }

  /**
   * Register a lazy-loaded service factory
   */
  registerFactory<T>(name: string, factory: ServiceFactory<T>): void {
    this.factories.set(name, factory);
  }

  /**
   * Get a service (will initialize if lazy-loaded)
   */
  get<T>(name: string): T | undefined {
    // Check if already instantiated
    if (this.services.has(name)) {
      return this.services.get(name) as T;
    }

    // Try to instantiate from factory
    if (this.factories.has(name)) {
      const factory = this.factories.get(name)!;
      const instance = factory();
      this.services.set(name, instance);
      return instance as T;
    }

    return undefined;
  }

  /**
   * Check if service exists
   */
  has(name: string): boolean {
    return this.services.has(name) || this.factories.has(name);
  }

  /**
   * Clear all services (for testing)
   */
  clear(): void {
    this.services.clear();
    this.factories.clear();
  }

  /**
   * Get all registered service names
   */
  getServiceNames(): string[] {
    return [
      ...Array.from(this.services.keys()),
      ...Array.from(this.factories.keys())
    ];
  }
}

// Export singleton
export const ServiceRegistry = new ServiceRegistryClass();

// Type-safe getters for common services
export const getPlayerVideoJS = () => ServiceRegistry.get<PlayerVideoJS>('PlayerVideoJS');
export const getPlayerMediaCache = () => ServiceRegistry.get<PlayerMediaCache>('PlayerMediaCache');
export const getPlayerHeartbeat = () => ServiceRegistry.get<Heartbeat>('PlayerHeartbeat');
export const getPlayerPlaylistSync = () => ServiceRegistry.get<PlaylistSync>('PlayerPlaylistSync');
export const getPlayerCommandExecutor = () => ServiceRegistry.get<any>('PlayerCommandExecutor'); // TODO: Add PlayerCommandExecutor interface
export const getPlayerHealthReporter = () => ServiceRegistry.get<any>('PlayerHealthReporter'); // TODO: Add PlayerHealthReporter interface
export const getPlayerHLSCache = () => ServiceRegistry.get<any>('PlayerHLSCache'); // TODO: Add PlayerHLSCache interface
export const getPlayerBackgroundAudio = () => ServiceRegistry.get<any>('PlayerBackgroundAudio'); // TODO: Add PlayerBackgroundAudio interface
export const getShellBootstrap = () => ServiceRegistry.get<ShellBootstrap>('ShellBootstrap');
export const getShellRegistration = () => ServiceRegistry.get<ShellRegistration>('ShellRegistration');
export const getShellActivationPoll = () => ServiceRegistry.get<ShellActivationPoll>('ShellActivationPoll');
export const getShellActivationScreen = () => ServiceRegistry.get<any>('ShellActivationScreen'); // TODO: Add ShellActivationScreen interface
export const getSharedWebSocket = () => ServiceRegistry.get<any>('SharedWebSocket'); // TODO: Add SharedWebSocket interface
export const getDeviceInfoPopup = () => ServiceRegistry.get<any>('DeviceInfoPopup'); // TODO: Add DeviceInfoPopup interface
