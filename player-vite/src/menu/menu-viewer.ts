/**
 * Menu Viewer Component
 * Public menu display for QR code scanning
 * Mobile-first responsive design
 */

import type { PublicMenu, PublicMenuItem, PublicMenuResponse, MenuViewerConfig } from './types';
import './menu-viewer.css';

// Preview data interface for carousel support
interface PreviewData {
  name: string;
  description: string;
  price: string;
  variant: string;
  media: Array<{
    url: string;
    type: 'image' | 'video';
  }>;
}

export class MenuViewer {
  private config: MenuViewerConfig;
  private container: HTMLElement | null = null;
  private menu: PublicMenu | null = null;
  private items: PublicMenuItem[] = [];
  private categories: string[] = [];
  private selectedCategory: string | null = null;
  private searchTerm: string = '';
  private isLoading = false;
  private error: string | null = null;
  private currentMediaIndex = 0;
  private currentPreviewData: PreviewData | null = null;
  private highlightedCarouselIntervals: Map<number, ReturnType<typeof setInterval>> = new Map();
  private expandedSubcategories: Set<string> = new Set();

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

    // Add class to html for CSS fallback (browsers that don't support :has())
    document.documentElement.classList.add('menu-mode-active');
    document.body.classList.add('menu-mode-active');

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
   * Group items by subcategory
   * Returns object with subcategory as key, items as value
   * Items without subcategory go to 'Lainnya' group
   */
  private groupItemsBySubcategory(items: PublicMenuItem[]): Map<string, PublicMenuItem[]> {
    const groups = new Map<string, PublicMenuItem[]>();
    const OTHER_GROUP = 'Lainnya';

    items.forEach(item => {
      const subcategory = item.subcategory || OTHER_GROUP;
      if (!groups.has(subcategory)) {
        groups.set(subcategory, []);
      }
      groups.get(subcategory)!.push(item);
    });

    // Sort groups: named subcategories first (sorted), then 'Lainnya' at the end
    const sortedGroups = new Map<string, PublicMenuItem[]>();
    const sortedKeys = Array.from(groups.keys())
      .filter(k => k !== OTHER_GROUP)
      .sort((a, b) => a.localeCompare(b, 'id'));

    sortedKeys.forEach(key => {
      sortedGroups.set(key, groups.get(key)!);
    });

    // Add 'Lainnya' at the end if it exists
    if (groups.has(OTHER_GROUP)) {
      sortedGroups.set(OTHER_GROUP, groups.get(OTHER_GROUP)!);
    }

    return sortedGroups;
  }

  /**
   * Toggle subcategory expand/collapse state
   */
  private toggleSubcategory(subcategory: string): void {
    if (this.expandedSubcategories.has(subcategory)) {
      this.expandedSubcategories.delete(subcategory);
    } else {
      this.expandedSubcategories.add(subcategory);
    }
    this.updateSubcategoryUI(subcategory);
  }

  /**
   * Update subcategory section UI (expand/collapse) without full re-render
   */
  private updateSubcategoryUI(subcategory: string): void {
    const section = document.querySelector(`[data-subcategory="${subcategory}"]`);
    if (!section) return;

    const header = section.querySelector('.menu-viewer__subcategory-header');
    const items = section.querySelector('.menu-viewer__subcategory-items');
    const chevron = header?.querySelector('.menu-viewer__subcategory-chevron');

    if (this.expandedSubcategories.has(subcategory)) {
      items?.classList.remove('menu-viewer__subcategory-items--collapsed');
      chevron?.classList.add('menu-viewer__subcategory-chevron--expanded');
    } else {
      items?.classList.add('menu-viewer__subcategory-items--collapsed');
      chevron?.classList.remove('menu-viewer__subcategory-chevron--expanded');
    }
  }

  /**
   * Check if we should show subcategory grouping (has at least one item with subcategory)
   */
  private hasSubcategoriesInCurrentView(): boolean {
    const categoryItems = this.selectedCategory
      ? this.items.filter(item => item.category === this.selectedCategory)
      : this.items;

    return categoryItems.some(item => item.subcategory);
  }

  /**
   * Get filtered items based on selected category and search term, sorted alphabetically
   */
  private getFilteredItems(): PublicMenuItem[] {
    let filtered = this.selectedCategory
      ? this.items.filter(item => item.category === this.selectedCategory)
      : [...this.items];

    // Filter by search term
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      filtered = filtered.filter(item =>
        item.name.toLowerCase().includes(term) ||
        (item.description && item.description.toLowerCase().includes(term)) ||
        (item.subcategory && item.subcategory.toLowerCase().includes(term))
      );
    }

    // Sort alphabetically by name
    return filtered.sort((a, b) => a.name.localeCompare(b.name, 'id'));
  }

  /**
   * Handle search input change - only update items, not entire page
   */
  private handleSearchInput(value: string): void {
    this.searchTerm = value;
    this.updateItemsOnly();
  }

  /**
   * Update only the items container without re-rendering entire page
   * This keeps the search input focused and responsive
   */
  private updateItemsOnly(): void {
    const itemsContainer = document.querySelector('.menu-viewer__minimalist-items');
    const emptyContainer = document.querySelector('.menu-viewer__empty');

    if (!itemsContainer) return;

    const filteredItems = this.getFilteredItems();

    // Update items HTML (grouped by subcategory if applicable, or flat list)
    // When searching, always show flat list for better search experience
    if (this.hasSubcategoriesInCurrentView() && !this.searchTerm) {
      itemsContainer.innerHTML = this.renderGroupedItems(filteredItems);
    } else {
      itemsContainer.innerHTML = filteredItems.map(item =>
        item.is_featured
          ? this.renderHighlightedItem(item)
          : this.renderNormalItem(item)
      ).join('');
    }

    // Handle empty state
    if (emptyContainer) {
      (emptyContainer as HTMLElement).style.display = filteredItems.length === 0 ? 'block' : 'none';
    } else if (filteredItems.length === 0) {
      // Create empty state if not exists
      const empty = document.createElement('div');
      empty.className = 'menu-viewer__empty';
      empty.innerHTML = '<p>No items found</p>';
      itemsContainer.parentElement?.insertBefore(empty, itemsContainer.nextSibling);
    }

    // Re-attach event listeners for items
    this.attachItemEventListeners();

    // Bind subcategory toggle events
    this.bindSubcategoryToggleEvents();
  }

  /**
   * Attach event listeners to menu items (for carousel, preview, etc)
   */
  private attachItemEventListeners(): void {
    // Highlighted item carousels
    document.querySelectorAll('.menu-viewer__highlighted-item').forEach((item) => {
      const itemId = parseInt(item.getAttribute('data-item-id') || '0');
      const mediaItems = item.querySelectorAll('.menu-viewer__media-item');
      const indicators = item.querySelectorAll('.menu-viewer__carousel-indicator');

      if (mediaItems.length > 1) {
        // Clear existing interval
        if (this.highlightedCarouselIntervals.has(itemId)) {
          clearInterval(this.highlightedCarouselIntervals.get(itemId));
        }

        let currentIndex = 0;
        const interval = setInterval(() => {
          currentIndex = (currentIndex + 1) % mediaItems.length;
          mediaItems.forEach((m, i) => {
            (m as HTMLElement).classList.toggle('active', i === currentIndex);
          });
          indicators.forEach((ind, i) => {
            (ind as HTMLElement).classList.toggle('active', i === currentIndex);
          });
        }, 4000);

        this.highlightedCarouselIntervals.set(itemId, interval);
      }
    });
  }

  /**
   * Bind subcategory toggle events for expand/collapse
   */
  private bindSubcategoryToggleEvents(): void {
    document.querySelectorAll('[data-toggle-subcategory]').forEach(header => {
      header.addEventListener('click', (e) => {
        const subcategory = (e.currentTarget as HTMLElement).dataset.toggleSubcategory;
        if (subcategory) {
          this.toggleSubcategory(subcategory);
        }
      });
    });
  }

  /**
   * Render variant badges (split by comma)
   * Variant = item variations like Hot, Cold, Large, Small (NOT subcategory)
   */
  private renderVariantBadges(variant: string | null): string {
    if (!variant) return '';

    const variants = variant.split(',').map(v => v.trim()).filter(v => v);
    if (variants.length === 0) return '';

    return `
      <div class="menu-viewer__variant-badges">
        ${variants.map(v => `
          <span class="menu-viewer__variant-badge">${v}</span>
        `).join('')}
      </div>
    `;
  }

  /**
   * Render inline tag badges (small badges after description)
   */
  private renderInlineTags(tags: string | null): string {
    if (!tags) return '';

    const tagList = tags.split(',').map(t => t.trim()).filter(t => t);
    if (tagList.length === 0) return '';

    return `<span class="menu-viewer__inline-tags">${tagList.map(tag =>
      `<span class="menu-viewer__inline-tag">${tag}</span>`
    ).join('')}</span>`;
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

    // Use minimalist rendering if display_mode is 'minimalist'
    if (this.menu.display_mode === 'minimalist') {
      this.renderMinimalist();
      return;
    }

    // Color scheme (60-30-10 principle)
    const primaryColor = this.menu.primary_color || '#ffffff';    // 60% - Background
    const secondaryColor = this.menu.secondary_color || '#f3f4f6'; // 30% - Header/Categories
    const themeColor = this.menu.theme_color || '#3b82f6';         // 10% - Accent
    const filteredItems = this.getFilteredItems();

    this.container.innerHTML = `
      <div class="menu-viewer" style="--primary-color: ${primaryColor}; --secondary-color: ${secondaryColor}; --theme-color: ${themeColor}">
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

  // =====================================================================
  // MINIMALIST MODE RENDERING
  // =====================================================================

  /**
   * Render items grouped by subcategory with expand/collapse sections
   */
  private renderGroupedItems(items: PublicMenuItem[]): string {
    const groups = this.groupItemsBySubcategory(items);

    return Array.from(groups.entries()).map(([subcategory, groupItems]) => {
      const isExpanded = this.expandedSubcategories.has(subcategory);
      const itemCount = groupItems.length;

      return `
        <div class="menu-viewer__subcategory-section" data-subcategory="${subcategory}">
          <button class="menu-viewer__subcategory-header" data-toggle-subcategory="${subcategory}">
            <span class="menu-viewer__subcategory-name">${subcategory}</span>
            <span class="menu-viewer__subcategory-count">${itemCount}</span>
            <svg class="menu-viewer__subcategory-chevron ${isExpanded ? 'menu-viewer__subcategory-chevron--expanded' : ''}" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
          <div class="menu-viewer__subcategory-items ${isExpanded ? '' : 'menu-viewer__subcategory-items--collapsed'}">
            ${groupItems.map(item =>
              item.is_featured
                ? this.renderHighlightedItem(item)
                : this.renderNormalItem(item)
            ).join('')}
          </div>
        </div>
      `;
    }).join('');
  }

  /**
   * Render the menu in minimalist mode
   */
  private renderMinimalist(): void {
    if (!this.container || !this.menu) return;

    // Color scheme (60-30-10 principle)
    const primaryColor = this.menu.primary_color || '#0f172a';    // 60% - Background (dark for minimalist)
    const secondaryColor = this.menu.secondary_color || '#1e293b'; // 30% - Header/Cards
    const themeColor = this.menu.theme_color || '#3b82f6';         // 10% - Accent
    const filteredItems = this.getFilteredItems();

    this.container.innerHTML = `
      <div class="menu-viewer menu-viewer--minimalist" style="--primary-color: ${primaryColor}; --secondary-color: ${secondaryColor}; --theme-color: ${themeColor}">
        <!-- Header -->
        <header class="menu-viewer__header">
          <div class="menu-viewer__header-text">
            <h1 class="menu-viewer__title">${this.menu.name}</h1>
            ${this.menu.description ? `<p class="menu-viewer__description">${this.menu.description}</p>` : ''}
            ${this.menu.outlet_extension ? `
              <div class="menu-viewer__header-extension">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                </svg>
                <span>Ext. ${this.menu.outlet_extension}</span>
              </div>
            ` : ''}
          </div>
        </header>

        <!-- Sticky Filter Bar (Categories + Search) -->
        <div class="menu-viewer__sticky-filter">
          <div class="menu-viewer__filter-row">
            <!-- Category Tabs -->
            ${this.categories.length > 0 ? `
              <div class="menu-viewer__minimalist-categories">
                <button
                  class="menu-viewer__minimalist-tab ${!this.selectedCategory ? 'menu-viewer__minimalist-tab--active' : ''}"
                  data-category=""
                >
                  All
                </button>
                ${this.categories.map(cat => `
                  <button
                    class="menu-viewer__minimalist-tab ${this.selectedCategory === cat ? 'menu-viewer__minimalist-tab--active' : ''}"
                    data-category="${cat}"
                  >
                    ${cat}
                  </button>
                `).join('')}
              </div>
            ` : ''}

            <!-- Search Toggle Button -->
            <button class="menu-viewer__search-toggle" id="search-toggle" title="Search">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </button>
          </div>

          <!-- Expandable Search Input -->
          <div class="menu-viewer__search-container ${this.searchTerm ? 'menu-viewer__search-container--expanded' : ''}" id="search-container">
            <svg class="menu-viewer__search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              type="text"
              class="menu-viewer__search-input"
              id="menu-search-input"
              placeholder="Search menu..."
              value="${this.searchTerm}"
            />
            <button class="menu-viewer__search-close" id="search-close">&times;</button>
          </div>
        </div>

        <!-- Minimalist Items (grouped by subcategory if available, or all items in order) -->
        <div class="menu-viewer__minimalist-items">
          ${this.hasSubcategoriesInCurrentView() && !this.searchTerm
            ? this.renderGroupedItems(filteredItems)
            : filteredItems.map(item =>
                item.is_featured
                  ? this.renderHighlightedItem(item)
                  : this.renderNormalItem(item)
              ).join('')
          }
        </div>

        ${filteredItems.length === 0 ? `
          <div class="menu-viewer__empty">
            <p>No items in this category</p>
          </div>
        ` : ''}

        <!-- Footer -->
        <footer class="menu-viewer__footer">
          ${this.menu.footer_description ? `<p class="menu-viewer__footer-desc">${this.menu.footer_description}</p>` : ''}
          <p class="menu-viewer__footer-powered">Powered by Digital Signage</p>
        </footer>
      </div>

      <!-- Contact FAB (Floating Action Button) -->
      ${(this.menu.whatsapp_number || this.menu.phone_number) ? `
        <div class="menu-viewer__fab-container" id="fab-container">
          <!-- FAB Options (hidden by default) -->
          <div class="menu-viewer__fab-options" id="fab-options">
            ${this.menu.whatsapp_number ? `
              <button class="menu-viewer__fab-option menu-viewer__fab-option--whatsapp" data-action="whatsapp" title="WhatsApp">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
              </button>
            ` : ''}
            ${this.menu.phone_number ? `
              <button class="menu-viewer__fab-option menu-viewer__fab-option--phone" data-action="phone" title="Call">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                </svg>
              </button>
            ` : ''}
          </div>
          <!-- Main FAB Button -->
          <button class="menu-viewer__fab-main" id="fab-main" title="${this.menu.contact_label || 'Contact'}">
            <svg class="menu-viewer__fab-icon menu-viewer__fab-icon--contact" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            <svg class="menu-viewer__fab-icon menu-viewer__fab-icon--close" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      ` : ''}

      <!-- Preview Popup (hidden by default) -->
      <div class="menu-viewer__preview-popup" id="preview-popup">
        <button class="menu-viewer__preview-close" id="preview-close">&times;</button>
        <div id="preview-content"></div>
      </div>
    `;

    // Bind events
    this.bindMinimalistEvents();
  }

  /**
   * Render a highlighted/featured item with carousel support
   * @param item - The menu item to render
   */
  private renderHighlightedItem(item: PublicMenuItem): string {
    const mediaArray = this.getItemMediaArray(item);
    const hasMedia = mediaArray.length > 0;
    const hasMultipleMedia = mediaArray.length > 1;

    // Build carousel slides HTML
    const slidesHtml = hasMedia ? mediaArray.map((media, index) => `
      <div class="menu-viewer__highlighted-slide ${index === 0 ? 'menu-viewer__highlighted-slide--active' : ''}" data-index="${index}">
        ${media.type === 'video' ? `
          <video src="${media.url}" muted loop playsinline></video>
        ` : `
          <img src="${media.url}" alt="${item.name}" loading="lazy" />
        `}
      </div>
    `).join('') : '';

    // Dots indicator for multiple media
    const dotsHtml = hasMultipleMedia ? `
      <div class="menu-viewer__highlighted-dots">
        ${mediaArray.map((_, i) => `
          <span class="menu-viewer__highlighted-dot ${i === 0 ? 'menu-viewer__highlighted-dot--active' : ''}" data-index="${i}"></span>
        `).join('')}
      </div>
    ` : '';

    return `
      <div class="menu-viewer__highlighted-item ${!item.is_available ? 'menu-viewer__item--unavailable' : ''}" data-item-id="${item.id}">
        ${hasMedia ? `
          <div class="menu-viewer__highlighted-media" data-item-id="${item.id}" data-slide-count="${mediaArray.length}">
            <div class="menu-viewer__highlighted-slides">
              ${slidesHtml}
            </div>
            ${dotsHtml}
          </div>
        ` : ''}
        <div class="menu-viewer__highlighted-content">
          <div class="menu-viewer__highlighted-header">
            <h3 class="menu-viewer__highlighted-name">
              <span class="menu-viewer__highlighted-star">&#9733;</span>
              ${item.name}
            </h3>
            ${this.menu?.show_prices && item.price !== null ? `
              <span class="menu-viewer__highlighted-price">${this.formatPrice(item.price, item.currency)}</span>
            ` : ''}
          </div>
          ${(item.description || item.tags) ? `
            <p class="menu-viewer__highlighted-description">
              ${item.description || ''}${this.renderInlineTags(item.tags)}
            </p>
          ` : ''}
          ${this.renderVariantBadges(item.variant)}
          ${!item.is_available ? `
            <span class="menu-viewer__unavailable-badge">Not Available</span>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Build media array from item (combine media array with legacy image_url/video_url)
   */
  private getItemMediaArray(item: PublicMenuItem): Array<{ url: string; type: 'image' | 'video' }> {
    const mediaList: Array<{ url: string; type: 'image' | 'video' }> = [];

    // Add media from new media array first (if available)
    if (item.media && item.media.length > 0) {
      item.media.forEach(m => {
        mediaList.push({
          url: m.url,
          type: m.type,
        });
      });
    } else {
      // Fallback to legacy image_url/video_url
      if (item.video_url) {
        mediaList.push({ url: item.video_url, type: 'video' });
      }
      if (item.image_url) {
        mediaList.push({ url: item.image_url, type: 'image' });
      }
    }

    return mediaList;
  }

  /**
   * Render a normal item (minimalist text-only, click name for preview)
   * @param item - The menu item to render
   */
  private renderNormalItem(item: PublicMenuItem): string {
    const mediaArray = this.getItemMediaArray(item);
    const hasMedia = mediaArray.length > 0;
    const hasMultipleMedia = mediaArray.length > 1;

    // Name classes - clickable if has media
    const nameClasses = [
      'menu-viewer__normal-item-name',
      hasMedia ? 'menu-viewer__normal-item-name--clickable' : '',
      hasMedia ? 'menu-viewer__normal-item-name--has-media' : '',
      hasMultipleMedia ? 'menu-viewer__normal-item-name--has-carousel' : ''
    ].filter(Boolean).join(' ');

    // Encode media array as JSON for data attribute (don't escape - use single quotes for attr)
    const mediaJson = hasMedia ? JSON.stringify(mediaArray) : '';

    return `
      <div class="menu-viewer__normal-item ${!item.is_available ? 'menu-viewer__item--unavailable' : ''}">
        <div class="menu-viewer__item-info">
          <div class="menu-viewer__item-name-row">
            <h3
              class="${nameClasses}"
              ${hasMedia ? `
                data-preview-id="${item.id}"
                data-preview-name="${this.escapeHtml(item.name)}"
                data-preview-desc="${this.escapeHtml(item.description || '')}"
                data-preview-price="${this.menu?.show_prices && item.price !== null ? this.formatPrice(item.price, item.currency) : ''}"
                data-preview-media='${mediaJson}'
                data-preview-variant="${this.escapeHtml(item.variant || '')}"
              ` : ''}
            >${item.name}${hasMultipleMedia ? `<span class="menu-viewer__media-count">${mediaArray.length}</span>` : ''}</h3>
          </div>
          ${(item.description || item.tags) ? `
            <p class="menu-viewer__normal-item-desc">${item.description || ''}${this.renderInlineTags(item.tags)}</p>
          ` : ''}
          ${this.renderVariantBadges(item.variant)}
          ${!item.is_available ? `
            <span class="menu-viewer__unavailable-badge">Not Available</span>
          ` : ''}
        </div>
        <div class="menu-viewer__item-right">
          ${this.menu?.show_prices && item.price !== null ? `
            <span class="menu-viewer__normal-item-price">${this.formatPrice(item.price, item.currency)}</span>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Escape HTML special characters
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Show preview popup with carousel support
   */
  private showPreviewPopup(data: PreviewData): void {
    const popup = document.getElementById('preview-popup');
    const content = document.getElementById('preview-content');
    if (!popup || !content) return;

    // Store current preview data and reset index
    this.currentPreviewData = data;
    this.currentMediaIndex = 0;

    // Render the popup content
    this.renderPreviewContent();

    popup.classList.add('menu-viewer__preview-popup--visible');
    document.body.style.overflow = 'hidden';
  }

  /**
   * Render preview content (called on init and navigation)
   */
  private renderPreviewContent(): void {
    const content = document.getElementById('preview-content');
    if (!content || !this.currentPreviewData) return;

    const data = this.currentPreviewData;
    const hasMultipleMedia = data.media.length > 1;
    const currentMedia = data.media[this.currentMediaIndex];

    // Build media HTML
    const mediaHtml = currentMedia.type === 'video'
      ? `<video class="menu-viewer__preview-media" src="${currentMedia.url}" controls autoplay></video>`
      : `<img class="menu-viewer__preview-media" src="${currentMedia.url}" alt="${data.name}" />`;

    // Build navigation arrows (only if multiple media)
    const navHtml = hasMultipleMedia ? `
      <button class="menu-viewer__carousel-nav menu-viewer__carousel-nav--prev" id="carousel-prev">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>
      <button class="menu-viewer__carousel-nav menu-viewer__carousel-nav--next" id="carousel-next">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </button>
    ` : '';

    // Build dots indicator (only if multiple media)
    const dotsHtml = hasMultipleMedia ? `
      <div class="menu-viewer__carousel-dots">
        ${data.media.map((_, i) => `
          <span class="menu-viewer__carousel-dot ${i === this.currentMediaIndex ? 'menu-viewer__carousel-dot--active' : ''}" data-index="${i}"></span>
        `).join('')}
      </div>
    ` : '';

    // Counter indicator
    const counterHtml = hasMultipleMedia
      ? `<span class="menu-viewer__carousel-counter">${this.currentMediaIndex + 1} / ${data.media.length}</span>`
      : '';

    content.innerHTML = `
      <div class="menu-viewer__preview-media-container">
        ${mediaHtml}
        ${navHtml}
        ${counterHtml}
      </div>
      ${dotsHtml}
      <div class="menu-viewer__preview-info">
        <h3 class="menu-viewer__preview-name">${data.name}</h3>
        ${data.variant ? `<span class="menu-viewer__preview-variant">${data.variant}</span>` : ''}
        ${data.price ? `<p class="menu-viewer__preview-price">${data.price}</p>` : ''}
        ${data.description ? `<p class="menu-viewer__preview-desc">${data.description}</p>` : ''}
      </div>
    `;

    // Bind carousel events
    this.bindCarouselEvents();
  }

  /**
   * Bind carousel navigation events
   */
  private bindCarouselEvents(): void {
    if (!this.currentPreviewData || this.currentPreviewData.media.length <= 1) return;

    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');

    if (prevBtn) {
      prevBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.navigateCarousel('prev');
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.navigateCarousel('next');
      });
    }

    // Dot clicks
    document.querySelectorAll('.menu-viewer__carousel-dot').forEach(dot => {
      dot.addEventListener('click', (e) => {
        e.stopPropagation();
        const index = parseInt((e.currentTarget as HTMLElement).dataset.index || '0', 10);
        this.navigateCarousel(index);
      });
    });

    // Swipe support for touch devices
    const container = document.querySelector('.menu-viewer__preview-media-container');
    if (container) {
      let startX = 0;
      let endX = 0;

      container.addEventListener('touchstart', (e: Event) => {
        startX = (e as TouchEvent).touches[0].clientX;
      }, { passive: true });

      container.addEventListener('touchend', (e: Event) => {
        endX = (e as TouchEvent).changedTouches[0].clientX;
        const diff = startX - endX;
        if (Math.abs(diff) > 50) {
          this.navigateCarousel(diff > 0 ? 'next' : 'prev');
        }
      }, { passive: true });
    }
  }

  /**
   * Navigate carousel
   */
  private navigateCarousel(direction: 'prev' | 'next' | number): void {
    if (!this.currentPreviewData) return;

    const mediaCount = this.currentPreviewData.media.length;

    if (typeof direction === 'number') {
      this.currentMediaIndex = direction;
    } else if (direction === 'prev') {
      this.currentMediaIndex = (this.currentMediaIndex - 1 + mediaCount) % mediaCount;
    } else {
      this.currentMediaIndex = (this.currentMediaIndex + 1) % mediaCount;
    }

    this.renderPreviewContent();
  }

  /**
   * Hide preview popup
   */
  private hidePreviewPopup(): void {
    const popup = document.getElementById('preview-popup');
    if (!popup) return;

    popup.classList.remove('menu-viewer__preview-popup--visible');
    document.body.style.overflow = '';

    // Stop video if playing
    const video = popup.querySelector('video');
    if (video) {
      video.pause();
    }
  }

  /**
   * Bind event listeners for minimalist mode
   */
  private bindMinimalistEvents(): void {
    if (!this.container) return;

    // Category tabs
    this.container.querySelectorAll('.menu-viewer__minimalist-tab').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const category = (e.currentTarget as HTMLElement).dataset.category || null;
        this.handleCategoryClick(category || null);
      });
    });

    // Search toggle button - expand search
    const searchToggle = document.getElementById('search-toggle');
    const searchContainer = document.getElementById('search-container');
    const searchInput = document.getElementById('menu-search-input') as HTMLInputElement;
    const searchClose = document.getElementById('search-close');

    if (searchToggle && searchContainer) {
      searchToggle.addEventListener('click', () => {
        searchContainer.classList.add('menu-viewer__search-container--expanded');
        searchInput?.focus();
      });
    }

    // Search close button - collapse search
    if (searchClose && searchContainer) {
      searchClose.addEventListener('click', () => {
        // Clear search and collapse
        this.searchTerm = '';
        if (searchInput) searchInput.value = '';
        this.updateItemsOnly();
        searchContainer.classList.remove('menu-viewer__search-container--expanded');
      });
    }

    // Search input - use 'input' event for real-time updates
    if (searchInput) {
      // Handle input event (typing, pasting, etc)
      searchInput.addEventListener('input', (e) => {
        const value = (e.target as HTMLInputElement).value;
        this.handleSearchInput(value);
      });

      // Also handle keyup for backspace/delete reliability
      searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Backspace' || e.key === 'Delete') {
          const value = (e.target as HTMLInputElement).value;
          if (value !== this.searchTerm) {
            this.handleSearchInput(value);
          }
        }
      });

      // Close search on Escape
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && searchContainer) {
          this.searchTerm = '';
          searchInput.value = '';
          this.updateItemsOnly();
          searchContainer.classList.remove('menu-viewer__search-container--expanded');
        }
      });
    }

    // FAB Toggle (show/hide contact options)
    const fabMain = document.getElementById('fab-main');
    const fabContainer = document.getElementById('fab-container');
    if (fabMain && fabContainer) {
      fabMain.addEventListener('click', (e) => {
        e.stopPropagation();
        fabContainer.classList.toggle('menu-viewer__fab-container--open');
      });

      // Close FAB when clicking outside
      document.addEventListener('click', (e) => {
        if (!fabContainer.contains(e.target as Node)) {
          fabContainer.classList.remove('menu-viewer__fab-container--open');
        }
      });
    }

    // WhatsApp button (FAB option)
    const whatsappBtn = this.container.querySelector('[data-action="whatsapp"]');
    if (whatsappBtn) {
      whatsappBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleWhatsAppClick();
        // Close FAB after action
        document.getElementById('fab-container')?.classList.remove('menu-viewer__fab-container--open');
      });
    }

    // Phone button (FAB option)
    const phoneBtn = this.container.querySelector('[data-action="phone"]');
    if (phoneBtn) {
      phoneBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handlePhoneClick();
        // Close FAB after action
        document.getElementById('fab-container')?.classList.remove('menu-viewer__fab-container--open');
      });
    }

    // Clickable menu names (click to preview with carousel)
    this.container.querySelectorAll('.menu-viewer__normal-item-name--clickable').forEach(nameEl => {
      nameEl.addEventListener('click', (e) => {
        const element = e.currentTarget as HTMLElement;

        // Parse media array from JSON data attribute
        let media: Array<{ url: string; type: 'image' | 'video' }> = [];
        try {
          const mediaData = element.dataset.previewMedia;
          if (mediaData) {
            media = JSON.parse(mediaData);
          }
        } catch {
          // Fallback for legacy single media format
          console.warn('Failed to parse media array, using fallback');
        }

        if (media.length === 0) return;

        this.showPreviewPopup({
          name: element.dataset.previewName || '',
          description: element.dataset.previewDesc || '',
          price: element.dataset.previewPrice || '',
          variant: element.dataset.previewVariant || '',
          media: media,
        });
      });
    });

    // Preview close button
    const closeBtn = document.getElementById('preview-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hidePreviewPopup());
    }

    // Close popup on background click
    const popup = document.getElementById('preview-popup');
    if (popup) {
      popup.addEventListener('click', (e) => {
        if (e.target === popup) {
          this.hidePreviewPopup();
        }
      });
    }

    // Close popup on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.hidePreviewPopup();
      }
    });

    // Video autoplay on hover for highlighted items
    this.container.querySelectorAll('.menu-viewer__highlighted-media video').forEach(video => {
      const videoEl = video as HTMLVideoElement;
      videoEl.parentElement?.addEventListener('mouseenter', () => videoEl.play());
      videoEl.parentElement?.addEventListener('mouseleave', () => {
        videoEl.pause();
        videoEl.currentTime = 0;
      });
    });

    // Initialize highlighted item carousels (auto-slide + swipe)
    this.initHighlightedCarousels();

    // Bind subcategory toggle events for expand/collapse
    this.bindSubcategoryToggleEvents();
  }

  /**
   * Initialize carousels for highlighted items
   */
  private initHighlightedCarousels(): void {
    if (!this.container) return;

    // Clear any existing intervals
    this.highlightedCarouselIntervals.forEach(interval => clearInterval(interval));
    this.highlightedCarouselIntervals.clear();

    // Find all highlighted media containers with multiple slides
    this.container.querySelectorAll('.menu-viewer__highlighted-media').forEach(mediaContainer => {
      const container = mediaContainer as HTMLElement;
      const slideCount = parseInt(container.dataset.slideCount || '0', 10);
      const itemId = parseInt(container.dataset.itemId || '0', 10);

      if (slideCount <= 1) return; // Skip single image items

      let currentIndex = 0;

      // Function to change slide
      const changeSlide = (newIndex: number) => {
        const slides = container.querySelectorAll('.menu-viewer__highlighted-slide');
        const dots = container.querySelectorAll('.menu-viewer__highlighted-dot');

        // Wrap around
        if (newIndex >= slideCount) newIndex = 0;
        if (newIndex < 0) newIndex = slideCount - 1;

        currentIndex = newIndex;

        // Update slides
        slides.forEach((slide, i) => {
          slide.classList.toggle('menu-viewer__highlighted-slide--active', i === currentIndex);
        });

        // Update dots
        dots.forEach((dot, i) => {
          dot.classList.toggle('menu-viewer__highlighted-dot--active', i === currentIndex);
        });
      };

      // Auto-slide every 4 seconds
      const interval = setInterval(() => {
        changeSlide(currentIndex + 1);
      }, 4000);
      this.highlightedCarouselIntervals.set(itemId, interval);

      // Touch/swipe support
      let touchStartX = 0;
      let touchEndX = 0;

      container.addEventListener('touchstart', (e: TouchEvent) => {
        touchStartX = e.touches[0].clientX;
      }, { passive: true });

      container.addEventListener('touchend', (e: TouchEvent) => {
        touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > 50) {
          // Reset auto-slide timer when user swipes
          clearInterval(this.highlightedCarouselIntervals.get(itemId)!);

          if (diff > 0) {
            changeSlide(currentIndex + 1); // Swipe left = next
          } else {
            changeSlide(currentIndex - 1); // Swipe right = prev
          }

          // Restart auto-slide
          const newInterval = setInterval(() => {
            changeSlide(currentIndex + 1);
          }, 4000);
          this.highlightedCarouselIntervals.set(itemId, newInterval);
        }
      }, { passive: true });

      // Dot click navigation
      container.querySelectorAll('.menu-viewer__highlighted-dot').forEach(dot => {
        dot.addEventListener('click', (e) => {
          const index = parseInt((e.currentTarget as HTMLElement).dataset.index || '0', 10);
          changeSlide(index);

          // Reset auto-slide timer when user clicks dot
          clearInterval(this.highlightedCarouselIntervals.get(itemId)!);
          const newInterval = setInterval(() => {
            changeSlide(currentIndex + 1);
          }, 4000);
          this.highlightedCarouselIntervals.set(itemId, newInterval);
        });
      });
    });
  }
}
