# Backend Architecture Documentation

## Overview
The backend is built with **Django 4.2** and **Django REST Framework**, following best practices for scalable, maintainable, and secure API development.

---

## 🏗️ Project Structure

```
backend/
├── apps/                          # Django applications
│   ├── users/                     # User management & authentication
│   │   ├── models.py             # User model with roles
│   │   ├── serializers.py        # User data serialization
│   │   ├── views.py              # Authentication endpoints
│   │   └── urls.py               # User routes
│   │
│   ├── vendors/                   # Vendor management
│   │   ├── models.py             # VendorProfile model
│   │   ├── serializers.py        # Vendor data serialization
│   │   ├── views.py              # Vendor CRUD & verification
│   │   ├── permissions.py        # Custom permissions
│   │   └── urls.py               # Vendor routes
│   │
│   ├── products/                  # Product management
│   │   ├── models.py             # Product, Category, Image, Variation
│   │   ├── serializers.py        # Product data serialization
│   │   ├── views.py              # Product CRUD & filtering
│   │   ├── recommendations.py    # Recommendation engine
│   │   └── urls.py               # Product routes
│   │
│   ├── orders/                    # Order processing
│   │   ├── models.py             # Order, OrderItem models
│   │   ├── serializers.py        # Order data serialization
│   │   ├── views.py              # Order creation & management
│   │   └── urls.py               # Order routes
│   │
│   └── payments/                  # Payment integration
│       ├── models.py             # Payment records
│       ├── views.py              # Stripe & Chapa integration
│       └── urls.py               # Payment routes
│
├── config/                        # Project configuration
│   ├── settings.py               # Django settings
│   ├── urls.py                   # Root URL configuration
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
│
├── media/                         # User uploads
│   ├── products/                 # Product images
│   ├── categories/               # Category images
│   ├── avatars/                  # User avatars
│   └── vendor_logos/             # Vendor logos
│
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
└── .env                          # Environment variables
```

---

## 📦 Core Components

### 1. Models Layer

#### User Model (`apps/users/models.py`)
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('vendor', 'Vendor'),
        ('buyer', 'Buyer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
```

**Features:**
- Role-based access control
- Email and phone verification
- Profile customization
- JWT authentication ready

#### VendorProfile Model (`apps/vendors/models.py`)
```python
class VendorProfile(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # Document fields for verification
    business_license = models.FileField(upload_to='vendor_docs/')
    # Social media integration
    facebook_url = models.URLField(blank=True)
```

**Features:**
- Document verification system
- Admin approval workflow
- Social media integration
- Office address tracking

#### Product Model (`apps/products/models.py`)
```python
class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    featured = models.BooleanField(default=False)
    
    def is_complete(self):
        """Check if product has all required information"""
        has_images = self.images.exists()
        has_category = self.category is not None
        has_basic_info = all([self.name, self.description, self.price > 0])
        return has_images and has_category and has_basic_info
```

**Features:**
- Draft system for quality control
- Product variations support
- Multiple images
- Automatic status management
- View and sales tracking

### 2. Serializers Layer

**Purpose:** Convert complex data types to JSON and validate input

```python
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    is_complete = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['vendor', 'views', 'sales_count', 'status']
```

**Features:**
- Nested serialization
- Custom fields
- Validation logic
- Read-only fields

### 3. Views Layer

#### Class-Based Views (CBV)
```python
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'vendor', 'featured']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'sales_count']
    
    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, 
            status='published'
        ).order_by('-featured', '-created_at')
```

**Features:**
- Generic views for CRUD operations
- Built-in filtering and pagination
- Permission classes
- Query optimization

#### Function-Based Views (FBV)
```python
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdmin])
def verify_vendor(request, pk):
    """Admin endpoint to verify vendors"""
    vendor = VendorProfile.objects.get(pk=pk)
    serializer = VendorVerificationSerializer(vendor, data=request.data)
    if serializer.is_valid():
        serializer.save(verified_by=request.user)
        return Response(serializer.data)
    return Response(serializer.errors, status=400)
```

**Features:**
- Decorators for permissions
- Custom business logic
- Transaction management
- Error handling

### 4. Permissions Layer

```python
class IsVendor(permissions.BasePermission):
    """Allow access only to vendors"""
    def has_permission(self, request, view):
        return request.user.role == 'vendor'

class IsVendorOwner(permissions.BasePermission):
    """Allow access only to the vendor who owns the resource"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
```

**Features:**
- Custom permission classes
- Object-level permissions
- Role-based access
- Reusable across views

---

## 🔐 Security Features

### 1. Authentication
- **JWT Tokens** - Stateless authentication
- **Refresh Tokens** - Long-lived sessions
- **Token Blacklisting** - Logout functionality

### 2. Authorization
- **Role-Based Access Control (RBAC)**
- **Object-Level Permissions**
- **Custom Permission Classes**

### 3. Data Protection
- **Input Validation** - Serializer validation
- **SQL Injection Prevention** - ORM usage
- **XSS Protection** - Django templates
- **CSRF Protection** - Built-in middleware

### 4. File Upload Security
- **File Type Validation**
- **File Size Limits**
- **Secure File Storage**
- **Virus Scanning (ready)**

---

## 📊 Database Design

### Relationships
```
User (1) -----> (1) VendorProfile
VendorProfile (1) -----> (*) Product
Product (1) -----> (*) ProductImage
Product (1) -----> (*) ProductVariation
Product (*) -----> (1) Category
Order (1) -----> (*) OrderItem
OrderItem (*) -----> (1) Product
```

### Indexes
```python
class Meta:
    indexes = [
        models.Index(fields=['slug']),
        models.Index(fields=['-featured', '-created_at']),
        models.Index(fields=['status']),
        models.Index(fields=['vendor', 'is_active']),
    ]
```

**Benefits:**
- Fast queries
- Efficient filtering
- Optimized sorting

---

## 🚀 API Endpoints

### Authentication
```
POST   /api/auth/register/          - User registration
POST   /api/auth/login/             - User login
POST   /api/auth/logout/            - User logout
GET    /api/auth/profile/           - Get user profile
PUT    /api/auth/profile/           - Update profile
POST   /api/auth/refresh/           - Refresh token
```

### Vendors
```
GET    /api/vendors/                - List approved vendors
POST   /api/vendors/create/         - Create vendor profile
GET    /api/vendors/{id}/           - Get vendor details (public)
GET    /api/vendors/profile/        - Get own vendor profile
PUT    /api/vendors/profile/        - Update vendor profile
GET    /api/vendors/manage/         - Admin: List all vendors
POST   /api/vendors/{id}/verify/    - Admin: Verify vendor
```

### Products
```
GET    /api/products/                           - List products
POST   /api/products/create/                    - Create product
GET    /api/products/{id}/                      - Get product details
PUT    /api/products/{id}/                      - Update product
DELETE /api/products/{id}/                      - Delete product
GET    /api/products/my-products/               - Vendor: Own products
GET    /api/products/{id}/recommendations/      - Get recommendations
GET    /api/products/{id}/similar/              - Get similar products
GET    /api/products/recommendations/trending/  - Trending products
GET    /api/products/recommendations/personalized/ - Personalized
```

### Orders
```
GET    /api/orders/                 - List orders
POST   /api/orders/create/          - Create order
GET    /api/orders/{id}/            - Get order details
PUT    /api/orders/{id}/            - Update order status
```

### Categories
```
GET    /api/products/categories/    - List categories
POST   /api/products/categories/    - Admin: Create category
GET    /api/products/categories/{id}/ - Get category
PUT    /api/products/categories/{id}/ - Admin: Update category
DELETE /api/products/categories/{id}/ - Admin: Delete category
```

---

## 🎯 Best Practices Implemented

### 1. Code Organization
- ✅ Separation of concerns
- ✅ DRY principle
- ✅ Modular architecture
- ✅ Clear naming conventions

### 2. Database Optimization
- ✅ Select related / Prefetch related
- ✅ Database indexing
- ✅ Query optimization
- ✅ Pagination

### 3. API Design
- ✅ RESTful principles
- ✅ Consistent naming
- ✅ Proper HTTP methods
- ✅ Status codes
- ✅ Error handling

### 4. Security
- ✅ Authentication required
- ✅ Permission checks
- ✅ Input validation
- ✅ Secure defaults

### 5. Documentation
- ✅ Swagger/OpenAPI
- ✅ Code comments
- ✅ Docstrings
- ✅ README files

---

## 🔧 Configuration

### Environment Variables
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# Payment
STRIPE_SECRET_KEY=sk_test_xxxxx
CHAPA_SECRET_KEY=CHASECK_TEST-xxxxx

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
```

### Settings Structure
```python
# config/settings.py
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    # Local apps
    'apps.users',
    'apps.vendors',
    'apps.products',
    'apps.orders',
    'apps.payments',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

## 📈 Performance Optimization

### 1. Database Queries
```python
# Bad - N+1 queries
products = Product.objects.all()
for product in products:
    print(product.vendor.business_name)  # Extra query each time

# Good - Single query with join
products = Product.objects.select_related('vendor', 'category').all()
for product in products:
    print(product.vendor.business_name)  # No extra query
```

### 2. Caching
```python
from django.core.cache import cache

def get_featured_products():
    cached = cache.get('featured_products')
    if cached:
        return cached
    
    products = Product.objects.filter(featured=True)[:8]
    cache.set('featured_products', products, 3600)  # 1 hour
    return products
```

### 3. Pagination
```python
class ProductListView(generics.ListAPIView):
    pagination_class = PageNumberPagination
    # Returns: {count, next, previous, results}
```

---

## 🧪 Testing

### Unit Tests
```python
from django.test import TestCase
from apps.products.models import Product

class ProductModelTest(TestCase):
    def test_product_creation(self):
        product = Product.objects.create(
            name="Test Product",
            price=99.99,
            stock=10
        )
        self.assertEqual(product.name, "Test Product")
        self.assertTrue(product.is_complete())
```

### API Tests
```python
from rest_framework.test import APITestCase

class ProductAPITest(APITestCase):
    def test_list_products(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
```

---

## 🚀 Deployment

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use PostgreSQL
- [ ] Set up AWS S3 for media
- [ ] Configure email service
- [ ] Set up Redis for caching
- [ ] Configure Celery for tasks
- [ ] Set up monitoring (Sentry)
- [ ] Configure backup system
- [ ] Set up SSL certificate

### Docker Support
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application"]
```

---

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [DRF Documentation](https://www.django-rest-framework.org/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)
- [API Best Practices](https://restfulapi.net/)

---

**Built with Django 4.2 + Django REST Framework**
