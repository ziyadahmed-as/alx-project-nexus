# Mobile App Troubleshooting Guide

## ✅ App Status: Running Successfully!

The mobile app has been bundled successfully and is ready to use.

## 📱 How to Test

1. **Install Expo Go** on your phone:
   - iOS: App Store
   - Android: Google Play Store

2. **Scan the QR Code** shown in your terminal

3. **Wait for the app to load** on your phone

## 🔧 Common Issues & Solutions

### Issue: "Cannot connect to API"

**Solution:**
- The API URL has been configured to: `http://10.92.142.155:8000/api`
- Make sure your phone and computer are on the same WiFi network
- Verify the backend is running: `http://10.92.142.155:8000/api`

### Issue: "Network request failed"

**Solution:**
1. Check if backend is accessible:
   ```bash
   # In a browser or curl, test:
   http://10.92.142.155:8000/api/products/
   ```

2. Make sure Django is running with `0.0.0.0:8000`:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

3. Check Windows Firewall settings - allow port 8000

### Issue: "App won't load on phone"

**Solution:**
1. Make sure Expo Go is installed
2. Check that you're on the same WiFi network
3. Try restarting the Expo server:
   - Press `Ctrl+C` in the terminal
   - Run `npm start` again
   - Scan the new QR code

### Issue: "White screen or crash"

**Solution:**
1. Check the terminal for error messages
2. Shake your phone to open the Expo menu
3. Select "Reload"
4. If still not working, clear cache:
   ```bash
   npm start -- --clear
   ```

## 🎯 Testing the App

Once loaded, you can:

1. **Register a new account**
   - Click "Don't have an account? Register"
   - Fill in your details
   - Submit

2. **Login**
   - Use your credentials
   - You'll be redirected to the Home screen

3. **Browse Products**
   - View product list
   - Tap on a product to see details

4. **Add to Cart**
   - On product detail page, tap "Add to Cart"
   - Navigate to Cart screen

5. **Manage Cart**
   - Increase/decrease quantities
   - Remove items
   - Proceed to checkout

## 📊 Current Configuration

- **Backend API**: http://10.92.142.155:8000/api
- **Expo Server**: exp://10.92.142.155:8081
- **Frontend Web**: http://10.92.142.155:3001

## 🔍 Debug Mode

To see detailed logs:
1. Shake your phone
2. Select "Debug Remote JS"
3. Check browser console for errors

## 📝 Notes

- The app uses JWT authentication
- Tokens are stored securely using Expo SecureStore
- All API calls go through the configured backend
- Make sure backend has CORS configured for mobile access

## 🆘 Still Having Issues?

Check the terminal output for specific error messages and look for:
- Network errors
- Authentication errors
- API endpoint errors
- Bundle errors

The app is currently running and ready to test!
