/**
 * Portal Viewer
 * Unified menu portal with tab navigation for all organization menus
 */

import './portal-viewer.css';
import { PortalResponse, PortalMenu, MENU_TYPE_LABELS, PortalViewerConfig } from './types';
import { MenuViewer } from '../menu/menu-viewer';

// Color utility function
function getContrastColor(hexColor: string): string {
  if (!hexColor || hexColor.length < 7) return 'white';
  try {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#1e293b' : '#ffffff';
  } catch {
    return 'white';
  }
}

export class PortalViewer {
  private container: HTMLElement;
  private config: PortalViewerConfig;
  private portalData: PortalResponse | null = null;
  private currentMenuIndex: number = 0;
  private menuViewer: MenuViewer | null = null;
  private menuContentContainer: HTMLElement | null = null;

  // Memory leak prevention - track resize handler for cleanup
  private resizeHandler: (() => void) | null = null;
  private isDestroyed = false;

  constructor(container: HTMLElement, config: PortalViewerConfig) {
    this.container = container;
    this.config = config;
    // Bind resize handler to preserve 'this' context
    this.resizeHandler = () => this.updateHeaderHeight();
  }

  /**
   * Load portal data and render
   */
  async load(): Promise<void> {
    console.log('[Portal] Loading portal:', this.config.portalSlug);

    // Add portal-mode-active class to html/body to hide player elements
    document.documentElement.classList.add('portal-mode-active');
    document.body.classList.add('portal-mode-active');

    try {
      // Fetch portal data from API
      const response = await fetch(
        `${this.config.apiBaseUrl}/api/v1/public/menu/portal/${this.config.portalSlug}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          this.renderError('Portal tidak ditemukan');
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      if (!result.success || !result.data) {
        throw new Error('Invalid API response');
      }

      this.portalData = result.data;
      console.log('[Portal] Loaded portal data:', this.portalData);

      // Render portal UI
      this.render();

    } catch (error) {
      console.error('[Portal] Error loading portal:', error);
      this.renderError('Gagal memuat portal menu');
    }
  }

  /**
   * Render the portal UI
   */
  private render(): void {
    if (!this.portalData) return;

    const { organization, menus } = this.portalData;

    // Check if there are any menus
    if (menus.length === 0) {
      this.renderError('Belum ada menu yang tersedia');
      return;
    }

    // Get colors from first menu (60-30-10 scheme)
    const firstMenu = menus[0];
    const primaryColor = firstMenu.primary_color || '#0f172a';
    const secondaryColor = firstMenu.secondary_color || '#1e293b';
    const themeColor = firstMenu.theme_color || '#3b82f6';

    // Auto-calculate text colors
    const primaryTextColor = getContrastColor(primaryColor);
    const secondaryTextColor = getContrastColor(secondaryColor);
    const themeTextColor = getContrastColor(themeColor);

    // Build CSS variables
    const cssVars = `
      --primary-color: ${primaryColor};
      --secondary-color: ${secondaryColor};
      --theme-color: ${themeColor};
      --primary-text-color: ${primaryTextColor};
      --secondary-text-color: ${secondaryTextColor};
      --theme-text-color: ${themeTextColor};
    `.replace(/\s+/g, ' ').trim();

    // Build portal HTML
    this.container.innerHTML = `
      <div class="portal-viewer" style="${cssVars}">
        <header class="portal-viewer__header">
          ${organization.logo_url ? `
            <img
              src="${organization.logo_url}"
              alt="${organization.name}"
              class="portal-viewer__logo"
            />
          ` : ''}
          <h1 class="portal-viewer__title">${organization.name}</h1>
          <nav class="portal-viewer__tabs" role="tablist">
            ${this.renderTabs(menus)}
          </nav>
        </header>
        <main class="portal-viewer__content" id="portal-menu-content">
          <div class="portal-viewer__loading">
            <div class="portal-viewer__spinner"></div>
            <p>Memuat menu...</p>
          </div>
        </main>
      </div>
    `;

    // Store reference to content container
    this.menuContentContainer = document.getElementById('portal-menu-content');

    // Calculate and set portal header height for sticky category menu
    this.updateHeaderHeight();

    // Attach tab click handlers
    this.attachTabHandlers();

    // Listen for resize to update header height - TRACKED for cleanup
    if (this.resizeHandler) {
      window.addEventListener('resize', this.resizeHandler);
    }

    // Load first menu
    this.loadMenu(0);
  }

  /**
   * Render tab buttons for each menu (styled like category tabs, no emoji)
   */
  private renderTabs(menus: PortalMenu[]): string {
    return menus.map((menu, index) => `
      <button
        type="button"
        class="portal-viewer__tab ${index === this.currentMenuIndex ? 'portal-viewer__tab--active' : ''}"
        data-menu-index="${index}"
        role="tab"
        aria-selected="${index === this.currentMenuIndex}"
        aria-controls="portal-menu-content"
      >
        ${this.getMenuTypeLabel(menu.menu_type)}
      </button>
    `).join('');
  }

  /**
   * Get display label for menu type
   */
  private getMenuTypeLabel(menuType: string): string {
    return MENU_TYPE_LABELS[menuType] || MENU_TYPE_LABELS.other;
  }

  /**
   * Attach click handlers to tab buttons
   */
  private attachTabHandlers(): void {
    const tabs = this.container.querySelectorAll('.portal-viewer__tab');

    tabs.forEach((tab) => {
      tab.addEventListener('click', (e) => {
        const button = e.currentTarget as HTMLButtonElement;
        const index = parseInt(button.dataset.menuIndex || '0', 10);

        if (index !== this.currentMenuIndex) {
          this.loadMenu(index);
        }
      });
    });
  }

  /**
   * Load a specific menu by index
   */
  private async loadMenu(index: number): Promise<void> {
    if (!this.portalData || !this.menuContentContainer) return;

    const menu = this.portalData.menus[index];
    if (!menu) return;

    console.log('[Portal] Loading menu:', menu.name, menu.public_url_code);

    // CRITICAL: Destroy previous MenuViewer to prevent memory leaks
    if (this.menuViewer) {
      console.log('[Portal] Destroying previous menu viewer');
      this.menuViewer.destroy();
      this.menuViewer = null;
    }

    // Update current index
    this.currentMenuIndex = index;

    // Update active tab styling
    this.updateActiveTabs();

    // Show loading state
    this.menuContentContainer.innerHTML = `
      <div class="portal-viewer__loading">
        <div class="portal-viewer__spinner"></div>
        <p>Memuat ${menu.name}...</p>
      </div>
    `;

    // Create new container for menu viewer with unique ID
    const menuContainerId = `portal-menu-viewer-${index}`;
    this.menuContentContainer.innerHTML = `<div id="${menuContainerId}" class="portal-viewer__menu-container"></div>`;

    try {
      // Initialize menu viewer with the menu's public code
      this.menuViewer = new MenuViewer({
        apiBaseUrl: this.config.apiBaseUrl,
        publicCode: menu.public_url_code
      });

      // Load the menu into the container
      await this.menuViewer.init(menuContainerId);
    } catch (error) {
      console.error('[Portal] Error loading menu:', error);
      this.menuContentContainer.innerHTML = `
        <div class="portal-viewer__error">
          <span class="portal-viewer__error-icon">⚠️</span>
          <p>Gagal memuat menu</p>
        </div>
      `;
    }
  }

  /**
   * Calculate and set portal header height as CSS variable
   * This allows the menu category to stick below the portal header
   */
  private updateHeaderHeight(): void {
    const header = this.container.querySelector('.portal-viewer__header') as HTMLElement;
    if (header) {
      const headerHeight = header.offsetHeight;
      this.container.style.setProperty('--portal-header-height', `${headerHeight}px`);
      console.log('[Portal] Header height set:', headerHeight);
    }
  }

  /**
   * Update active state on tab buttons
   */
  private updateActiveTabs(): void {
    const tabs = this.container.querySelectorAll('.portal-viewer__tab');

    tabs.forEach((tab, index) => {
      const isActive = index === this.currentMenuIndex;
      tab.classList.toggle('portal-viewer__tab--active', isActive);
      tab.setAttribute('aria-selected', String(isActive));
    });
  }

  /**
   * Render error state
   */
  private renderError(message: string): void {
    this.container.innerHTML = `
      <div class="portal-viewer portal-viewer--error">
        <div class="portal-viewer__error">
          <span class="portal-viewer__error-icon">⚠️</span>
          <h2>Oops!</h2>
          <p>${message}</p>
          <button
            type="button"
            class="portal-viewer__retry-btn"
            onclick="window.location.reload()"
          >
            Coba Lagi
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Destroy the viewer and clean up all resources
   * MUST be called when portal is unmounted to prevent memory leaks
   */
  destroy(): void {
    if (this.isDestroyed) return;
    this.isDestroyed = true;

    console.log('[Portal] Destroying and cleaning up resources');

    // 1. Destroy MenuViewer instance
    if (this.menuViewer) {
      this.menuViewer.destroy();
      this.menuViewer = null;
    }

    // 2. Remove resize listener
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler);
      this.resizeHandler = null;
    }

    // 3. Remove portal mode classes
    document.documentElement.classList.remove('portal-mode-active');
    document.body.classList.remove('portal-mode-active');

    // 4. Clear references
    this.portalData = null;
    this.menuContentContainer = null;
    this.container.innerHTML = '';
  }
}
