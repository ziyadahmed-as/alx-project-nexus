import { create } from 'zustand';

interface CartItem {
  id: number;
  product: any;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  addItem: (product: any, quantity: number) => void;
  removeItem: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],

  addItem: (product, quantity) => {
    const items = get().items;
    const existing = items.find((item) => item.id === product.id);
    
    if (existing) {
      set({
        items: items.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        ),
      });
    } else {
      set({ items: [...items, { id: product.id, product, quantity }] });
    }
  },

  removeItem: (productId) => {
    set({ items: get().items.filter((item) => item.id !== productId) });
  },

  updateQuantity: (productId, quantity) => {
    if (quantity <= 0) {
      get().removeItem(productId);
    } else {
      set({
        items: get().items.map((item) =>
          item.id === productId ? { ...item, quantity } : item
        ),
      });
    }
  },

  clearCart: () => set({ items: [] }),

  total: () => {
    return get().items.reduce(
      (sum, item) => sum + item.product.price * item.quantity,
      0
    );
  },
}));
