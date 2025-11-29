# E-Commerce Mobile App

React Native mobile app built with Expo for the multivendor e-commerce platform.

## Quick Start

1. **Install Expo Go on your phone**
   - iOS: Download from App Store
   - Android: Download from Google Play

2. **Start the development server**
   ```bash
   cd mobile
   npm start
   ```

3. **Scan the QR code**
   - Use Expo Go app to scan the QR code
   - App will load on your phone

## Features

- User authentication (login/register)
- Browse products
- Product details
- Shopping cart
- Add/remove items
- Checkout

## Tech Stack

- React Native with Expo
- TypeScript
- React Navigation
- Zustand (state management)
- Axios (API calls)
- Expo Secure Store (token storage)

## API Configuration

Update the API URL in `src/config/api.ts`:
```typescript
const API_URL = 'http://YOUR_IP:8000/api';
```

Note: Use your computer's IP address, not localhost, when testing on a physical device.

## Development

```bash
# Start development server
npm start

# Clear cache
npm start -- --clear
```

## Building for Production

```bash
# Build for Android
eas build --platform android

# Build for iOS
eas build --platform ios
```
