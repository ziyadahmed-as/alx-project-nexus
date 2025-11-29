'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

export default function VendorDashboard() {
  const { user, isAuthenticated } = useAuthStore();
  const [products, setProducts] = useState([]);
  const [activeTab, setActiveTab] = useState<'published' | 'draft'>('published');
  const [stats, setStats] = useState({ 
    total_products: 0, 
    published_products: 0,
    draft_products: 0,
    total_orders: 0, 
    total_sales: 0 
  });
  const [needsSetup, setNeedsSetup] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (user?.role !== 'vendor') {
      router.push('/');
      return;
    }
    fetchDashboardData();
  }, [isAuthenticated, user]);

  const fetchDashboardData = async () => {
    try {
      const productsRes = await api.get('/products/my-products/');
      const productData = productsRes.data.results || productsRes.data;
      setProducts(productData);
      
      // Calculate stats
      const productArray = Array.isArray(productData) ? productData : [];
      const published = productArray.filter((p: any) => p.status === 'published').length;
      const draft = productArray.filter((p: any) => p.status === 'draft').length;
      
      setStats({
        total_products: productArray.length,
        published_products: published,
        draft_products: draft,
        total_orders: 0,
        total_sales: 0
      });
    } catch (error: any) {
      console.error('Error fetching dashboard data:', error);
      // If vendor profile doesn't exist, show setup prompt
      if (error.response?.status === 500 || error.response?.status === 404) {
        setNeedsSetup(true);
      }
    }
  };

  const handleDeleteProduct = async (productId: number) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
      await api.delete(`/products/${productId}/`);
      toast.success('Product deleted successfully');
      fetchDashboardData();
    } catch (error) {
      toast.error('Failed to delete product');
    }
  };

  if (needsSetup) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="mb-6">
                <svg className="w-24 h-24 mx-auto text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h1 className="text-3xl font-bold mb-4">Welcome, Vendor!</h1>
              <p className="text-gray-600 mb-6">
                To start selling on our platform, you need to complete your vendor profile setup.
                This includes your business information, office address, and verification documents.
              </p>
              <button
                onClick={() => router.push('/vendor/setup')}
                className="bg-primary text-white px-8 py-3 rounded-lg hover:bg-blue-600 font-medium text-lg"
              >
                Complete Vendor Setup
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-lg min-h-screen">
          <div className="p-6">
            <h2 className="text-xl font-bold mb-6">Vendor Panel</h2>
            <nav className="space-y-2">
              <button
                onClick={() => router.push('/vendor/dashboard')}
                className="w-full text-left px-4 py-3 bg-blue-50 text-primary rounded-lg font-medium flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                Dashboard
              </button>
              <button
                onClick={() => router.push('/vendor/products/new')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Product
              </button>
              <button
                onClick={() => router.push('/orders')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
                Orders
              </button>
              <button
                onClick={() => router.push('/profile')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Profile
              </button>
              <button
                onClick={() => router.push('/vendor/setup')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Documents
              </button>
            </nav>
          </div>
        </aside>

        {/* Main Content with proper margins */}
        <main className="flex-1 p-6 md:p-8 lg:p-10">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">Vendor Dashboard</h1>
          
          {/* Documentation Alert */}
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-2">Vendor Documentation</h3>
                <p className="text-gray-700 mb-4">
                  Keep your business documents up to date. Submit or update your verification documents, business license, tax certificates, and other required documentation.
                </p>
                <button
                  onClick={() => router.push('/vendor/setup')}
                  className="bg-yellow-600 text-white px-6 py-2.5 rounded-lg hover:bg-yellow-700 font-medium flex items-center gap-2 shadow-sm"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Submit/Update Documents
                </button>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-600 mb-2">Total Products</h3>
            <p className="text-3xl font-bold">{stats.total_products}</p>
          </div>
          
          <div className="bg-green-50 p-6 rounded-lg shadow border border-green-200">
            <h3 className="text-green-700 mb-2 font-medium">Published</h3>
            <p className="text-3xl font-bold text-green-600">{stats.published_products}</p>
          </div>
          
          <div className="bg-yellow-50 p-6 rounded-lg shadow border border-yellow-200">
            <h3 className="text-yellow-700 mb-2 font-medium">Drafts</h3>
            <p className="text-3xl font-bold text-yellow-600">{stats.draft_products}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-600 mb-2">Total Sales</h3>
            <p className="text-3xl font-bold">${stats.total_sales}</p>
          </div>
        </div>
        
        {/* Quick Share Section */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-bold mb-2">Share Your Store</h2>
          <p className="text-gray-600 mb-4 text-sm">Share your products on social media to reach more customers!</p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => window.open(`https://facebook.com/sharer/sharer.php?u=${window.location.origin}/vendors/${user?.id}`, '_blank')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
              Share on Facebook
            </button>
            <button
              onClick={() => window.open(`https://twitter.com/intent/tweet?text=Check out my store!&url=${window.location.origin}/vendors/${user?.id}`, '_blank')}
              className="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
              Share on X
            </button>
            <button
              onClick={() => window.open(`https://t.me/share/url?url=${window.location.origin}/vendors/${user?.id}&text=Check out my store!`, '_blank')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
              </svg>
              Share on Telegram
            </button>
          </div>
        </div>
        
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">My Products</h2>
              <button
                onClick={() => router.push('/vendor/products/new')}
                className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 font-medium flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add New Product
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 mb-6 border-b">
              <button
                onClick={() => setActiveTab('published')}
                className={`pb-3 px-4 font-medium transition-colors ${
                  activeTab === 'published'
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Published ({stats.published_products})
              </button>
              <button
                onClick={() => setActiveTab('draft')}
                className={`pb-3 px-4 font-medium transition-colors ${
                  activeTab === 'draft'
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Drafts ({stats.draft_products})
              </button>
            </div>

            {/* Draft Info Banner */}
            {activeTab === 'draft' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm">
                    <p className="font-medium text-yellow-900 mb-1">Draft Products</p>
                    <p className="text-yellow-800">
                      These products are incomplete and not visible to customers. To publish, ensure each product has:
                      a category, at least one image, and all required information filled out.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {products.filter((p: any) => p.status === activeTab).length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-24 h-24 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <p className="text-gray-600 mb-4">
                  {activeTab === 'published' ? 'No published products yet' : 'No draft products'}
                </p>
                <button
                  onClick={() => router.push('/vendor/products/new')}
                  className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600"
                >
                  Add Your First Product
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left py-3 px-4 font-semibold">Product</th>
                      <th className="text-left py-3 px-4 font-semibold">Price</th>
                      <th className="text-left py-3 px-4 font-semibold">Stock</th>
                      <th className="text-left py-3 px-4 font-semibold">Sales</th>
                      <th className="text-left py-3 px-4 font-semibold">Status</th>
                      {activeTab === 'draft' && <th className="text-left py-3 px-4 font-semibold">Missing</th>}
                      <th className="text-center py-3 px-4 font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.filter((p: any) => p.status === activeTab).map((product: any) => (
                      <tr key={product.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="font-medium">{product.name}</div>
                          <div className="text-sm text-gray-600">SKU: {product.sku}</div>
                        </td>
                        <td className="py-3 px-4 font-semibold">${parseFloat(product.price).toFixed(2)}</td>
                        <td className="py-3 px-4">
                          <span className={`${product.stock > 10 ? 'text-green-600' : product.stock > 0 ? 'text-yellow-600' : 'text-red-600'} font-medium`}>
                            {product.stock}
                          </span>
                        </td>
                        <td className="py-3 px-4">{product.sales_count || 0}</td>
                        <td className="py-3 px-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            product.status === 'published' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {product.status === 'published' ? 'Published' : 'Draft'}
                          </span>
                        </td>
                        {activeTab === 'draft' && (
                          <td className="py-3 px-4">
                            <div className="text-xs text-gray-600">
                              {!product.category && <div>• Category</div>}
                              {(!product.images || product.images.length === 0) && <div>• Images</div>}
                              {!product.is_complete && <div>• Info</div>}
                            </div>
                          </td>
                        )}
                        <td className="py-3 px-4">
                          <div className="flex justify-center gap-2">
                            <button 
                              onClick={() => router.push(`/products/${product.id}`)}
                              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                              title="View"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            </button>
                            <button 
                              onClick={() => router.push(`/vendor/products/${product.id}/edit`)}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                              title="Edit"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button 
                              onClick={() => handleDeleteProduct(product.id)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                              title="Delete"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          </div>
        </main>
      </div>
    </div>
  );
}
