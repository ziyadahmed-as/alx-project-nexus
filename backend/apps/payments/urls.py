from django.urls import path
from .views import create_payment_intent, stripe_webhook, PaymentListView

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('create-intent/', create_payment_intent, name='create-payment-intent'),
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),
]
