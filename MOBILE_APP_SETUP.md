# React Native Mobile App Setup Guide

## Overview
This guide will help you create a React Native mobile app using Expo for the multivendor e-commerce platform. No Android Studio required!

---

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ installed
- npm or yarn
- Expo Go app on your phone (iOS/Android)

### Installation Steps

```bash
# 1. Create new Expo project
cd multivendor-ecommerce
npx create-expo-app mobile --template blank-typescript

# 2. Navigate to mobile directory
cd mobile

# 3. Install dependencies
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install axios zustand
npm install @expo/vector-icons
npm install expo-image-picker expo-secure-store
npm install react-native-toast-message

# 4. Start development server
npx expo start
```

### Running the App

1. **On Your Phone:**
   - Install "Expo Go" from App Store (iOS) or Play Store (Android)
   - Scan the QR code shown in terminal
   - App will load on your phone

2. **On Emulator (Optional):**
   - Press `a` for Android emulator
   - Press `i` for iOS simulator (Mac only)

---

## 📁 Project Structure

```
mobile/
├── src/
│   ├── screens/              # App screens
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   └── RegisterScreen.tsx
│   │   ├── home/
│   │   │   └── HomeScreen.tsx
│   │   ├── products/
│   │   │   ├── ProductListScreen.tsx
│   │   │   └── ProductDetailScreen.tsx
│   │   ├── cart/
│   │   │   └── CartScreen.tsx
│   │   ├── profile/
│   │   │   └── ProfileScreen.tsx
│   │   └── vendor/
│   │       └── VendorDashboardScreen.tsx
│   │
│   ├── components/          # Reusable components
│   │   ├── ProductCard.tsx
│   │   ├── Header.tsx
│   │   └── Button.tsx
│   │
│   ├── navigation/          # Navigation setup
│   │   ├── AppNavigator.tsx
│   │   └── AuthNavigator.tsx
│   │
│   ├── store/              # State management
│   │   ├── authStore.ts
│   │   └── cartStore.ts
│   │
│   ├── services/           # API services
│   │   └── api.ts
│   │
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   │
│   └── utils/              # Utilities
│       └── helpers.ts
│
├── assets/                 # Images, fonts
├── App.tsx                # Entry point
├── app.json              # Expo configuration
└── package.json          # Dependencies
```

---

## 🎯 Key Features to Implement

### 1. Authentication
- Login/Register screens
- JWT token storage
- Role-based navigation

### 2. Product Browsing
- Product list with filters
- Product detail with images
- Search functionality
- Categories

### 3. Shopping Cart
- Add/remove items
- Update quantities
- Persistent cart

### 4. Checkout
- Shipping address
- Payment integration
- Order confirmation

### 5. User Profile
- View/edit profile
- Order history
- Settings

### 6. Vendor Features
- Vendor dashboard
- Product management
- Order management

---

## 📱 Sample Implementation

### App.tsx
```typescript
import { NavigationContainer } from '@react-navigation/native';
import { useAuthStore } from './src/store/authStore';
import AuthNavigator from './src/navigation/AuthNavigator';
import AppNavigator from './src/navigation/AppNavigator';
import Toast from 'react-native-toast-message';

export default function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <>
      <NavigationContainer>
        {isAuthenticated ? <AppNavigator /> : <AuthNavigator />}
      </NavigationContainer>
      <Toast />
    </>
  );
}
```

### API Service (src/services/api.ts)
```typescript
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_URL = 'http://YOUR_BACKEND_IP:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### Auth Store (src/store/authStore.ts)
```typescript
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import api from '../services/api';

interface AuthState {
  user: any | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login: async (username, password) => {
    const response = await api.post('/auth/login/', { username, password });
    await SecureStore.setItemAsync('access_token', response.data.access);
    set({ user: response.data.user, isAuthenticated: true });
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('access_token');
    set({ user: null, isAuthenticated: false });
  },
}));
```

### Login Screen (src/screens/auth/LoginScreen.tsx)
```typescript
import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useAuthStore } from '../../store/authStore';
import Toast from 'react-native-toast-message';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuthStore();

  const handleLogin = async () => {
    try {
      await login(username, password);
      Toast.show({ type: 'success', text1: 'Login successful!' });
    } catch (error) {
      Toast.show({ type: 'error', text1: 'Login failed' });
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Login</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      
      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>Login</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 30,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#3B82F6',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
```

### Product Card Component
```typescript
import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';

interface ProductCardProps {
  product: any;
  onPress: () => void;
}

export default function ProductCard({ product, onPress }: ProductCardProps) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <Image
        source={{ uri: product.images?.[0]?.image || 'https://via.placeholder.com/150' }}
        style={styles.image}
      />
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={2}>{product.name}</Text>
        <Text style={styles.price}>${product.price}</Text>
        {product.featured && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>⭐ Featured</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  image: {
    width: '100%',
    height: 200,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
  },
  info: {
    padding: 12,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 5,
  },
  price: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#3B82F6',
  },
  badge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginTop: 5,
  },
  badgeText: {
    fontSize: 12,
    color: '#92400E',
    fontWeight: '600',
  },
});
```

---

## 🔧 Configuration

### app.json
```json
{
  "expo": {
    "name": "Multivendor Shop",
    "slug": "multivendor-shop",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "updates": {
      "fallbackToCacheTimeout": 0
    },
    "assetBundlePatterns": [
      "**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.yourcompany.multivendorshop"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#FFFFFF"
      },
      "package": "com.yourcompany.multivendorshop"
    },
    "web": {
      "favicon": "./assets/favicon.png"
    }
  }
}
```

---

## 🌐 Connecting to Backend

### Important Notes:

1. **Local Development:**
   ```typescript
   // Use your computer's IP address, not localhost
   const API_URL = 'http://192.168.1.100:8000/api';
   ```

2. **Find Your IP:**
   ```bash
   # Windows
   ipconfig
   
   # Mac/Linux
   ifconfig
   ```

3. **Update Django ALLOWED_HOSTS:**
   ```python
   # backend/config/settings.py
   ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.100']
   ```

4. **Update CORS:**
   ```python
   CORS_ALLOWED_ORIGINS = [
       'http://localhost:3000',
       'http://192.168.1.100:8000',
   ]
   ```

---

## 📦 Complete Package.json

```json
{
  "name": "mobile",
  "version": "1.0.0",
  "main": "node_modules/expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  },
  "dependencies": {
    "expo": "~49.0.0",
    "expo-status-bar": "~1.6.0",
    "react": "18.2.0",
    "react-native": "0.72.6",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "@react-navigation/bottom-tabs": "^6.5.11",
    "react-native-screens": "~3.25.0",
    "react-native-safe-area-context": "4.7.4",
    "axios": "^1.6.0",
    "zustand": "^4.4.6",
    "@expo/vector-icons": "^13.0.0",
    "expo-image-picker": "~14.5.0",
    "expo-secure-store": "~12.5.0",
    "react-native-toast-message": "^2.1.7"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0",
    "@types/react": "~18.2.14",
    "typescript": "^5.1.3"
  }
}
```

---

## 🎨 Design System

### Colors
```typescript
export const Colors = {
  primary: '#3B82F6',
  secondary: '#10B981',
  danger: '#EF4444',
  warning: '#F59E0B',
  success: '#10B981',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  },
};
```

---

## 🚀 Building for Production

### Build APK (Android)
```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure build
eas build:configure

# Build APK
eas build --platform android --profile preview
```

### Build for iOS
```bash
# Build for iOS (requires Apple Developer account)
eas build --platform ios
```

---

## 📱 Features Checklist

- [ ] Authentication (Login/Register)
- [ ] Product browsing
- [ ] Product search & filters
- [ ] Product details
- [ ] Shopping cart
- [ ] Checkout process
- [ ] Order history
- [ ] User profile
- [ ] Vendor dashboard
- [ ] Push notifications
- [ ] Offline support
- [ ] Image caching
- [ ] Pull to refresh
- [ ] Infinite scroll

---

## 🐛 Troubleshooting

### Common Issues:

1. **Can't connect to backend:**
   - Use IP address, not localhost
   - Check firewall settings
   - Ensure backend is running

2. **Expo Go not loading:**
   - Ensure phone and computer on same WiFi
   - Try tunnel mode: `npx expo start --tunnel`

3. **Image not loading:**
   - Check image URLs
   - Ensure CORS is configured
   - Use absolute URLs

---

## 📚 Resources

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)
- [React Navigation](https://reactnavigation.org/)
- [Expo Go App](https://expo.dev/client)

---

## 🎯 Next Steps

1. Set up project structure
2. Implement authentication
3. Create product screens
4. Add shopping cart
5. Implement checkout
6. Add vendor features
7. Test on real devices
8. Build and deploy

---

**Ready to build your mobile app! 📱**
