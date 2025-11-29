# Multivendor E-commerce Platform

Complete multivendor e-commerce platform with Django REST Framework backend and Next.js 15 PWA frontend.

## 🚀 Features

### Backend (Django REST Framework)
- ✅ JWT Authentication with role-based access (Admin, Vendor, Buyer)
- ✅ Vendor verification and management system with document upload
- ✅ Product & inventory management with categories and variations
- ✅ Multi-vendor order processing
- ✅ Stripe & Chapa payment integration (test mode enabled)
- ✅ Optimized queries with caching and indexing
- ✅ RESTful API with Swagger documentation
- ✅ Social media integration for vendors
- ✅ Office address verification

### Frontend (Next.js 15 PWA)
- ✅ Progressive Web App with offline support
- ✅ Mobile-first responsive design
- ✅ Real-time cart management with Zustand
- ✅ Enhanced Vendor and Admin dashboards with sidebars
- ✅ Secure payment processing (Stripe/Chapa)
- ✅ Product browsing with search and filters
- ✅ Social media sharing for products
- ✅ User profile management
- ✅ Order tracking system

## 📋 Quick Start

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
# .env file is already configured with SQLite
# No additional setup needed for development
```

5. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser:**
```bash
python manage.py createsuperuser
```

7. **Run server:**
```bash
python manage.py runserver
```

Backend will be available at: **http://127.0.0.1:8000/**

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install --legacy-peer-deps
```

3. **Configure environment:**
```bash
# Create .env.local file
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

4. **Run development server:**
```bash
npm run dev
```

Frontend will be available at: **http://localhost:3000/**

## 🎯 User Roles & Features

### 1. Admin
- **Dashboard**: Enhanced with sidebar navigation
  - View all vendors and verification status
  - Manage vendor approvals/rejections
  - View all orders and payments
  - Access platform analytics
  - Manage users and categories
- **Vendor Management**: Review documents, verify vendors
- **Full System Control**: Access to all platform features

### 2. Vendor
- **Dashboard**: Enhanced with sidebar navigation
  - View sales statistics
  - Manage products (add, edit, delete)
  - Track orders
  - Share store on social media
- **Product Management**: 
  - Add products with images
  - Set pricing and inventory
  - Manage categories
- **Profile Setup**: 
  - Business information
  - Office address
  - Document upload (business license, ID, tax certificate)
  - Social media links (Facebook, Instagram, X, Telegram)

### 3. Buyer
- **Shopping**: Browse products from multiple vendors
- **Cart Management**: Add/remove items, update quantities
- **Checkout**: Secure payment with Stripe or Chapa
- **Order Tracking**: View order status and history
- **Profile Management**: Update personal information
- **Become a Vendor**: Apply to sell on the platform

## 💳 Payment Integration

### Test Mode (Default)
- Payments are simulated for development
- No real payment processing
- Orders are automatically marked as completed

### Production Mode
- **Stripe**: International payments (USD, EUR, etc.)
- **Chapa**: Ethiopian payments (ETB)
- Configure API keys in `.env` file

## 🗂️ Project Structure

```
multivendor-ecommerce/
├── backend/
│   ├── apps/
│   │   ├── users/          # Authentication & roles
│   │   ├── vendors/        # Vendor management
│   │   ├── products/       # Product catalog
│   │   ├── orders/         # Order processing
│   │   └── payments/       # Payment handling
│   ├── config/             # Django settings
│   ├── media/              # Uploaded files
│   └── db.sqlite3          # Database
│
└── frontend/
    ├── src/
    │   ├── app/            # Next.js pages
    │   │   ├── admin/      # Admin dashboard
    │   │   ├── vendor/     # Vendor dashboard
    │   │   ├── products/   # Product pages
    │   │   ├── orders/     # Order pages
    │   │   ├── profile/    # User profile
    │   │   └── checkout/   # Checkout flow
    │   ├── components/     # Reusable components
    │   ├── lib/           # API client
    │   └── store/         # State management
    └── public/            # Static assets
```

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `GET /api/auth/profile/` - Get user profile
- `PATCH /api/auth/profile/` - Update profile

### Vendors
- `GET /api/vendors/` - List approved vendors
- `POST /api/vendors/create/` - Create vendor profile
- `GET /api/vendors/{id}/` - Vendor details
- `POST /api/vendors/{id}/verify/` - Verify vendor (admin)

### Products
- `GET /api/products/` - List products
- `POST /api/products/create/` - Create product
- `GET /api/products/{id}/` - Product details
- `GET /api/products/my-products/` - Vendor's products

### Orders
- `GET /api/orders/` - List orders
- `POST /api/orders/create/` - Create order
- `GET /api/orders/{id}/` - Order details

### Payments
- `POST /api/payments/create-intent/` - Create payment

**API Documentation**: http://localhost:8000/api/docs/

## 🛠️ Tech Stack

### Backend
- Django 5.0.1
- Django REST Framework 3.14.0
- SQLite (development) / PostgreSQL (production)
- JWT Authentication
- Pillow (image processing)

### Frontend
- Next.js 15.5.6
- React 19.2.0
- TypeScript 5.6.3
- Tailwind CSS 3.4.14
- Zustand 5.0.8 (state management)
- Axios 1.7.7 (HTTP client)

## 🎨 Key Features Implemented

### ✅ User Management
- Role-based authentication (Admin, Vendor, Buyer)
- Profile management with avatar
- Password change functionality
- User verification system

### ✅ Vendor System
- Application process with document upload
- Admin verification workflow
- Business information management
- Office address verification
- Social media integration
- Product management dashboard

### ✅ Product Management
- Category system
- Product variations
- Image upload
- Stock management
- SKU generation
- Featured products

### ✅ Order System
- Multi-vendor cart
- Order tracking
- Status management
- Payment integration
- Order history

### ✅ Payment Processing
- Stripe integration
- Chapa integration
- Test mode for development
- Payment verification
- Transaction history

### ✅ Social Features
- Product sharing (Facebook, X, Telegram, WhatsApp)
- Vendor store sharing
- Referral tracking via URL parameters

### ✅ UI/UX
- Responsive design
- Enhanced dashboards with sidebars
- Loading states
- Toast notifications
- Empty states
- Icon-based actions

## 🚀 Deployment

### Backend (Production)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Frontend (Production)
```bash
# Build for production
npm run build

# Start production server
npm start
```

## 📝 Environment Variables

### Backend (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Payment Gateways (leave empty for test mode)
STRIPE_SECRET_KEY=
CHAPA_SECRET_KEY=
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_STRIPE_KEY=your_stripe_publishable_key
```

## 📱 Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000/api
- **Admin Panel**: http://127.0.0.1:8000/admin
- **API Docs**: http://127.0.0.1:8000/api/docs

## 🎓 Default Test Accounts

Create these via Django admin or registration:
- **Admin**: Full system access
- **Vendor**: Product management access
- **Buyer**: Shopping access

## 📄 License

MIT License - Feel free to use this project for learning or commercial purposes.

## 🤝 Contributing

This is a complete e-commerce platform ready for customization and deployment. Feel free to extend it with additional features!

---

**Built with ❤️ using Django REST Framework & Next.js**
