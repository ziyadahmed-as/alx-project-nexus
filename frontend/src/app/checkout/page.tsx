'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useCartStore } from '@/store/cartStore';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

export default function CheckoutPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { items, total, clearCart } = useCartStore();
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [formData, setFormData] = useState({
    shipping_address: '',
    shipping_city: '',
    shipping_country: 'Ethiopia',
    shipping_postal_code: '',
    payment_method: 'stripe',
  });

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (items.length === 0) {
      router.push('/cart');
      return;
    }
  }, [isAuthenticated, items]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create order
      const orderData = {
        ...formData,
        items: items.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        }))
      };

      const response = await api.post('/orders/create/', orderData);
      const order = response.data;
      
      toast.success('Order created successfully!');

      // Process payment
      if (formData.payment_method === 'stripe') {
        await processStripePayment(order.id);
      } else if (formData.payment_method === 'chapa') {
        await processChapaPayment(order.id);
      }

      clearCart();
      router.push('/orders');
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 
                      error.response?.data?.message ||
                      'Failed to place order';
      toast.error(errorMsg);
      console.error('Checkout error:', error);
    } finally {
      setLoading(false);
    }
  };

  const processStripePayment = async (orderId: number) => {
    try {
      const response = await api.post('/payments/create-intent/', {
        order_id: orderId,
        payment_method: 'stripe'
      });
      
      if (response.data.success) {
        // Test mode - payment completed
        toast.success(response.data.message || 'Payment processed successfully!');
      } else if (response.data.client_secret) {
        // Production mode - would redirect to Stripe checkout
        toast.success('Redirecting to payment...');
        // TODO: Integrate Stripe Elements here
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Payment processing failed';
      toast.error(errorMsg);
      throw error;
    }
  };

  const processChapaPayment = async (orderId: number) => {
    try {
      const response = await api.post('/payments/create-intent/', {
        order_id: orderId,
        payment_method: 'chapa'
      });
      
      if (response.data.success) {
        // Test mode - payment completed
        toast.success(response.data.message || 'Payment processed successfully!');
      } else if (response.data.checkout_url) {
        // Production mode - redirect to Chapa checkout
        toast.success('Redirecting to Chapa payment...');
        setTimeout(() => {
          window.location.href = response.data.checkout_url;
        }, 1000);
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Payment processing failed';
      toast.error(errorMsg);
      throw error;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  if (!mounted) {
    return null;
  }

  if (!isAuthenticated || items.length === 0) {
    return null;
  }

  const subtotal = total();
  const shipping = 50.00;
  const tax = subtotal * 0.05;
  const grandTotal = subtotal + shipping + tax;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">Checkout</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Checkout Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Customer Information */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Customer Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Name</label>
                  <input
                    type="text"
                    value={`${user?.first_name || ''} ${user?.last_name || ''}`}
                    disabled
                    className="w-full px-4 py-2 border rounded-lg bg-gray-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-4 py-2 border rounded-lg bg-gray-50"
                  />
                </div>
              </div>
            </div>

            {/* Shipping Information */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Shipping Information</h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Street Address *</label>
                  <textarea
                    name="shipping_address"
                    value={formData.shipping_address}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                    placeholder="Enter your full address"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">City *</label>
                    <input
                      type="text"
                      name="shipping_city"
                      value={formData.shipping_city}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                      placeholder="City"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Postal Code *</label>
                    <input
                      type="text"
                      name="shipping_postal_code"
                      value={formData.shipping_postal_code}
                      onChange={handleChange}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                      placeholder="Postal Code"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Country *</label>
                  <select
                    name="shipping_country"
                    value={formData.shipping_country}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                  >
                    <option value="Ethiopia">Ethiopia</option>
                    <option value="Kenya">Kenya</option>
                    <option value="Uganda">Uganda</option>
                    <option value="Tanzania">Tanzania</option>
                    <option value="USA">United States</option>
                    <option value="UK">United Kingdom</option>
                    <option value="Canada">Canada</option>
                  </select>
                </div>

                {/* Payment Method */}
                <div className="pt-4 border-t">
                  <h3 className="text-lg font-bold mb-4">Payment Method</h3>
                  
                  <div className="space-y-3">
                    <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="payment_method"
                        value="stripe"
                        checked={formData.payment_method === 'stripe'}
                        onChange={handleChange}
                        className="w-4 h-4"
                      />
                      <div className="ml-3 flex-1">
                        <div className="font-medium">Credit/Debit Card (Stripe)</div>
                        <div className="text-sm text-gray-600">
                          Pay securely with Visa, Mastercard, or American Express
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <img src="/visa.svg" alt="Visa" className="h-6" onError={(e) => e.currentTarget.style.display = 'none'} />
                        <img src="/mastercard.svg" alt="Mastercard" className="h-6" onError={(e) => e.currentTarget.style.display = 'none'} />
                      </div>
                    </label>

                    <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="payment_method"
                        value="chapa"
                        checked={formData.payment_method === 'chapa'}
                        onChange={handleChange}
                        className="w-4 h-4"
                      />
                      <div className="ml-3 flex-1">
                        <div className="font-medium">Chapa Payment</div>
                        <div className="text-sm text-gray-600">
                          Pay with Ethiopian Birr (ETB) - Mobile Money, Bank Transfer
                        </div>
                      </div>
                      <span className="text-green-600 font-bold">ETB</span>
                    </label>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary text-white py-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 font-bold text-lg mt-6"
                >
                  {loading ? 'Processing...' : `Place Order - $${grandTotal.toFixed(2)}`}
                </button>
              </form>
            </div>
          </div>

          {/* Order Summary */}
          <div>
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
              <h2 className="text-xl font-bold mb-4">Order Summary</h2>
              
              {/* Cart Items */}
              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                {items.map((item) => (
                  <div key={item.id} className="flex gap-3 pb-3 border-b">
                    <div className="w-16 h-16 bg-gray-100 rounded flex-shrink-0">
                      {item.image ? (
                        <img src={item.image} alt={item.name} className="w-full h-full object-cover rounded" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-400">
                          No img
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm truncate">{item.name}</h4>
                      <p className="text-xs text-gray-600">by {item.vendor}</p>
                      <p className="text-sm">Qty: {item.quantity}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">${(item.price * item.quantity).toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Price Breakdown */}
              <div className="space-y-2 mb-4 pt-4 border-t">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="font-medium">${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Shipping</span>
                  <span className="font-medium">${shipping.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tax (10%)</span>
                  <span className="font-medium">${tax.toFixed(2)}</span>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-bold">Total</span>
                  <span className="text-2xl font-bold text-primary">${grandTotal.toFixed(2)}</span>
                </div>
              </div>

              {/* Security Badge */}
              <div className="mt-6 pt-6 border-t text-center">
                <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
                  <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                  <span>Secure Checkout</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
