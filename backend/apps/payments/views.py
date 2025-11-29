from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.conf import settings
import stripe
import requests
from .models import Payment
from .serializers import PaymentSerializer, PaymentIntentSerializer
from apps.orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_intent(request):
    try:
        serializer = PaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = Order.objects.get(id=serializer.validated_data['order_id'])
        payment_method = serializer.validated_data['payment_method']
        
        if payment_method == 'stripe':
            # Check if Stripe is configured
            if not settings.STRIPE_SECRET_KEY:
                # For testing: create a mock payment
                payment = Payment.objects.create(
                    order=order,
                    payment_method='stripe',
                    transaction_id=f"test_stripe_{order.order_number}",
                    amount=order.total_amount,
                    currency='usd',
                    status='completed'
                )
                order.payment_status = 'completed'
                order.status = 'confirmed'
                order.save()
                return Response({
                    'success': True,
                    'message': 'Payment completed (test mode)',
                    'payment_id': payment.id
                })
            
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),
                currency='usd',
                metadata={'order_id': order.id}
            )
            
            Payment.objects.create(
                order=order,
                payment_method='stripe',
                transaction_id=intent.id,
                amount=order.total_amount,
                currency='usd'
            )
            
            return Response({'client_secret': intent.client_secret})
        
        elif payment_method == 'chapa':
            # Check if Chapa is configured
            if not settings.CHAPA_SECRET_KEY:
                # For testing: create a mock payment
                payment = Payment.objects.create(
                    order=order,
                    payment_method='chapa',
                    transaction_id=f"test_chapa_{order.order_number}",
                    amount=order.total_amount,
                    currency='ETB',
                    status='completed'
                )
                order.payment_status = 'completed'
                order.status = 'confirmed'
                order.save()
                return Response({
                    'success': True,
                    'message': 'Payment completed (test mode)',
                    'payment_id': payment.id
                })
            
            url = "https://api.chapa.co/v1/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "amount": str(order.total_amount),
                "currency": "ETB",
                "email": request.user.email,
                "first_name": request.user.first_name or "Customer",
                "last_name": request.user.last_name or "User",
                "tx_ref": f"ORDER-{order.order_number}",
                "callback_url": f"{settings.FRONTEND_URL}/payment/callback",
                "return_url": f"{settings.FRONTEND_URL}/orders"
            }
            
            response = requests.post(url, json=data, headers=headers)
            result = response.json()
            
            if result.get('status') == 'success':
                Payment.objects.create(
                    order=order,
                    payment_method='chapa',
                    transaction_id=result['data']['tx_ref'],
                    amount=order.total_amount,
                    currency='ETB'
                )
                return Response({'checkout_url': result['data']['checkout_url']})
            else:
                return Response({
                    'error': 'Chapa payment initialization failed',
                    'details': result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Invalid payment method'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Payment processing failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            payment = Payment.objects.get(transaction_id=intent['id'])
            payment.status = 'completed'
            payment.save()
            
            payment.order.payment_status = 'completed'
            payment.order.status = 'confirmed'
            payment.order.save()
        
        return Response({'status': 'success'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Payment.objects.all()
        return Payment.objects.filter(order__buyer=self.request.user)
