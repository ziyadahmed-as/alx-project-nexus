from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariation

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    is_complete = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['vendor', 'views', 'sales_count', 'status']
    
    def get_is_complete(self, obj):
        """Check if product has all required information"""
        return obj.is_complete()
    
    def create(self, validated_data):
        """Create product and set initial status to draft"""
        validated_data['status'] = 'draft'
        product = super().create(validated_data)
        return product
    
    def update(self, instance, validated_data):
        """Update product and automatically update status based on completeness"""
        product = super().update(instance, validated_data)
        product.update_status()
        return product
