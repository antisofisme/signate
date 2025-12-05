/**
 * Service Registry
 * Centralized service management to replace window.* global pollution
 *
 * @features
 * - Type-safe service registration
 * - Lazy initialization support
 * - Clear dependency management
 * - Easy testing and mocking
 *
 * Note: Type imports removed to prevent circular dependencies during build.
 * Services are still type-safe through generic parameters at usage sites.
 */

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
// Using any to prevent circular dependencies, actual type safety comes from service implementations
export const getPlayerVideoJS = () => ServiceRegistry.get<any>('PlayerVideoJS');
export const getPlayerMediaCache = () => ServiceRegistry.get<any>('PlayerMediaCache');
export const getPlayerHeartbeat = () => ServiceRegistry.get<any>('PlayerHeartbeat');
export const getPlayerPlaylistSync = () => ServiceRegistry.get<any>('PlayerPlaylistSync');
export const getPlayerCommandExecutor = () => ServiceRegistry.get<any>('PlayerCommandExecutor');
export const getPlayerHealthReporter = () => ServiceRegistry.get<any>('PlayerHealthReporter');
export const getPlayerCapabilitiesReporter = () => ServiceRegistry.get<any>('PlayerCapabilitiesReporter');
export const getPlayerHLSCache = () => ServiceRegistry.get<any>('PlayerHLSCache');
export const getPlayerBackgroundAudio = () => ServiceRegistry.get<any>('PlayerBackgroundAudio');
export const getShellBootstrap = () => ServiceRegistry.get<any>('ShellBootstrap');
export const getShellRegistration = () => ServiceRegistry.get<any>('ShellRegistration');
export const getShellActivationPoll = () => ServiceRegistry.get<any>('ShellActivationPoll');
export const getShellActivationScreen = () => ServiceRegistry.get<any>('ShellActivationScreen');
export const getSharedWebSocket = () => ServiceRegistry.get<any>('SharedWebSocket');
export const getDeviceInfoPopup = () => ServiceRegistry.get<any>('DeviceInfoPopup');
export const getPlayerBehavioralMetrics = () => ServiceRegistry.get<any>('PlayerBehavioralMetrics');
export const getPlayerPerformanceMetrics = () => ServiceRegistry.get<any>('PlayerPerformanceMetrics');
