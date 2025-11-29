from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from apps.products.models import Product
import uuid

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'vendor':
            return Order.objects.filter(items__vendor=user.vendor_profile).distinct()
        return Order.objects.filter(buyer=user)

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from rest_framework import serializers as drf_serializers
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_data = serializer.validated_data
        total = 0
        
        # Check if user is a vendor trying to order their own products
        if request.user.role == 'vendor':
            try:
                vendor_profile = request.user.vendor_profile
                for item_data in order_data['items']:
                    product = Product.objects.get(id=item_data['product_id'])
                    if product.vendor == vendor_profile:
                        raise drf_serializers.ValidationError({
                            'detail': f'You cannot purchase your own product: {product.name}'
                        })
            except Exception as e:
                if 'cannot purchase your own product' in str(e):
                    raise
        
        order = Order.objects.create(
            buyer=request.user,
            order_number=f"ORD-{uuid.uuid4().hex[:10].upper()}",
            shipping_address=order_data['shipping_address'],
            shipping_city=order_data['shipping_city'],
            shipping_country=order_data['shipping_country'],
            shipping_postal_code=order_data['shipping_postal_code'],
            payment_method=order_data['payment_method'],
            total_amount=0
        )
        
        for item_data in order_data['items']:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = item_data['quantity']
            
            if product.stock < quantity:
                from rest_framework import serializers as drf_serializers
                raise drf_serializers.ValidationError(f"Insufficient stock for {product.name}")
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                vendor=product.vendor,
                quantity=quantity,
                price=product.price
            )
            
            product.stock -= quantity
            product.sales_count += quantity
            product.save()
            
            total += order_item.subtotal
        
        order.total_amount = total
        order.save()
        
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
