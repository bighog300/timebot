import { create } from 'zustand';

type Toast = { id: number; message: string };

interface UIState {
  toasts: Toast[];
  pushToast: (message: string) => void;
  dismissToast: (id: number) => void;
}

export const useUIStore = create<UIState>((set) => ({
  toasts: [],
  pushToast: (message) =>
    set((state) => ({
      toasts: [...state.toasts, { id: Date.now(), message }],
    })),
  dismissToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
