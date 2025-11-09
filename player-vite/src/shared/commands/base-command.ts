/**
 * Base Command Class
 *
 * @class BaseCommand
 * @description
 * Abstract base class for all remote commands.
 * Implements Command Pattern for modular command execution.
 *
 * @features
 * - Timeout protection (30s max)
 * - Validation framework
 * - Error handling
 * - WebOS detection
 * - Browser fallbacks
 *
 * @usage
 * ```typescript
 * class MyCommand extends BaseCommand {
 *   async execute(parameters: any): Promise<any> {
 *     // Your implementation
 *   }
 * }
 * ```
 */

export interface CommandResult {
  success: boolean;
  [key: string]: any;
}

export interface WebOSService {
  request: (service: string, options: {
    method: string;
    parameters?: any;
    onSuccess?: (res: any) => void;
    onFailure?: (err: any) => void;
  }) => void;
}

export interface WebOSWindow extends Window {
  webOS?: {
    service: WebOSService;
    platformVersion?: string;
    deviceInfo?: any;
  };
}

export abstract class BaseCommand {
  /**
   * Command timeout (30 seconds max)
   */
  static readonly TIMEOUT = 30000;

  protected name: string;
  private startTime: number | null = null;

  /**
   * Create command instance
   * @param name - Command name
   */
  constructor(name: string) {
    this.name = name;
  }

  /**
   * Execute command with timeout protection
   *
   * @param parameters - Command parameters
   * @returns Execution result
   */
  async executeWithTimeout(parameters?: any): Promise<CommandResult> {
    this.startTime = Date.now();

    // Create timeout promise
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Command execution timeout after ${BaseCommand.TIMEOUT}ms`));
      }, BaseCommand.TIMEOUT);
    });

    // Race between execution and timeout
    return Promise.race([
      this.execute(parameters),
      timeoutPromise
    ]);
  }

  /**
   * Execute command (to be overridden by subclasses)
   *
   * @param parameters - Command parameters
   * @returns Execution result
   * @abstract
   */
  abstract execute(parameters?: any): Promise<CommandResult>;

  /**
   * Validate command parameters (to be overridden by subclasses)
   *
   * @param parameters - Command parameters
   * @throws Error if validation fails
   */
  validate(parameters?: any): void {
    // Default: no validation
    // Subclasses should override this
  }

  /**
   * Check if running on WebOS TV
   */
  protected isWebOS(): boolean {
    const win = window as WebOSWindow;
    return typeof win.webOS !== 'undefined' && !!win.webOS.service;
  }

  /**
   * Check if running in browser (non-WebOS)
   */
  protected isBrowser(): boolean {
    return !this.isWebOS();
  }

  /**
   * Get execution duration in milliseconds
   */
  protected getDuration(): number {
    if (!this.startTime) return 0;
    return Date.now() - this.startTime;
  }

  /**
   * Create WebOS service request
   *
   * @param service - Luna service URI
   * @param method - Service method
   * @param parameters - Method parameters
   * @returns Service response
   */
  protected webOSRequest(service: string, method: string, parameters: any = {}): Promise<any> {
    if (!this.isWebOS()) {
      throw new Error('WebOS API not available');
    }

    const win = window as WebOSWindow;

    return new Promise((resolve, reject) => {
      win.webOS!.service.request(service, {
        method,
        parameters,
        onSuccess: (res) => resolve(res),
        onFailure: (err) => reject(new Error(err.errorText || 'Unknown WebOS error'))
      });
    });
  }

  /**
   * Log command execution
   *
   * @param message - Log message
   * @param data - Optional data to log
   */
  protected log(message: string, data?: any): void {
    const prefix = `[Command:${this.name}]`;
    if (data) {
      console.log(prefix, message, data);
    } else {
      console.log(prefix, message);
    }
  }

  /**
   * Log command error
   *
   * @param message - Error message
   * @param error - Optional error object
   */
  protected logError(message: string, error?: Error): void {
    const prefix = `[Command:${this.name}]`;
    if (error) {
      console.error(prefix, message, error);
    } else {
      console.error(prefix, message);
    }
  }
}
