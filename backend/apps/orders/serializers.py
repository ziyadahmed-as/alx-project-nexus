from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['subtotal', 'vendor']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['buyer', 'order_number', 'payment_status']

class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())
    shipping_address = serializers.CharField()
    shipping_city = serializers.CharField()
    shipping_country = serializers.CharField()
    shipping_postal_code = serializers.CharField()
    payment_method = serializers.CharField()
