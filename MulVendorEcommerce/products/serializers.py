from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview, ProductVariant, VendorProductRelation
from vendors.models import VendorDashboard
from users.serializers import VendorSerializer, UserSerializer
from django.utils.text import slugify

class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'is_active']
        read_only_fields = ['id', 'slug']
        extra_kwargs = {
            'name': {'required': True}
        }

    def validate(self, data):
        if data.get('parent') and data['parent'] == self.instance:
            raise serializers.ValidationError("A category cannot be its own parent")
        return data

    def create(self, validated_data):
        if 'slug' not in validated_data:
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

class RecursiveCategorySerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

class CategoryTreeSerializer(CategorySerializer):
    children = RecursiveCategorySerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['children']

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'is_main', 'order']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'value', 'price_modifier', 'sku', 'stock', 'is_active']
        read_only_fields = ['id']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'title', 'review', 'is_approved', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

class ProductSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    current_price = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'category', 'name', 'slug', 'description', 'specifications',
            'price', 'discount_price', 'current_price', 'cost_price', 'stock', 'sku', 'upc',
            'status', 'is_featured', 'is_active', 'created_at', 'updated_at', 'published_at',
            'images', 'variants', 'reviews', 'main_image', 'in_stock'
        ]
        read_only_fields = [
            'id', 'slug', 'current_price', 'created_at', 'updated_at', 'published_at',
            'vendor', 'in_stock'
        ]

    def get_current_price(self, obj):
        return obj.discount_price if obj.discount_price else obj.price

    def get_main_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            serializer = ProductImageSerializer(main_image, context=self.context)
            return serializer.data
        return None

    def get_in_stock(self, obj):
        return obj.stock > 0

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'name', 'description', 'specifications',
            'price', 'discount_price', 'cost_price', 'stock', 'sku', 'upc',
            'status', 'is_featured', 'is_active', 'images'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        if data.get('discount_price') and data.get('price'):
            if data['discount_price'] >= data['price']:
                raise serializers.ValidationError("Discount price must be lower than regular price")
        return data

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        product = Product.objects.create(
            vendor=self.context['request'].user.vendor,
            **validated_data
        )
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        return product

class VendorProductRelationSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = VendorProductRelation
        fields = ['id', 'vendor', 'product', 'is_primary', 'commission_rate', 'created_at']
        read_only_fields = ['id', 'created_at']