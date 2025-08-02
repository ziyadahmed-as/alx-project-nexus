from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, ProductReview, ProductQuestion
from Users.serializers import VendorProfileSerializer, UserSerializer
from Users.models import VendorProfile
import uuid

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    parent_category_name = serializers.CharField(source='parent_category.name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 
            'parent_category', 'parent_category_name',
            'image', 'image_url', 'is_active',
            'created_at', 'updated_at', 'subcategories'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'image_url']
        extra_kwargs = {
            'parent_category': {'write_only': True}
        }

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data
        return None

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            'id', 'image', 'image_url', 'alt_text',
            'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def validate(self, data):
        if data.get('is_primary'):
            ProductImage.objects.filter(
                product_id=self.context.get('product_id')
            ).update(is_primary=False)
        return data

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price',
            'quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = ProductReview
        fields = [
            'id', 'product_id', 'user', 'rating',
            'title', 'comment', 'vendor_response',
            'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'vendor_response',
            'is_approved', 'created_at', 'updated_at'
        ]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

class ProductQuestionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    answered_by = UserSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = ProductQuestion
        fields = [
            'id', 'product_id', 'user', 'question',
            'answer', 'answered_by', 'is_approved',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'answered_by', 'is_approved',
            'created_at', 'updated_at'
        ]

class ProductSerializer(serializers.ModelSerializer):
    vendor = VendorProfileSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=VendorProfile.objects.all(),
        source='vendor',
        write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    questions = ProductQuestionSerializer(many=True, read_only=True)
    
    discount_percentage = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_id', 'category', 'category_id',
            'name', 'slug', 'description', 'short_description',
            'sku', 'price', 'compare_at_price', 'cost_per_item',
            'condition', 'condition_display', 'status', 'status_display',
            'quantity', 'weight', 'is_active', 'is_featured',
            'is_digital', 'rating', 'view_count', 'created_at',
            'updated_at', 'images', 'variants', 'reviews',
            'questions', 'discount_percentage', 'is_available'
        ]
        read_only_fields = [
            'id', 'slug', 'rating', 'view_count',
            'created_at', 'updated_at', 'condition_display',
            'status_display'
        ]

    def get_discount_percentage(self, obj):
        return obj.discount_percentage

    def get_is_available(self, obj):
        return obj.is_available

    def validate(self, data):
        if data.get('compare_at_price') and data['compare_at_price'] <= data.get('price', 0):
            raise serializers.ValidationError(
                "Compare at price must be greater than current price"
            )
        
        if data.get('quantity') and data['quantity'] < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
            
        return data

    def create(self, validated_data):
        product = super().create(validated_data)
        request = self.context.get('request')
        
        if request and 'images' in request.FILES:
            for image_file in request.FILES.getlist('images'):
                ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    alt_text=f"Image for {product.name}"
                )
                
        return product