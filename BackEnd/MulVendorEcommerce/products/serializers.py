from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    Category, Product, ProductImage, 
    ProductVariant, ProductReview, ProductQuestion
)
from Users.models import User
from django.utils import timezone

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model with hierarchical support"""
    subcategories = serializers.SerializerMethodField()
    parent_category_name = serializers.CharField(
        source='parent_category.name', 
        read_only=True
    )

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 
            'parent_category', 'parent_category_name',
            'image', 'is_active', 'subcategories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        extra_kwargs = {
            'parent_category': {'required': False}
        }

    def get_subcategories(self, obj):
        """Recursively get subcategories"""
        subcategories = obj.subcategories.filter(is_active=True)
        return CategorySerializer(subcategories, many=True).data

    def validate_parent_category(self, value):
        """Prevent circular references in category hierarchy"""
        if value and value.id == self.instance.id if self.instance else None:
            raise serializers.ValidationError(
                _("Category cannot be its own parent")
            )
        return value

class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model with permission checks"""
    uploaded_by_email = serializers.EmailField(
        source='uploaded_by.email', 
        read_only=True
    )

    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'alt_text',
            'is_primary', 'order', 'uploaded_by',
            'uploaded_by_email', 'created_at'
        ]
        read_only_fields = [
            'id', 'uploaded_by', 'uploaded_by_email', 'created_at'
        ]

    def validate(self, data):
        """Validate image upload permissions"""
        request = self.context.get('request')
        product = data.get('product') or self.instance.product if self.instance else None
        
        if request and product:
            if not ProductImage.can_add_image(request.user, product):
                raise serializers.ValidationError(
                    _("You don't have permission to add images to this product")
                )
        return data

    def create(self, validated_data):
        """Set uploaded_by to current user"""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)

class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant model with permission checks"""
    created_by_email = serializers.EmailField(
        source='created_by.email', 
        read_only=True
    )
    updated_by_email = serializers.EmailField(
        source='updated_by.email', 
        read_only=True
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'name', 'sku',
            'price', 'quantity', 'created_by',
            'created_by_email', 'updated_by',
            'updated_by_email', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_by_email',
            'updated_by', 'updated_by_email',
            'created_at', 'updated_at'
        ]

    def validate(self, data):
        """Validate variant management permissions"""
        request = self.context.get('request')
        product = data.get('product') or self.instance.product if self.instance else None
        
        if request and product:
            if not ProductVariant.can_manage_variant(request.user, product):
                raise serializers.ValidationError(
                    _("You don't have permission to manage variants for this product")
                )
        return data

    def create(self, validated_data):
        """Set created_by to current user"""
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Set updated_by to current user"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview model with permission checks"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    vendor_response = serializers.CharField(
        required=False, 
        allow_blank=True,
        allow_null=True
    )
    can_approve = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'user', 'user_email',
            'rating', 'title', 'comment', 'vendor_response',
            'is_approved', 'can_approve', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'created_at',
            'updated_at', 'can_approve'
        ]

    def get_can_approve(self, obj):
        """Check if current user can approve this review"""
        request = self.context.get('request')
        return (request and 
                ProductReview.can_approve_review(request.user, obj.product))

    def validate(self, data):
        """Validate review permissions and content"""
        request = self.context.get('request')
        
        # On create, check if user can create reviews
        if not self.instance and request:
            if request.user.is_anonymous:
                raise serializers.ValidationError(
                    _("You must be logged in to submit a review")
                )
            
        # On update, check if user can modify the review
        if self.instance and request:
            if (self.instance.user != request.user and 
                not self.get_can_approve(self.instance)):
                raise serializers.ValidationError(
                    _("You can only edit your own reviews")
                )
            
            # Only allow vendor/admin to update is_approved and vendor_response
            if not self.get_can_approve(self.instance):
                if 'is_approved' in data or 'vendor_response' in data:
                    raise serializers.ValidationError(
                        _("You don't have permission to approve reviews or add vendor responses")
                    )
        
        return data

    def create(self, validated_data):
        """Set user to current user and default is_approved"""
        validated_data['user'] = self.context['request'].user
        validated_data['is_approved'] = False  # Reviews need approval by default
        return super().create(validated_data)

class ProductQuestionSerializer(serializers.ModelSerializer):
    """Serializer for ProductQuestion model with permission checks"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    answered_by_email = serializers.EmailField(
        source='answered_by.email', 
        read_only=True
    )
    can_answer = serializers.SerializerMethodField()

    class Meta:
        model = ProductQuestion
        fields = [
            'id', 'product', 'user', 'user_email',
            'question', 'answer', 'answered_by',
            'answered_by_email', 'is_approved',
            'can_answer', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'created_at',
            'updated_at', 'can_answer'
        ]

    def get_can_answer(self, obj):
        """Check if current user can answer this question"""
        request = self.context.get('request')
        return (request and 
                ProductQuestion.can_answer_question(request.user, obj.product))

    def validate(self, data):
        """Validate question permissions and content"""
        request = self.context.get('request')
        
        # On create, check if user can create questions
        if not self.instance and request:
            if request.user.is_anonymous:
                raise serializers.ValidationError(
                    _("You must be logged in to ask a question")
                )
            
        # On update, check if user can modify the question
        if self.instance and request:
            # Only allow vendor/admin to update answer, answered_by, is_approved
            if not self.get_can_answer(self.instance):
                if any(field in data for field in ['answer', 'answered_by', 'is_approved']):
                    raise serializers.ValidationError(
                        _("You don't have permission to answer questions")
                    )
            
            # Set answered_by to current user if answering
            if 'answer' in data and data['answer'] and not data.get('answered_by'):
                data['answered_by'] = request.user
        
        return data

    def create(self, validated_data):
        """Set user to current user and default is_approved"""
        validated_data['user'] = self.context['request'].user
        validated_data['is_approved'] = False  # Questions need approval by default
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    """Main Product serializer with nested relationships"""
    vendor_name = serializers.CharField(
        source='vendor.user.business_name', 
        read_only=True
    )
    category_name = serializers.CharField(
        source='category.name', 
        read_only=True
    )
    created_by_email = serializers.EmailField(
        source='created_by.email', 
        read_only=True
    )
    updated_by_email = serializers.EmailField(
        source='updated_by.email', 
        read_only=True
    )
    discount_percentage = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    # Nested serializers
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    questions = ProductQuestionSerializer(many=True, read_only=True)
    
    # Permission fields
    can_edit = serializers.SerializerMethodField()
    can_change_status = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_name', 'category',
            'category_name', 'name', 'slug', 'description',
            'short_description', 'sku', 'price', 'compare_at_price',
            'cost_per_item', 'condition', 'status', 'quantity',
            'weight', 'is_active', 'is_featured', 'is_digital',
            'rating', 'view_count', 'discount_percentage',
            'is_available', 'created_by', 'created_by_email',
            'updated_by', 'updated_by_email', 'created_at',
            'updated_at', 'images', 'variants', 'reviews',
            'questions', 'can_edit', 'can_change_status',
            'can_delete'
        ]
        read_only_fields = [
            'id', 'slug', 'vendor_name', 'category_name',
            'rating', 'view_count', 'discount_percentage',
            'is_available', 'created_by', 'created_by_email',
            'updated_by', 'updated_by_email', 'created_at',
            'updated_at', 'images', 'variants', 'reviews',
            'questions', 'can_edit', 'can_change_status',
            'can_delete'
        ]
        extra_kwargs = {
            'vendor': {'required': False}
        }

    def get_discount_percentage(self, obj):
        return obj.discount_percentage

    def get_is_available(self, obj):
        return obj.is_available

    def get_can_edit(self, obj):
        request = self.context.get('request')
        return (request and 
                Product.can_edit_product(request.user, obj))

    def get_can_change_status(self, obj):
        request = self.context.get('request')
        return (request and 
                Product.can_change_status(request.user, obj))

    def get_can_delete(self, obj):
        request = self.context.get('request')
        return (request and 
                Product.can_delete_product(request.user, obj))

    def validate(self, data):
        """Validate product data and permissions"""
        request = self.context.get('request')
        instance = self.instance
        
        # On create, check if user can create products
        if not instance and request:
            if not Product.can_create_product(request.user):
                raise serializers.ValidationError(
                    _("You don't have permission to create products")
                )
            
            # Set vendor automatically for vendor users
            if hasattr(request.user, 'vendor'):
                data['vendor'] = request.user.vendor
            elif hasattr(request.user, 'vendor_employee'):
                data['vendor'] = request.user.vendor_employee.vendor
            else:
                raise serializers.ValidationError(
                    _("Only vendors and their employees can create products")
                )
        
        # On update, check if user can edit the product
        if instance and request:
            if not Product.can_edit_product(request.user, instance):
                raise serializers.ValidationError(
                    _("You don't have permission to edit this product")
                )
            
            # Only allow status change if user has permission
            if 'status' in data and not Product.can_change_status(request.user, instance):
                raise serializers.ValidationError(
                    _("You don't have permission to change product status")
                )
        
        return data

    def create(self, validated_data):
        """Set created_by and updated_by to current user"""
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Set updated_by to current user"""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings"""
    vendor_name = serializers.CharField(
        source='vendor.user.business_name', 
        read_only=True
    )
    category_name = serializers.CharField(
        source='category.name', 
        read_only=True
    )
    discount_percentage = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description',
            'price', 'compare_at_price', 'discount_percentage',
            'is_available', 'rating', 'vendor_name',
            'category_name', 'primary_image'
        ]
        read_only_fields = fields

    def get_discount_percentage(self, obj):
        return obj.discount_percentage

    def get_is_available(self, obj):
        return obj.is_available

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

class ProductAdminSerializer(ProductSerializer):
    """Extended serializer for admin users with additional fields"""
    class Meta(ProductSerializer.Meta):
        read_only_fields = [
            field for field in ProductSerializer.Meta.read_only_fields 
            if field not in ['status', 'is_active', 'is_featured']
        ]
        fields = ProductSerializer.Meta.fields + [
            'status', 'is_active', 'is_featured'
        ]   