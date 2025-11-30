/**
 * Portal Viewer
 * Unified menu portal with tab navigation for all organization menus
 */

import './portal-viewer.css';
import { PortalResponse, PortalMenu, MENU_TYPE_ICONS, PortalViewerConfig } from './types';
import { MenuViewer } from '../menu/menu-viewer';

export class PortalViewer {
  private container: HTMLElement;
  private config: PortalViewerConfig;
  private portalData: PortalResponse | null = null;
  private currentMenuIndex: number = 0;
  private menuViewer: MenuViewer | null = null;
  private menuContentContainer: HTMLElement | null = null;

  constructor(container: HTMLElement, config: PortalViewerConfig) {
    this.container = container;
    this.config = config;
  }

  /**
   * Load portal data and render
   */
  async load(): Promise<void> {
    console.log('[Portal] Loading portal:', this.config.portalSlug);

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

    // Build portal HTML
    this.container.innerHTML = `
      <div class="portal-viewer">
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

    // Attach tab click handlers
    this.attachTabHandlers();

    // Load first menu
    this.loadMenu(0);
  }

  /**
   * Render tab buttons for each menu
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
        <span class="portal-viewer__tab-icon">${this.getMenuIcon(menu.menu_type)}</span>
        <span class="portal-viewer__tab-label">${menu.name}</span>
      </button>
    `).join('');
  }

  /**
   * Get icon for menu type
   */
  private getMenuIcon(menuType: string): string {
    return MENU_TYPE_ICONS[menuType] || MENU_TYPE_ICONS.other;
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

    // Initialize menu viewer with the menu's public code
    // MenuViewer expects config in constructor, then init(containerId)
    this.menuViewer = new MenuViewer({
      apiBaseUrl: this.config.apiBaseUrl,
      publicCode: menu.public_url_code
    });

    // Load the menu into the container
    await this.menuViewer.init(menuContainerId);
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
   * Destroy the viewer and clean up
   */
  destroy(): void {
    this.portalData = null;
    this.menuViewer = null;
    this.menuContentContainer = null;
    this.container.innerHTML = '';
  }
}
