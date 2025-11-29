# 🛍️ Professional Multivendor E-commerce Platform

> **Enterprise-grade marketplace solution with advanced features comparable to Amazon, eBay, and Etsy**

A complete, production-ready multivendor e-commerce platform built with Django REST Framework (Backend) and Next.js 15 (Frontend). Features include vendor management, product variations, advanced filtering, payment integration, and much more.

[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.0-38B2AC.svg)](https://tailwindcss.com/)

---

## ✨ Key Features

### 🏪 Multi-Vendor System
- Complete vendor registration & verification workflow
- Document upload & admin approval
- Vendor dashboard with analytics
- Product management (CRUD)
- Order tracking & management

### 📦 Advanced Product Management
- **Draft System** - Quality control before publishing
- **Product Variations** - Size, color, material options
- **Multiple Images** - Gallery with primary image selection
- **Smart Categorization** - Multi-level categories
- **Stock Management** - Real-time inventory tracking
- **Featured Products** - Admin-curated highlights

### 🔍 Powerful Search & Filtering
- Full-text search
- Price range filtering (budget)
- Location-based filtering
- Date range filtering
- Category filtering
- Multiple sorting options

### 🛒 Shopping Experience
- Intuitive shopping cart
- Guest checkout support
- Multiple payment gateways (Stripe, Chapa)
- Order tracking
- Social media sharing
- Product reviews (ready)

### 👥 User Management
- Role-based access (Admin, Vendor, Buyer)
- JWT authentication
- Profile management
- Secure password handling
- Email verification (ready)

### 🎨 Modern UI/UX
- Responsive design (mobile-first)
- Progressive Web App (PWA)
- Loading states & animations
- Toast notifications
- Intuitive navigation

### 🔒 Security Features
- Vendor self-purchase prevention
- Input validation & sanitization
- CORS protection
- Secure file uploads
- Role-based permissions

### 📊 Analytics & Reporting
- Sales tracking
- Product views
- Vendor performance
- Dashboard metrics
- Revenue tracking

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL (optional, SQLite for development)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd multivendor-ecommerce

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

Visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs/

📖 **Detailed setup guide:** [setup.md](setup.md)

---

## 📁 Project Structure

```
multivendor-ecommerce/
├── backend/                 # Django REST Framework
│   ├── apps/
│   │   ├── users/          # User management
│   │   ├── vendors/        # Vendor profiles
│   │   ├── products/       # Product management
│   │   ├── orders/         # Order processing
│   │   └── payments/       # Payment integration
│   ├── config/             # Django settings
│   └── media/              # User uploads
│
├── frontend/               # Next.js 15
│   ├── src/
│   │   ├── app/           # Pages & routes
│   │   ├── components/    # Reusable components
│   │   ├── store/         # State management
│   │   └── lib/           # Utilities
│   └── public/            # Static assets
│
└── docs/                  # Documentation
    ├── PROFESSIONAL_ECOMMERCE_FEATURES.md
    ├── DRAFT_SYSTEM.md
    ├── PRODUCT_SORTING_FEATURES.md
    └── ...
```

---

## 🎯 Core Functionality

### For Buyers
✅ Browse products with advanced filters  
✅ Search by name, price, location, date  
✅ Add to cart & checkout  
✅ Multiple payment options  
✅ Track orders  
✅ Share products on social media  

### For Vendors
✅ Register & get verified  
✅ Create & manage products  
✅ Upload multiple images  
✅ Add product variations  
✅ Track sales & analytics  
✅ Manage orders  
✅ Share store on social media  

### For Admins
✅ Approve/reject vendors  
✅ Manage all products  
✅ Moderate content  
✅ View analytics  
✅ Manage categories  
✅ System oversight  

---

## 🛠️ Technology Stack

### Backend
- **Framework:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL / SQLite
- **Authentication:** JWT (Simple JWT)
- **API Docs:** drf-spectacular (Swagger)
- **File Storage:** Local / AWS S3 (ready)
- **Task Queue:** Celery (ready)
- **Cache:** Redis (ready)

### Frontend
- **Framework:** Next.js 15 (React 18)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** Zustand
- **HTTP Client:** Axios
- **Notifications:** React Hot Toast
- **PWA:** next-pwa (ready)

### Payment Integration
- **Stripe:** International payments
- **Chapa:** Ethiopian payment gateway

---

## 📚 Documentation

### Setup & Configuration
- [Quick Setup Guide](setup.md)
- [Environment Variables](backend/.env.example)
- [Git Ignore Guide](GITIGNORE_GUIDE.md)

### Features
- [Professional E-commerce Features](PROFESSIONAL_ECOMMERCE_FEATURES.md)
- [Draft System](DRAFT_SYSTEM.md)
- [Product Sorting & Filtering](PRODUCT_SORTING_FEATURES.md)
- [Vendor Self-Purchase Prevention](VENDOR_SELF_PURCHASE_PREVENTION.md)
- [Auto Dashboard Redirect](AUTO_DASHBOARD_REDIRECT.md)

### API
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/schema/

---

## 🔐 Security

- ✅ JWT authentication
- ✅ Role-based access control
- ✅ Input validation & sanitization
- ✅ CORS protection
- ✅ Secure file uploads
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CSRF protection

---

## 🌐 Internationalization

- English (default)
- Amharic (ready)
- Oromo (ready)
- Multi-currency support (ready)

---

## 📈 Performance

- ⚡ Server-side rendering (SSR)
- ⚡ Static generation
- ⚡ Image optimization
- ⚡ Code splitting
- ⚡ Lazy loading
- ⚡ Database indexing
- ⚡ API caching (ready)

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

---

## 🚀 Deployment

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure production database
- [ ] Set up AWS S3 for media
- [ ] Configure email service
- [ ] Set up Redis for caching
- [ ] Configure Celery for tasks
- [ ] Set up monitoring
- [ ] Configure backup system
- [ ] Set up SSL certificate
- [ ] Configure CDN

### Deployment Options
- **Backend:** Heroku, AWS, DigitalOcean, Railway
- **Frontend:** Vercel, Netlify, AWS Amplify
- **Database:** AWS RDS, DigitalOcean Managed DB
- **Media:** AWS S3, Cloudinary

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Django REST Framework team
- Next.js team
- Tailwind CSS team
- All open-source contributors

---

## 📞 Support

- 📧 Email: support@yourdomain.com
- 📖 Documentation: Full documentation available in `/docs`
- 🐛 Issues: GitHub Issues

---

**Built with ❤️ using Django, Next.js, and modern web technologies**
