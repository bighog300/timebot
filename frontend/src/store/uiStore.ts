import { create } from 'zustand';

type Toast = { id: number; message: string; type?: 'success' | 'error' };

interface UIState {
  toasts: Toast[];
  pushToast: (message: string, type?: 'success' | 'error') => void;
  dismissToast: (id: number) => void;
}

export const useUIStore = create<UIState>((set) => ({
  toasts: [],
  pushToast: (message, type = 'success') =>
    set((state) => ({
      toasts: [...state.toasts, { id: Date.now(), message, type }],
    })),
  dismissToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
