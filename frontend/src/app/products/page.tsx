'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import ProductCard from '@/components/ProductCard';
import Navbar from '@/components/Navbar';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('newest');
  const [showFilters, setShowFilters] = useState(false);
  const searchParams = useSearchParams();
  const router = useRouter();
  
  // Filter states
  const [filters, setFilters] = useState({
    minPrice: '',
    maxPrice: '',
    location: '',
    category: '',
    dateFrom: '',
    dateTo: '',
    search: ''
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [sortBy, searchParams]);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/products/categories/');
      setCategories(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      let url = '/products/';
      const params = new URLSearchParams();
      
      // Add filters from URL
      const featured = searchParams.get('featured');
      const urlCategory = searchParams.get('category');
      
      if (featured) params.append('featured', featured);
      if (urlCategory) params.append('category', urlCategory);
      
      // Add custom filters
      if (filters.category) params.append('category', filters.category);
      if (filters.search) params.append('search', filters.search);
      if (filters.minPrice) params.append('min_price', filters.minPrice);
      if (filters.maxPrice) params.append('max_price', filters.maxPrice);
      if (filters.location) params.append('location', filters.location);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      
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
      let productsData = response.data.results || response.data;
      
      // Client-side filtering for price range (if backend doesn't support it)
      if (filters.minPrice || filters.maxPrice) {
        productsData = productsData.filter((p: any) => {
          const price = parseFloat(p.price);
          const min = filters.minPrice ? parseFloat(filters.minPrice) : 0;
          const max = filters.maxPrice ? parseFloat(filters.maxPrice) : Infinity;
          return price >= min && price <= max;
        });
      }
      
      // Client-side filtering for date range
      if (filters.dateFrom || filters.dateTo) {
        productsData = productsData.filter((p: any) => {
          const productDate = new Date(p.created_at);
          const fromDate = filters.dateFrom ? new Date(filters.dateFrom) : new Date(0);
          const toDate = filters.dateTo ? new Date(filters.dateTo) : new Date();
          return productDate >= fromDate && productDate <= toDate;
        });
      }
      
      setProducts(productsData);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    fetchProducts();
    setShowFilters(false);
  };

  const clearFilters = () => {
    setFilters({
      minPrice: '',
      maxPrice: '',
      location: '',
      category: '',
      dateFrom: '',
      dateTo: '',
      search: ''
    });
    fetchProducts();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header with Search and Sort */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">All Products</h1>
            <p className="text-gray-600">
              {loading ? 'Loading...' : `${products.length} products found`}
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
            {/* Search Bar */}
            <div className="relative flex-1 md:w-64">
              <input
                type="text"
                placeholder="Search products..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && applyFilters()}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
              />
              <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
            {/* Filter Button */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2 justify-center"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filters
              {(filters.minPrice || filters.maxPrice || filters.location || filters.category || filters.dateFrom || filters.dateTo) && (
                <span className="bg-primary text-white text-xs px-2 py-0.5 rounded-full">Active</span>
              )}
            </button>
            
            {/* Sort Dropdown */}
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

        {/* Advanced Filters Panel */}
        {showFilters && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Advanced Filters</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Price Range */}
              <div>
                <label className="block text-sm font-medium mb-2">Price Range</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={filters.minPrice}
                    onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={filters.maxPrice}
                    onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Categories</option>
                  {categories.map((cat: any) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              {/* Location */}
              <div>
                <label className="block text-sm font-medium mb-2">Vendor Location</label>
                <input
                  type="text"
                  placeholder="City or Country"
                  value={filters.location}
                  onChange={(e) => handleFilterChange('location', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium mb-2">Published Date</label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={filters.dateFrom}
                    onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary text-sm"
                  />
                  <input
                    type="date"
                    value={filters.dateTo}
                    onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Filter Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={applyFilters}
                className="flex-1 bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 font-medium"
              >
                Apply Filters
              </button>
              <button
                onClick={clearFilters}
                className="px-6 py-2 border rounded-lg hover:bg-gray-50"
              >
                Clear All
              </button>
            </div>
          </div>
        )}

        {/* Quick Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSortBy('featured')}
              className={`px-4 py-2 rounded-lg transition ${
                sortBy === 'featured'
                  ? 'bg-yellow-100 text-yellow-800 font-semibold'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              ⭐ Featured
            </button>
            <button
              onClick={() => setSortBy('newest')}
              className={`px-4 py-2 rounded-lg transition ${
                sortBy === 'newest'
                  ? 'bg-green-100 text-green-800 font-semibold'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              🆕 New Arrivals
            </button>
            <button
              onClick={() => setSortBy('popular')}
              className={`px-4 py-2 rounded-lg transition ${
                sortBy === 'popular'
                  ? 'bg-blue-100 text-blue-800 font-semibold'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              🔥 Popular
            </button>
            
            {/* Active Filters Display */}
            {filters.minPrice && (
              <span className="px-3 py-2 bg-purple-100 text-purple-800 rounded-lg text-sm flex items-center gap-2">
                Min: ${filters.minPrice}
                <button onClick={() => handleFilterChange('minPrice', '')} className="hover:text-purple-900">×</button>
              </span>
            )}
            {filters.maxPrice && (
              <span className="px-3 py-2 bg-purple-100 text-purple-800 rounded-lg text-sm flex items-center gap-2">
                Max: ${filters.maxPrice}
                <button onClick={() => handleFilterChange('maxPrice', '')} className="hover:text-purple-900">×</button>
              </span>
            )}
            {filters.location && (
              <span className="px-3 py-2 bg-blue-100 text-blue-800 rounded-lg text-sm flex items-center gap-2">
                📍 {filters.location}
                <button onClick={() => handleFilterChange('location', '')} className="hover:text-blue-900">×</button>
              </span>
            )}
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
