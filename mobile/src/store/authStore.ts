import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import api from '../config/api';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_vendor: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post('/users/login/', { email, password });
      await SecureStore.setItemAsync('token', data.access);
      set({ token: data.access, user: data.user });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (email, password, firstName, lastName) => {
    set({ isLoading: true });
    try {
      await api.post('/users/register/', {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('token');
    set({ user: null, token: null });
  },

  loadUser: async () => {
    const token = await SecureStore.getItemAsync('token');
    if (token) {
      try {
        const { data } = await api.get('/users/profile/');
        set({ user: data, token });
      } catch {
        await SecureStore.deleteItemAsync('token');
      }
    }
  },
}));
