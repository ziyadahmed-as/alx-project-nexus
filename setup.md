# Quick Setup Guide

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ and npm installed
- Git installed

## Initial Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd multivendor-ecommerce
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Copy environment variables
cp .env.example .env

# Edit .env file with your actual values
# Use your preferred text editor (nano, vim, code, etc.)
nano .env

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser

# Create some categories (optional)
python manage.py shell
>>> from apps.products.models import Category
>>> Category.objects.create(name="Electronics", slug="electronics", description="Electronic devices and gadgets")
>>> Category.objects.create(name="Fashion", slug="fashion", description="Clothing and accessories")
>>> Category.objects.create(name="Home & Garden", slug="home-garden", description="Home and garden products")
>>> exit()

# Start development server
python manage.py runserver
```

Backend will be running at: http://localhost:8000

### 3. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Copy environment variables
cp .env.example .env.local

# Edit .env.local file with your actual values
nano .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be running at: http://localhost:3000

## Verify Installation

1. **Backend API**: Visit http://localhost:8000/api/docs/ to see API documentation
2. **Frontend**: Visit http://localhost:3000 to see the application
3. **Admin Panel**: Visit http://localhost:8000/admin/ to access Django admin

## Create Test Data

### Create Test Users

```bash
cd backend
python manage.py shell
```

```python
from apps.users.models import User

# Create admin user
admin = User.objects.create_superuser(
    username='admin',
    email='admin@example.com',
    password='admin123',
    first_name='Admin',
    last_name='User'
)

# Create vendor user
vendor = User.objects.create_user(
    username='vendor1',
    email='vendor1@example.com',
    password='vendor123',
    first_name='John',
    last_name='Vendor',
    role='vendor'
)

# Create buyer user
buyer = User.objects.create_user(
    username='buyer1',
    email='buyer1@example.com',
    password='buyer123',
    first_name='Jane',
    last_name='Buyer',
    role='buyer'
)

print("Test users created successfully!")
exit()
```

## Test the Application

### 1. Test Admin Login
- Go to http://localhost:3000/login
- Username: `admin`
- Password: `admin123`
- Should redirect to Admin Dashboard

### 2. Test Vendor Login
- Go to http://localhost:3000/login
- Username: `vendor1`
- Password: `vendor123`
- Should redirect to Vendor Dashboard
- Complete vendor profile setup

### 3. Test Buyer Login
- Go to http://localhost:3000/login
- Username: `buyer1`
- Password: `buyer123`
- Should redirect to Home Page

## Common Issues

### Issue: Port already in use
**Backend:**
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

**Frontend:**
```bash
# Kill process on port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:3000 | xargs kill -9
```

### Issue: Module not found
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Database errors
```bash
cd backend
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Issue: CORS errors
Make sure your backend `.env` has:
```
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

And frontend `.env.local` has:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Development Workflow

### Running Both Servers

**Option 1: Two Terminal Windows**
- Terminal 1: `cd backend && python manage.py runserver`
- Terminal 2: `cd frontend && npm run dev`

**Option 2: Using tmux/screen (Linux/macOS)**
```bash
# Start tmux
tmux

# Split window
Ctrl+B then "

# In first pane
cd backend && source venv/bin/activate && python manage.py runserver

# Switch to second pane (Ctrl+B then arrow key)
cd frontend && npm run dev
```

### Making Changes

1. **Backend Changes:**
   - Edit Python files
   - Django auto-reloads on file changes
   - If models changed: `python manage.py makemigrations && python manage.py migrate`

2. **Frontend Changes:**
   - Edit TypeScript/React files
   - Next.js auto-reloads on file changes
   - If dependencies changed: `npm install`

### Git Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Your commit message"

# Push
git push origin main
```

## Production Deployment

See `DEPLOYMENT.md` for production deployment instructions.

## Need Help?

- Check `GITIGNORE_GUIDE.md` for .gitignore configuration
- Check `DRAFT_SYSTEM.md` for product draft system
- Check `AUTO_DASHBOARD_REDIRECT.md` for authentication flow
- Check API documentation at http://localhost:8000/api/docs/

## Next Steps

1. Configure payment gateways (Stripe, Chapa)
2. Set up email service (Gmail SMTP or SendGrid)
3. Configure cloud storage for media files (AWS S3)
4. Set up Redis for caching (optional)
5. Configure Celery for background tasks (optional)
6. Set up monitoring and logging
7. Configure domain and SSL certificate
8. Set up CI/CD pipeline

## Useful Commands

### Backend
```bash
# Create new app
python manage.py startapp app_name

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Shell
python manage.py shell
```

### Frontend
```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

## Support

For issues and questions:
- Email: support@yourdomain.com
- GitHub Issues: <your-repo-url>/issues
