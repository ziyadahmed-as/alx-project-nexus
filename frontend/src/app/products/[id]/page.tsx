'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { useCartStore } from '@/store/cartStore';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';
import SocialShare from '@/components/SocialShare';

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const addItem = useCartStore((state) => state.addItem);
  const { user, isAuthenticated } = useAuthStore();
  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const [isOwnProduct, setIsOwnProduct] = useState(false);

  useEffect(() => {
    fetchProduct();
  }, []);

  const fetchProduct = async () => {
    try {
      const response = await api.get(`/products/${params.id}/`);
      setProduct(response.data);
      
      // Check if current user is the product owner
      if (isAuthenticated && user) {
        // Check if user is vendor and owns this product
        if (user.role === 'vendor') {
          try {
            const vendorProfile = await api.get('/vendors/profile/');
            if (vendorProfile.data.id === response.data.vendor) {
              setIsOwnProduct(true);
            }
          } catch (error) {
            console.log('Could not fetch vendor profile');
          }
        }
      }
    } catch (error) {
      console.error('Error fetching product:', error);
      toast.error('Product not found');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    if (!product) return;
    
    // Prevent vendors from adding their own products to cart
    if (isOwnProduct) {
      toast.error('You cannot purchase your own products!');
      return;
    }
    
    addItem({
      id: product.id,
      name: product.name,
      price: parseFloat(product.price),
      quantity: quantity,
      vendor: product.vendor_name,
      image: product.images?.[0]?.image,
    });
    
    toast.success(`Added ${quantity} item(s) to cart!`);
  };

  const handleBuyNow = () => {
    handleAddToCart();
    router.push('/cart');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8 text-center">
          <div className="animate-pulse">Loading...</div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-gray-600 mb-4">Product not found</p>
          <button
            onClick={() => router.push('/products')}
            className="bg-primary text-white px-6 py-2 rounded-lg"
          >
            Back to Products
          </button>
        </div>
      </div>
    );
  }

  const discount = product.compare_price 
    ? Math.round(((parseFloat(product.compare_price) - parseFloat(product.price)) / parseFloat(product.compare_price)) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="mb-6 text-sm text-gray-600">
          <Link href="/" className="hover:text-primary">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/products" className="hover:text-primary">Products</Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900">{product.name}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Product Images */}
          <div>
            <div className="bg-white rounded-lg shadow-md p-4 mb-4">
              <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
                {product.images && product.images.length > 0 ? (
                  <img
                    src={product.images[selectedImage]?.image}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-gray-400 text-lg">No Image</span>
                )}
              </div>
            </div>
            
            {/* Thumbnail Images */}
            {product.images && product.images.length > 1 && (
              <div className="grid grid-cols-4 gap-2">
                {product.images.map((image: any, index: number) => (
                  <button
                    key={image.id}
                    onClick={() => setSelectedImage(index)}
                    className={`aspect-square bg-white rounded-lg p-2 border-2 ${
                      selectedImage === index ? 'border-primary' : 'border-gray-200'
                    }`}
                  >
                    <img
                      src={image.image}
                      alt={`${product.name} ${index + 1}`}
                      className="w-full h-full object-cover rounded"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div>
            <div className="bg-white rounded-lg shadow-md p-6">
              {/* Product Title */}
              <h1 className="text-3xl font-bold mb-2">{product.name}</h1>
              
              {/* Vendor */}
              <Link 
                href={`/vendors/${product.vendor}`}
                className="text-primary hover:underline mb-4 inline-block"
              >
                by {product.vendor_name}
              </Link>

              {/* Rating & Reviews */}
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center">
                  <span className="text-yellow-500 text-lg">★★★★★</span>
                  <span className="ml-2 text-sm text-gray-600">(0 reviews)</span>
                </div>
                <span className="text-sm text-gray-600">
                  {product.sales_count || 0} sold
                </span>
              </div>

              {/* Price */}
              <div className="mb-6">
                <div className="flex items-baseline gap-3">
                  <span className="text-4xl font-bold text-primary">
                    ${parseFloat(product.price).toFixed(2)}
                  </span>
                  {product.compare_price && (
                    <>
                      <span className="text-xl text-gray-400 line-through">
                        ${parseFloat(product.compare_price).toFixed(2)}
                      </span>
                      <span className="bg-red-100 text-red-600 px-2 py-1 rounded text-sm font-semibold">
                        {discount}% OFF
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Stock Status */}
              <div className="mb-6">
                {product.stock > 0 ? (
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-green-600 font-medium">
                      In Stock ({product.stock} available)
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    <span className="text-red-600 font-medium">Out of Stock</span>
                  </div>
                )}
              </div>

              {/* Quantity Selector */}
              {product.stock > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">Quantity</label>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="w-10 h-10 border rounded-lg hover:bg-gray-100"
                    >
                      -
                    </button>
                    <input
                      type="number"
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, Math.min(product.stock, parseInt(e.target.value) || 1)))}
                      className="w-20 text-center border rounded-lg py-2"
                      min="1"
                      max={product.stock}
                    />
                    <button
                      onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                      className="w-10 h-10 border rounded-lg hover:bg-gray-100"
                    >
                      +
                    </button>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-4 mb-6">
                {isOwnProduct ? (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h3 className="font-semibold text-blue-900 mb-1">This is Your Product</h3>
                        <p className="text-sm text-blue-800 mb-3">
                          You cannot purchase your own products. You can edit or manage this product from your vendor dashboard.
                        </p>
                        <button
                          onClick={() => router.push(`/vendor/products/${product.id}/edit`)}
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
                        >
                          Edit Product
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-4">
                    <button
                      onClick={handleAddToCart}
                      disabled={product.stock === 0}
                      className="flex-1 bg-primary text-white py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 font-medium"
                    >
                      Add to Cart
                    </button>
                    <button
                      onClick={handleBuyNow}
                      disabled={product.stock === 0}
                      className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium"
                    >
                      Buy Now
                    </button>
                  </div>
                )}
                
                {/* Social Share */}
                <div className="flex justify-center">
                  <SocialShare 
                    productId={product.id}
                    productName={product.name}
                    productPrice={product.price}
                    vendorId={product.vendor}
                  />
                </div>
              </div>

              {/* Product Meta */}
              <div className="border-t pt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">SKU:</span>
                  <span className="font-medium">{product.sku}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Category:</span>
                  <span className="font-medium">{product.category || 'Uncategorized'}</span>
                </div>
                {product.featured && (
                  <div className="flex items-center gap-2">
                    <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-semibold">
                      ⭐ Featured Product
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Product Description */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">Product Description</h2>
          <div className="prose max-w-none text-gray-700 whitespace-pre-line">
            {product.description}
          </div>
        </div>

        {/* Product Variations */}
        {product.variations && product.variations.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4">Available Variations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {product.variations.map((variation: any) => (
                <div key={variation.id} className="border rounded-lg p-4">
                  <div className="font-semibold">{variation.name}: {variation.value}</div>
                  <div className="text-sm text-gray-600">
                    Price: ${(parseFloat(product.price) + parseFloat(variation.price_adjustment)).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">
                    Stock: {variation.stock}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reviews Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">Customer Reviews</h2>
          <div className="text-center py-12 text-gray-500">
            <p>No reviews yet. Be the first to review this product!</p>
          </div>
        </div>
      </main>
    </div>
  );
}
