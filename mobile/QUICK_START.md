# 🚀 Quick Start Guide

## No Android Studio Required!

This app uses Expo, so you can test directly on your phone without any emulators.

## Step 1: Install Expo Go

Download the Expo Go app on your phone:
- **iOS**: [App Store](https://apps.apple.com/app/expo-go/id982107779)
- **Android**: [Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

## Step 2: Start the App

```bash
cd mobile
npm start
```

## Step 3: Scan QR Code

- **iOS**: Open Camera app and scan the QR code
- **Android**: Open Expo Go app and scan the QR code

The app will load on your phone!

## Important: API Configuration

Since you're testing on a physical device, you need to use your computer's IP address instead of localhost.

1. Find your computer's IP address:
   - Windows: Run `ipconfig` and look for IPv4 Address
   - Mac/Linux: Run `ifconfig` or `ip addr`

2. Update `mobile/src/config/api.ts`:
   ```typescript
   const API_URL = 'http://YOUR_IP_ADDRESS:8000/api';
   // Example: 'http://192.168.1.100:8000/api'
   ```

3. Make sure your Django backend is running and accessible:
   ```bash
   cd backend
   python manage.py runserver 0.0.0.0:8000
   ```

## Troubleshooting

**Can't connect to API?**
- Ensure your phone and computer are on the same WiFi network
- Check your firewall settings
- Verify the backend is running with `0.0.0.0:8000`

**App won't load?**
- Try clearing cache: `npm start -- --clear`
- Restart Expo Go app
- Check for error messages in the terminal

## Features Available

✅ User login/register
✅ Browse products
✅ View product details
✅ Add to cart
✅ Manage cart items
✅ Checkout

## Next Steps

Once the app is running, you can:
- Login with existing credentials
- Browse products from your backend
- Add items to cart
- Test the checkout flow

Happy coding! 🎉
