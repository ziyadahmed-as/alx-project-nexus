'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';
import ProductShareButtons from '@/components/ProductShareButtons';

export default function ShareProductPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tiktokLink, setTiktokLink] = useState<any>(null);
  const [loadingTiktokLink, setLoadingTiktokLink] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchProduct();
  }, [isAuthenticated]);

  const fetchProduct = async () => {
    try {
      const response = await api.get(`/products/${params.id}/`);
      const productData = response.data;
      
      // Verify this product belongs to the current vendor
      const myProductsResponse = await api.get('/products/my-products/');
      const myProducts = myProductsResponse.data.results || myProductsResponse.data;
      const isMyProduct = myProducts.some((p: any) => p.id === parseInt(params.id as string));
      
      if (!isMyProduct) {
        toast.error('You do not have permission to share this product');
        router.push('/vendor/dashboard');
        return;
      }
      
      setProduct(productData);
    } catch (error) {
      toast.error('Failed to load product');
      router.push('/vendor/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const generateTiktokLink = async () => {
    setLoadingTiktokLink(true);
    try {
      const response = await api.get(`/products/${params.id}/tiktok-link/`);
      setTiktokLink(response.data);
      toast.success('TikTok dashboard link generated!');
    } catch (error) {
      toast.error('Failed to generate TikTok link');
    } finally {
      setLoadingTiktokLink(false);
    }
  };

  const copyTiktokLink = async () => {
    if (tiktokLink) {
      try {
        await navigator.clipboard.writeText(tiktokLink.tiktok_dashboard_link);
        toast.success('TikTok dashboard link copied!');
      } catch (error) {
        toast.error('Failed to copy link');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8 text-center">Loading...</div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-gray-600">Product not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <button
          onClick={() => router.back()}
          className="text-gray-600 hover:text-gray-900 mb-6"
        >
          ← Back
        </button>

        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Share Your Product</h1>

          {/* Product Preview */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex gap-4">
              {product.image && (
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-24 h-24 object-cover rounded-lg"
                />
              )}
              <div className="flex-1">
                <h2 className="text-xl font-bold mb-2">{product.name}</h2>
                <p className="text-2xl text-primary font-bold mb-2">${product.price}</p>
                <p className="text-sm text-gray-600 line-clamp-2">{product.description}</p>
              </div>
            </div>
          </div>

          {/* Share Options */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold mb-4">Share on Social Media</h3>
            <p className="text-sm text-gray-600 mb-6">
              Share your product on social media to reach more customers and increase sales!
            </p>

            <ProductShareButtons
              productId={product.id}
              productName={product.name}
              productDescription={product.description}
              productImage={product.image}
              productPrice={product.price}
            />
          </div>

          {/* TikTok Dashboard Link Generator */}
          <div className="bg-gradient-to-r from-black to-gray-800 text-white rounded-lg p-6 mt-6">
            <div className="flex items-center gap-3 mb-4">
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
              </svg>
              <div>
                <h3 className="text-xl font-bold">TikTok Dashboard Link</h3>
                <p className="text-sm text-gray-300">Generate a special tracking link for TikTok</p>
              </div>
            </div>

            {!tiktokLink ? (
              <button
                onClick={generateTiktokLink}
                disabled={loadingTiktokLink}
                className="w-full bg-white text-black py-3 px-6 rounded-lg hover:bg-gray-100 transition-colors font-medium disabled:opacity-50"
              >
                {loadingTiktokLink ? 'Generating...' : 'Generate TikTok Dashboard Link'}
              </button>
            ) : (
              <div className="space-y-4">
                <div className="bg-white/10 rounded-lg p-4">
                  <label className="block text-sm font-medium mb-2">Dashboard Link (with tracking)</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={tiktokLink.tiktok_dashboard_link}
                      readOnly
                      className="flex-1 px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-sm text-white"
                    />
                    <button
                      onClick={copyTiktokLink}
                      className="px-4 py-2 bg-white text-black rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                </div>

                <div className="bg-white/10 rounded-lg p-4">
                  <label className="block text-sm font-medium mb-2">Suggested Caption</label>
                  <p className="text-sm bg-white/20 p-3 rounded-lg">{tiktokLink.share_text}</p>
                </div>

                <div className="bg-white/10 rounded-lg p-4">
                  <label className="block text-sm font-medium mb-2">Suggested Hashtags</label>
                  <p className="text-sm bg-white/20 p-3 rounded-lg">
                    #{tiktokLink.hashtags.join(' #')}
                  </p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      copyTiktokLink();
                      window.open('https://www.tiktok.com/', '_blank');
                    }}
                    className="flex-1 bg-white text-black py-3 px-6 rounded-lg hover:bg-gray-100 transition-colors font-medium"
                  >
                    Copy & Open TikTok
                  </button>
                  <button
                    onClick={() => setTiktokLink(null)}
                    className="px-4 py-3 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors"
                  >
                    Reset
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Share Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-6">
            <h3 className="font-bold mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Sharing Tips
            </h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• <strong>Facebook:</strong> Share directly to your timeline or business page</li>
              <li>• <strong>Instagram:</strong> Copy link and paste in your story or bio</li>
              <li>• <strong>TikTok:</strong> Use the dashboard link above for better tracking</li>
              <li>• <strong>Telegram:</strong> Share in your channels or groups</li>
              <li>• <strong>WhatsApp:</strong> Send to your contacts or status</li>
              <li>• <strong>Twitter/X:</strong> Tweet about your product with the link</li>
            </ul>
          </div>

          {/* Share Statistics */}
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h3 className="text-lg font-bold mb-4">Product Statistics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-primary">{product.views || 0}</p>
                <p className="text-sm text-gray-600">Views</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">{product.sales_count || 0}</p>
                <p className="text-sm text-gray-600">Sales</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">{product.stock || 0}</p>
                <p className="text-sm text-gray-600">In Stock</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
