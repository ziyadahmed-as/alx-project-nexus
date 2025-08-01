# products/serializers.py

from rest_framework import serializers
from Users.serializers import VendorProfileSerializer, UserDetailSerializer  # Using existing serializers
from .models import Category, Product, ProductImage, ProductReview, ProductQuestion
from Users.models import Vendor  # Import Vendor model directly

# -------------------------------
# Category Serializer 
# this serializer handles the category model, including nested subcategories
# -------------------------------   
class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent_category', 'slug', 'subcategories']
        read_only_fields = ['slug']

    def get_subcategories(self, obj):
        # Nested subcategories serialization
        children = obj.subcategories.all()
        return CategorySerializer(children, many=True).data

# -------------------------------
# Product Image Serializer
# this serializer handles product images, including main image and alt text
# -------------------------------   
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_main']
        read_only_fields = ['id']

    def validate(self, attrs):
        # Additional validations if needed can go here
        return attrs

# -------------------------------
# Product Review Serializer
# this serializer handles product reviews, including user and rating
# -------------------------------
class ProductReviewSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)  # Using UserDetailSerializer from Users app

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'review', 'created_at', 'updated_at', 'is_approved']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_approved']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

# -------------------------------
# Product Question Serializer
# this serializer handles product questions, including user and answer
# -------------------------------
class ProductQuestionSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    answered_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ProductQuestion
        fields = ['id', 'user', 'question', 'answer', 'created_at', 'answered_at', 'is_public', 'is_approved']
        read_only_fields = ['id', 'user', 'created_at', 'answered_at', 'is_approved']

    def validate(self, attrs):
        # Ensure answer is provided only if question is answered
        if attrs.get('answer') and not attrs.get('is_public', True):
            # example rule: non-public answered questions maybe disallowed, adjust as needed
            pass
        return attrs

# -------------------------------
# Product Serializer
# this serializer handles the product model, including vendor, category, and nested relationships
# -------------------------------
class ProductSerializer(serializers.ModelSerializer):
    vendor = VendorProfileSerializer(read_only=True)  # Using VendorProfileSerializer for read operations
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True
    )
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    questions = ProductQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_id', 'category', 'name', 'description', 
            'price', 'discount_price', 'stock', 'sku', 'is_approved', 
            'is_active', 'created_at', 'updated_at', 'images', 'reviews', 
            'questions',
        ]
        read_only_fields = ['id', 'vendor', 'is_approved', 'created_at', 'updated_at']

    def validate(self, data):
        price = data.get('price')
        discount_price = data.get('discount_price')
        if discount_price is not None and discount_price > price:
            raise serializers.ValidationError("Discount price cannot be greater than the original price.")
        return data