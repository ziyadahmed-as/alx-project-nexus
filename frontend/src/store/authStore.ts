import { create } from 'zustand';
import api from '@/lib/api';

interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'vendor' | 'buyer';
  first_name: string;
  last_name: string;
  phone?: string;
  avatar?: string;
  is_verified?: boolean;
  created_at?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<User>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  
  login: async (username, password) => {
    const response = await api.post('/auth/login/', { username, password });
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    set({ user: response.data.user, isAuthenticated: true });
    return response.data.user;
  },
  
  register: async (data) => {
    await api.post('/auth/register/', data);
  },
  
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    set({ user: null, isAuthenticated: false });
  },
  
  fetchUser: async () => {
    try {
      const response = await api.get('/auth/profile/');
      set({ user: response.data, isAuthenticated: true });
    } catch (error) {
      set({ user: null, isAuthenticated: false });
    }
  },
}));
