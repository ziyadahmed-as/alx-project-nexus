'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import Navbar from '@/components/Navbar';
import { useAuthStore } from '@/store/authStore';

export default function Home() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newProducts, setNewProducts] = useState([]);
  const [recommendedProducts, setRecommendedProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // Redirect authenticated users to their dashboards
    if (isAuthenticated && user) {
      if (user.role === 'admin') {
        router.push('/admin/dashboard');
        return;
      } else if (user.role === 'vendor') {
        router.push('/vendor/dashboard');
        return;
      }
    }
    fetchProducts();
  }, [isAuthenticated, user]);

  const fetchProducts = async () => {
    try {
      // Fetch all products (already sorted by featured and newest)
      const response = await api.get('/products/');
      const allProducts = response.data.results || response.data;
      
      // Separate featured and new products
      const featured = allProducts.filter((p: any) => p.featured);
      const newest = allProducts.slice(0, 8); // Get first 8 (newest)
      
      setFeaturedProducts(featured.slice(0, 8));
      setNewProducts(newest);

      // Fetch personalized recommendations
      try {
        const recResponse = await api.get('/products/recommendations/personalized/');
        setRecommendedProducts(recResponse.data.slice(0, 8));
      } catch (error) {
        console.log('Could not fetch recommendations');
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <section className="mb-12 text-center">
          <h1 className="text-4xl font-bold mb-4">Welcome to Multivendor Marketplace</h1>
          <p className="text-gray-600 mb-6">Shop from thousands of vendors worldwide</p>
          <Link href="/products" className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 inline-block">
            Browse Products
          </Link>
        </section>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading products...</p>
          </div>
        ) : (
          <>
            {/* Featured Products Section */}
            {featuredProducts.length > 0 && (
              <section className="mb-12">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <svg className="w-8 h-8 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                    <h2 className="text-3xl font-bold">Featured Products</h2>
                  </div>
                  <Link href="/products?featured=true" className="text-primary hover:underline font-medium">
                    View All →
                  </Link>
                </div>
                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg p-6 mb-4">
                  <p className="text-gray-700">
                    ⭐ Handpicked products from our top vendors - Quality guaranteed!
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {featuredProducts.map((product: any) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </section>
            )}

            {/* New Products Section */}
            <section className="mb-12">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                  </svg>
                  <h2 className="text-3xl font-bold">New Arrivals</h2>
                </div>
                <Link href="/products" className="text-primary hover:underline font-medium">
                  View All →
                </Link>
              </div>
              <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 mb-4">
                <p className="text-gray-700">
                  🆕 Fresh products just added - Be the first to discover them!
                </p>
              </div>
              {newProducts.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {newProducts.map((product: any) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  <p className="text-gray-600">No products available yet</p>
                </div>
              )}
            </section>

            {/* Recommended for You Section */}
            {recommendedProducts.length > 0 && (
              <section className="mb-12">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <h2 className="text-3xl font-bold">Recommended for You</h2>
                  </div>
                  <Link href="/products" className="text-primary hover:underline font-medium">
                    View All →
                  </Link>
                </div>
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6 mb-4">
                  <p className="text-gray-700">
                    💡 Personalized picks based on your browsing and shopping history
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {recommendedProducts.map((product: any) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </section>
            )}

            {/* Categories Section */}
            <section className="mb-12">
              <h2 className="text-3xl font-bold mb-6">Shop by Category</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href="/products?category=electronics" className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center">
                  <div className="text-4xl mb-2">📱</div>
                  <h3 className="font-semibold">Electronics</h3>
                </Link>
                <Link href="/products?category=fashion" className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center">
                  <div className="text-4xl mb-2">👕</div>
                  <h3 className="font-semibold">Fashion</h3>
                </Link>
                <Link href="/products?category=home-garden" className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center">
                  <div className="text-4xl mb-2">🏠</div>
                  <h3 className="font-semibold">Home & Garden</h3>
                </Link>
                <Link href="/products?category=sports" className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center">
                  <div className="text-4xl mb-2">⚽</div>
                  <h3 className="font-semibold">Sports</h3>
                </Link>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
