# Multivendor E-commerce Backend

Django REST Framework backend for the multivendor e-commerce platform.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run server:
```bash
python manage.py runserver
```

## API Documentation

Visit http://localhost:8000/api/docs/ for Swagger UI documentation.

## Key Features

- JWT Authentication
- Role-based access (Admin, Vendor, Buyer)
- Vendor verification system
- Product & inventory management
- Order processing
- Stripe & Chapa payment integration
- Optimized queries with caching
