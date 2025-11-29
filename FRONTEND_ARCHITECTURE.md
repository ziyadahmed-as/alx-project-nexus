# Frontend Architecture Documentation

## Overview
The frontend is built with **Next.js 15**, **React 18**, and **TypeScript**, following modern best practices for performance, SEO, and user experience.

---

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── (auth)/               # Authentication routes
│   │   │   ├── login/
│   │   │   └── register/
│   │   │
│   │   ├── admin/                # Admin dashboard
│   │   │   ├── dashboard/
│   │   │   ├── vendors/
│   │   │   ├── products/
│   │   │   ├── orders/
│   │   │   ├── users/
│   │   │   └── categories/
│   │   │
│   │   ├── vendor/               # Vendor dashboard
│   │   │   ├── dashboard/
│   │   │   ├── products/
│   │   │   │   ├── new/
│   │   │   │   └── [id]/edit/
│   │   │   └── setup/
│   │   │
│   │   ├── products/             # Product pages
│   │   │   ├── page.tsx         # Product listing
│   │   │   └── [id]/            # Product detail
│   │   │
│   │   ├── vendors/              # Vendor storefronts
│   │   │   └── [id]/
│   │   │
│   │   ├── profile/              # User profile
│   │   │   ├── page.tsx
│   │   │   └── settings/
│   │   │
│   │   ├── cart/                 # Shopping cart
│   │   ├── checkout/             # Checkout process
│   │   ├── orders/               # Order history
│   │   │
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home page
│   │   └── globals.css           # Global styles
│   │
│   ├── components/               # Reusable components
│   │   ├── Navbar.tsx
│   │   ├── ProductCard.tsx
│   │   ├── SocialShare.tsx
│   │   └── ...
│   │
│   ├── store/                    # State management (Zustand)
│   │   ├── authStore.ts         # Authentication state
│   │   └── cartStore.ts         # Shopping cart state
│   │
│   └── lib/                      # Utilities
│       ├── api.ts               # Axios instance
│       └── utils.ts             # Helper functions
│
├── public/                       # Static assets
│   ├── manifest.json            # PWA manifest
│   └── icons/
│
├── next.config.js               # Next.js configuration
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
└── package.json                 # Dependencies
```

---

## 📦 Core Technologies

### 1. Next.js 15 (App Router)
**Features:**
- Server-side rendering (SSR)
- Static site generation (SSG)
- API routes
- File-based routing
- Image optimization
- Font optimization

**Example:**
```typescript
// app/products/page.tsx
export default function ProductsPage() {
  // Server Component by default
  return <div>Products</div>
}

// app/products/[id]/page.tsx
export default function ProductDetail({ params }: { params: { id: string } }) {
  return <div>Product {params.id}</div>
}
```

### 2. React 18
**Features:**
- Hooks (useState, useEffect, useContext)
- Client Components ('use client')
- Suspense boundaries
- Error boundaries

**Example:**
```typescript
'use client';

import { useState, useEffect } from 'react';

export default function ProductList() {
  const [products, setProducts] = useState([]);
  
  useEffect(() => {
    fetchProducts();
  }, []);
  
  return <div>{/* Render products */}</div>
}
```

### 3. TypeScript
**Benefits:**
- Type safety
- Better IDE support
- Catch errors early
- Self-documenting code

**Example:**
```typescript
interface Product {
  id: number;
  name: string;
  price: string;
  stock: number;
  images?: ProductImage[];
}

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  return <div>{product.name}</div>
}
```

### 4. Tailwind CSS
**Benefits:**
- Utility-first CSS
- Responsive design
- Dark mode support
- Custom theming

**Example:**
```tsx
<button className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition">
  Add to Cart
</button>
```

---

## 🎯 State Management

### Zustand Stores

#### Auth Store (`store/authStore.ts`)
```typescript
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  
  login: async (username, password) => {
    const response = await api.post('/auth/login/', { username, password });
    localStorage.setItem('access_token', response.data.access);
    set({ user: response.data.user, isAuthenticated: true });
    return response.data.user;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, isAuthenticated: false });
  },
}));
```

**Usage:**
```typescript
const { user, isAuthenticated, login, logout } = useAuthStore();

// Login
await login('username', 'password');

// Check auth
if (isAuthenticated) {
  console.log(user.role);
}

// Logout
logout();
```

#### Cart Store (`store/cartStore.ts`)
```typescript
interface CartState {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: number) => void;
  updateQuantity: (id: number, quantity: number) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  
  addItem: (item) => {
    const items = get().items;
    const existing = items.find(i => i.id === item.id);
    
    if (existing) {
      set({
        items: items.map(i =>
          i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
        )
      });
    } else {
      set({ items: [...items, { ...item, quantity: 1 }] });
    }
  },
  
  total: () => {
    return get().items.reduce((sum, item) => 
      sum + item.price * item.quantity, 0
    );
  },
}));
```

---

## 🔌 API Integration

### Axios Instance (`lib/api.ts`)
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

**Usage:**
```typescript
// GET request
const response = await api.get('/products/');
const products = response.data;

// POST request
const response = await api.post('/products/create/', {
  name: 'Product Name',
  price: 99.99
});

// File upload
const formData = new FormData();
formData.append('image', file);
await api.post('/products/upload/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

---

## 🎨 Component Patterns

### 1. Server Components (Default)
```typescript
// app/products/page.tsx
export default function ProductsPage() {
  // Runs on server
  // Can directly access database
  // No JavaScript sent to client
  return <div>Products</div>
}
```

### 2. Client Components
```typescript
'use client';

// app/cart/page.tsx
import { useState } from 'react';

export default function CartPage() {
  const [items, setItems] = useState([]);
  // Interactive, uses hooks
  return <div>Cart</div>
}
```

### 3. Reusable Components
```typescript
// components/ProductCard.tsx
interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  );
}
```

### 4. Layout Components
```typescript
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
```

---

## 🚀 Routing

### File-Based Routing
```
app/
├── page.tsx                    → /
├── products/
│   ├── page.tsx               → /products
│   └── [id]/
│       └── page.tsx           → /products/123
├── vendors/
│   └── [id]/
│       └── page.tsx           → /vendors/456
└── admin/
    └── dashboard/
        └── page.tsx           → /admin/dashboard
```

### Dynamic Routes
```typescript
// app/products/[id]/page.tsx
export default function ProductDetail({ params }: { params: { id: string } }) {
  const productId = params.id;
  return <div>Product {productId}</div>
}
```

### Navigation
```typescript
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// Programmatic navigation
const router = useRouter();
router.push('/products');
router.back();

// Link component
<Link href="/products">Products</Link>
```

---

## 🎨 Styling

### Tailwind CSS Classes
```tsx
// Responsive design
<div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">

// Hover effects
<button className="bg-primary hover:bg-blue-600 transition">

// Conditional classes
<span className={`px-3 py-1 rounded-full ${
  status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
}`}>

// Custom colors (tailwind.config.js)
colors: {
  primary: '#3B82F6',
  secondary: '#10B981',
}
```

### Global Styles
```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn-primary {
    @apply bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600;
  }
}
```

---

## 🔐 Authentication Flow

### 1. Login Process
```typescript
// app/login/page.tsx
const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    const userData = await login(username, password);
    toast.success('Login successful!');
    
    // Role-based redirect
    if (userData.role === 'admin') {
      router.push('/admin/dashboard');
    } else if (userData.role === 'vendor') {
      router.push('/vendor/dashboard');
    } else {
      router.push('/');
    }
  } catch (error) {
    toast.error('Login failed');
  }
};
```

### 2. Protected Routes
```typescript
// app/vendor/dashboard/page.tsx
useEffect(() => {
  if (!isAuthenticated) {
    router.push('/login');
    return;
  }
  if (user?.role !== 'vendor') {
    router.push('/');
    return;
  }
}, [isAuthenticated, user]);
```

### 3. Conditional Rendering
```typescript
{isAuthenticated ? (
  <Link href="/profile">Profile</Link>
) : (
  <Link href="/login">Login</Link>
)}
```

---

## 📱 Responsive Design

### Mobile-First Approach
```tsx
<div className="
  px-4              // Mobile: 16px padding
  md:px-8           // Tablet: 32px padding
  lg:px-12          // Desktop: 48px padding
">
  <div className="
    grid 
    grid-cols-1     // Mobile: 1 column
    md:grid-cols-2  // Tablet: 2 columns
    lg:grid-cols-4  // Desktop: 4 columns
    gap-6
  ">
    {products.map(product => (
      <ProductCard key={product.id} product={product} />
    ))}
  </div>
</div>
```

### Breakpoints
```javascript
// tailwind.config.js
theme: {
  screens: {
    'sm': '640px',   // Mobile landscape
    'md': '768px',   // Tablet
    'lg': '1024px',  // Desktop
    'xl': '1280px',  // Large desktop
    '2xl': '1536px', // Extra large
  }
}
```

---

## ⚡ Performance Optimization

### 1. Image Optimization
```typescript
import Image from 'next/image';

<Image
  src="/product.jpg"
  alt="Product"
  width={500}
  height={500}
  priority  // Load immediately
  placeholder="blur"  // Show blur while loading
/>
```

### 2. Code Splitting
```typescript
import dynamic from 'next/dynamic';

// Lazy load component
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
  ssr: false  // Don't render on server
});
```

### 3. Memoization
```typescript
import { useMemo, useCallback } from 'react';

// Memoize expensive calculations
const total = useMemo(() => {
  return items.reduce((sum, item) => sum + item.price, 0);
}, [items]);

// Memoize functions
const handleClick = useCallback(() => {
  console.log('Clicked');
}, []);
```

---

## 🎯 Best Practices

### 1. Component Organization
```typescript
// ✅ Good - Single responsibility
function ProductCard({ product }) {
  return <div>{product.name}</div>
}

function ProductList({ products }) {
  return products.map(p => <ProductCard key={p.id} product={p} />)
}

// ❌ Bad - Too much in one component
function ProductPage() {
  // Fetching, filtering, rendering all in one
}
```

### 2. Type Safety
```typescript
// ✅ Good - Typed props
interface Props {
  product: Product;
  onAdd: (id: number) => void;
}

// ❌ Bad - Any types
function Component(props: any) {}
```

### 3. Error Handling
```typescript
// ✅ Good - Try/catch with user feedback
try {
  await api.post('/products/', data);
  toast.success('Product created!');
} catch (error) {
  toast.error('Failed to create product');
  console.error(error);
}

// ❌ Bad - Silent failures
await api.post('/products/', data);
```

### 4. Loading States
```typescript
// ✅ Good - Show loading state
{loading ? (
  <div>Loading...</div>
) : (
  <ProductList products={products} />
)}

// ❌ Bad - No feedback
<ProductList products={products} />
```

---

## 🧪 Testing

### Component Testing
```typescript
import { render, screen } from '@testing-library/react';
import ProductCard from './ProductCard';

test('renders product name', () => {
  const product = { id: 1, name: 'Test Product', price: '99.99' };
  render(<ProductCard product={product} />);
  expect(screen.getByText('Test Product')).toBeInTheDocument();
});
```

---

## 🚀 Deployment

### Build Process
```bash
# Development
npm run dev

# Production build
npm run build

# Start production server
npm start
```

### Environment Variables
```env
# .env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_xxxxx
```

### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Zustand](https://github.com/pmndrs/zustand)

---

**Built with Next.js 15 + React 18 + TypeScript**
