/**
 * Menu Viewer Component
 * Public menu display for QR code scanning
 * Mobile-first responsive design
 */

import type { PublicMenu, PublicMenuItem, PublicMenuResponse, MenuViewerConfig } from './types';
import './menu-viewer.css';

export class MenuViewer {
  private config: MenuViewerConfig;
  private container: HTMLElement | null = null;
  private menu: PublicMenu | null = null;
  private items: PublicMenuItem[] = [];
  private categories: string[] = [];
  private selectedCategory: string | null = null;
  private isLoading = false;
  private error: string | null = null;

  constructor(config: MenuViewerConfig) {
    this.config = config;
  }

  /**
   * Initialize and render the menu viewer
   */
  async init(containerId: string): Promise<void> {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error('[MenuViewer] Container not found:', containerId);
      return;
    }

    // Show loading state
    this.isLoading = true;
    this.render();

    // Fetch menu data
    try {
      await this.fetchMenu();
      this.extractCategories();
      this.isLoading = false;
      this.render();
    } catch (err) {
      this.isLoading = false;
      this.error = err instanceof Error ? err.message : 'Failed to load menu';
      this.render();
    }
  }

  /**
   * Fetch menu data from public API
   */
  private async fetchMenu(): Promise<void> {
    const url = `${this.config.apiBaseUrl}/api/v1/public/menu/${this.config.publicCode}?limit=100`;

    const response = await fetch(url);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Menu not found');
      }
      throw new Error(`Failed to load menu (${response.status})`);
    }

    const json = await response.json();

    // Handle wrapped response
    const data: PublicMenuResponse = json.data || json;

    this.menu = data.menu;
    this.items = data.items;
  }

  /**
   * Extract unique categories from items
   */
  private extractCategories(): void {
    const categorySet = new Set<string>();
    this.items.forEach(item => {
      if (item.category) {
        categorySet.add(item.category);
      }
    });
    this.categories = Array.from(categorySet).sort();
  }

  /**
   * Get filtered items based on selected category
   */
  private getFilteredItems(): PublicMenuItem[] {
    if (!this.selectedCategory) {
      return this.items;
    }
    return this.items.filter(item => item.category === this.selectedCategory);
  }

  /**
   * Format price with currency
   */
  private formatPrice(price: number | null, currency: string): string {
    if (price === null) return '';

    try {
      return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: currency || 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(price);
    } catch {
      return `${currency} ${price.toLocaleString()}`;
    }
  }

  /**
   * Handle WhatsApp button click
   */
  private handleWhatsAppClick(): void {
    if (!this.menu?.whatsapp_number) return;

    // Track click
    this.trackContactClick('whatsapp');

    // Open WhatsApp
    const number = this.menu.whatsapp_number.replace(/[^0-9]/g, '');
    const message = encodeURIComponent(`Hi, I'm interested in your menu: ${this.menu.name}`);
    window.open(`https://wa.me/${number}?text=${message}`, '_blank');
  }

  /**
   * Handle Phone button click
   */
  private handlePhoneClick(): void {
    if (!this.menu?.phone_number) return;

    // Track click
    this.trackContactClick('phone');

    // Open phone dialer
    window.location.href = `tel:${this.menu.phone_number}`;
  }

  /**
   * Track contact button click
   */
  private async trackContactClick(contactType: 'whatsapp' | 'phone'): Promise<void> {
    try {
      await fetch(
        `${this.config.apiBaseUrl}/api/v1/public/menu/${this.config.publicCode}/track-contact?contact_type=${contactType}`,
        { method: 'POST' }
      );
    } catch {
      // Ignore tracking errors
    }
  }

  /**
   * Handle category filter click
   */
  private handleCategoryClick(category: string | null): void {
    this.selectedCategory = category;
    this.render();
  }

  /**
   * Get menu type icon
   */
  private getMenuTypeIcon(): string {
    const icons: Record<string, string> = {
      restaurant: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>',
      laundry: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="20" x="2" y="2" rx="2"/><circle cx="12" cy="12" r="5"/><path d="M12 7v1"/></svg>',
      spa: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22c4.97 0 9-2.69 9-6s-4.03-6-9-6-9 2.69-9 6 4.03 6 9 6z"/><path d="M12 10c0-4.97 2.69-9 6-9s6 4.03 6 9"/><path d="M12 10c0-4.97-2.69-9-6-9s-6 4.03-6 9"/></svg>',
      room_service: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 18h20v2H2zM4 18c0-4 4-8 8-8s8 4 8 8"/><path d="M12 6v2"/><circle cx="12" cy="4" r="2"/></svg>',
      other: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 9h6v6H9z"/></svg>',
    };
    return icons[this.menu?.menu_type || 'other'] || icons.other;
  }

  /**
   * Render the menu viewer
   */
  private render(): void {
    if (!this.container) return;

    // Loading state
    if (this.isLoading) {
      this.container.innerHTML = `
        <div class="menu-viewer menu-viewer--loading">
          <div class="menu-viewer__spinner"></div>
          <p>Loading menu...</p>
        </div>
      `;
      return;
    }

    // Error state
    if (this.error) {
      this.container.innerHTML = `
        <div class="menu-viewer menu-viewer--error">
          <div class="menu-viewer__error-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" x2="12" y1="8" y2="12"/>
              <line x1="12" x2="12.01" y1="16" y2="16"/>
            </svg>
          </div>
          <h2>Menu Not Found</h2>
          <p>${this.error}</p>
        </div>
      `;
      return;
    }

    if (!this.menu) return;

    const themeColor = this.menu.theme_color || '#3b82f6';
    const filteredItems = this.getFilteredItems();

    this.container.innerHTML = `
      <div class="menu-viewer" style="--theme-color: ${themeColor}">
        <!-- Header -->
        <header class="menu-viewer__header">
          <div class="menu-viewer__header-icon">
            ${this.getMenuTypeIcon()}
          </div>
          <div class="menu-viewer__header-text">
            <h1 class="menu-viewer__title">${this.menu.name}</h1>
            ${this.menu.description ? `<p class="menu-viewer__description">${this.menu.description}</p>` : ''}
          </div>
        </header>

        <!-- Category Filter -->
        ${this.categories.length > 0 ? `
          <div class="menu-viewer__categories">
            <button
              class="menu-viewer__category-btn ${!this.selectedCategory ? 'menu-viewer__category-btn--active' : ''}"
              data-category=""
            >
              All
            </button>
            ${this.categories.map(cat => `
              <button
                class="menu-viewer__category-btn ${this.selectedCategory === cat ? 'menu-viewer__category-btn--active' : ''}"
                data-category="${cat}"
              >
                ${cat}
              </button>
            `).join('')}
          </div>
        ` : ''}

        <!-- Menu Items -->
        <div class="menu-viewer__items menu-viewer__items--${this.menu.display_mode}">
          ${filteredItems.map(item => this.renderItem(item)).join('')}
        </div>

        ${filteredItems.length === 0 ? `
          <div class="menu-viewer__empty">
            <p>No items in this category</p>
          </div>
        ` : ''}

        <!-- Contact Buttons -->
        ${(this.menu.whatsapp_number || this.menu.phone_number) ? `
          <div class="menu-viewer__contact">
            ${this.menu.contact_label ? `<p class="menu-viewer__contact-label">${this.menu.contact_label}</p>` : ''}
            <div class="menu-viewer__contact-buttons">
              ${this.menu.whatsapp_number ? `
                <button class="menu-viewer__contact-btn menu-viewer__contact-btn--whatsapp" data-action="whatsapp">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                  </svg>
                  WhatsApp
                </button>
              ` : ''}
              ${this.menu.phone_number ? `
                <button class="menu-viewer__contact-btn menu-viewer__contact-btn--phone" data-action="phone">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                  </svg>
                  Call
                </button>
              ` : ''}
            </div>
          </div>
        ` : ''}

        <!-- Footer -->
        <footer class="menu-viewer__footer">
          <p>Powered by Digital Signage</p>
        </footer>
      </div>
    `;

    // Bind event listeners
    this.bindEvents();
  }

  /**
   * Render a single menu item
   */
  private renderItem(item: PublicMenuItem): string {
    const hasMedia = item.image_url || item.video_url;

    return `
      <div class="menu-viewer__item ${item.is_featured ? 'menu-viewer__item--featured' : ''} ${!item.is_available ? 'menu-viewer__item--unavailable' : ''}">
        ${hasMedia ? `
          <div class="menu-viewer__item-media">
            ${item.video_url ? `
              <video src="${item.video_url}" muted loop playsinline></video>
            ` : `
              <img src="${item.image_url}" alt="${item.name}" loading="lazy" />
            `}
          </div>
        ` : ''}
        <div class="menu-viewer__item-content">
          <div class="menu-viewer__item-header">
            <h3 class="menu-viewer__item-name">
              ${item.is_featured ? '<span class="menu-viewer__item-star">&#9733;</span>' : ''}
              ${item.name}
            </h3>
            ${this.menu?.show_prices && item.price !== null ? `
              <span class="menu-viewer__item-price">${this.formatPrice(item.price, item.currency)}</span>
            ` : ''}
          </div>
          ${item.description ? `
            <p class="menu-viewer__item-description">${item.description}</p>
          ` : ''}
          ${!item.is_available ? `
            <span class="menu-viewer__item-unavailable-badge">Not Available</span>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Bind event listeners
   */
  private bindEvents(): void {
    if (!this.container) return;

    // Category buttons
    this.container.querySelectorAll('.menu-viewer__category-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const category = (e.currentTarget as HTMLElement).dataset.category || null;
        this.handleCategoryClick(category || null);
      });
    });

    // WhatsApp button
    const whatsappBtn = this.container.querySelector('[data-action="whatsapp"]');
    if (whatsappBtn) {
      whatsappBtn.addEventListener('click', () => this.handleWhatsAppClick());
    }

    // Phone button
    const phoneBtn = this.container.querySelector('[data-action="phone"]');
    if (phoneBtn) {
      phoneBtn.addEventListener('click', () => this.handlePhoneClick());
    }

    // Video autoplay on hover (for grid mode)
    this.container.querySelectorAll('.menu-viewer__item-media video').forEach(video => {
      const videoEl = video as HTMLVideoElement;
      videoEl.parentElement?.addEventListener('mouseenter', () => videoEl.play());
      videoEl.parentElement?.addEventListener('mouseleave', () => {
        videoEl.pause();
        videoEl.currentTime = 0;
      });
    });
  }
}
