'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import Navbar from '@/components/Navbar';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('newest');
  const searchParams = useSearchParams();

  useEffect(() => {
    fetchProducts();
  }, [sortBy, searchParams]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      let url = '/products/';
      const params = new URLSearchParams();
      
      // Add filters from URL
      const featured = searchParams.get('featured');
      const category = searchParams.get('category');
      
      if (featured) params.append('featured', featured);
      if (category) params.append('category', category);
      
      // Add sorting
      switch (sortBy) {
        case 'newest':
          params.append('ordering', '-created_at');
          break;
        case 'price-low':
          params.append('ordering', 'price');
          break;
        case 'price-high':
          params.append('ordering', '-price');
          break;
        case 'popular':
          params.append('ordering', '-sales_count');
          break;
        case 'featured':
          params.append('ordering', '-featured,-created_at');
          break;
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await api.get(url);
      setProducts(response.data.results || response.data);
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
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">All Products</h1>
            <p className="text-gray-600">
              {loading ? 'Loading...' : `${products.length} products found`}
            </p>
          </div>
          
          {/* Sort Dropdown */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary bg-white"
            >
              <option value="featured">Featured First</option>
              <option value="newest">Newest First</option>
              <option value="popular">Most Popular</option>
              <option value="price-low">Price: Low to High</option>
              <option value="price-high">Price: High to Low</option>
            </select>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSortBy('featured')}
              className={`px-4 py-2 rounded-lg ${
                sortBy === 'featured'
                  ? 'bg-yellow-100 text-yellow-800 font-semibold'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              ⭐ Featured
            </button>
            <button
              onClick={() => setSortBy('newest')}
              className={`px-4 py-2 rounded-lg ${
                sortBy === 'newest'
                  ? 'bg-green-100 text-green-800 font-semibold'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              🆕 New Arrivals
            </button>
            <button
              onClick={() => setSortBy('popular')}
              className={`px-4 py-2 rounded-lg ${
                sortBy === 'popular'
                  ? 'bg-blue-100 text-blue-800 font-semibold'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              🔥 Popular
            </button>
          </div>
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading products...</p>
          </div>
        ) : products.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map((product: any) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p className="text-gray-600 mb-4">No products found</p>
          </div>
        )}
      </main>
    </div>
  );
}
