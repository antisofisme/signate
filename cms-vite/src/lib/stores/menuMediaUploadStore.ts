/**
 * Menu Media Upload Queue Store - Zustand
 * Simple upload queue for menu media images
 */

import { create } from 'zustand';

export interface MenuMediaQueueItem {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

interface MenuMediaUploadStore {
  items: MenuMediaQueueItem[];
  isMinimized: boolean;
  isProcessing: boolean;
  panelHeight: number;

  // Actions
  addToQueue: (files: File[]) => void;
  removeFromQueue: (id: string) => void;
  updateStatus: (id: string, status: MenuMediaQueueItem['status'], error?: string) => void;
  updateProgress: (id: string, progress: number) => void;
  clearQueue: () => void;
  clearCompleted: () => void;
  setProcessing: (isProcessing: boolean) => void;
  toggleMinimize: () => void;
  setPanelHeight: (height: number) => void;

  // Computed
  getPendingItems: () => MenuMediaQueueItem[];
  getSummary: () => {
    total: number;
    pending: number;
    uploading: number;
    success: number;
    error: number;
  };
}

const generateId = () => Math.random().toString(36).substring(2, 9);

export const useMenuMediaUploadStore = create<MenuMediaUploadStore>((set, get) => ({
  items: [],
  isMinimized: false,
  isProcessing: false,
  panelHeight: 0,

  addToQueue: (files) => {
    const newItems: MenuMediaQueueItem[] = files.map((file) => ({
      id: generateId(),
      file,
      status: 'pending',
      progress: 0,
    }));
    set((state) => ({
      items: [...state.items, ...newItems],
      isMinimized: false, // Expand when adding
    }));
  },

  removeFromQueue: (id) => {
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    }));
  },

  updateStatus: (id, status, error) => {
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, status, error, progress: status === 'success' ? 100 : item.progress } : item
      ),
    }));
  },

  updateProgress: (id, progress) => {
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, progress } : item
      ),
    }));
  },

  clearQueue: () => {
    set({ items: [], isProcessing: false });
  },

  clearCompleted: () => {
    set((state) => ({
      items: state.items.filter((item) => item.status !== 'success'),
    }));
  },

  setProcessing: (isProcessing) => {
    set({ isProcessing });
  },

  toggleMinimize: () => {
    set((state) => ({ isMinimized: !state.isMinimized }));
  },

  setPanelHeight: (height) => {
    set({ panelHeight: height });
  },

  getPendingItems: () => {
    return get().items.filter((item) => item.status === 'pending');
  },

  getSummary: () => {
    const items = get().items;
    return {
      total: items.length,
      pending: items.filter((i) => i.status === 'pending').length,
      uploading: items.filter((i) => i.status === 'uploading').length,
      success: items.filter((i) => i.status === 'success').length,
      error: items.filter((i) => i.status === 'error').length,
    };
  },
}));
