'use client';

import Link from 'next/link';
import { useCartStore } from '@/store/cartStore';
import toast from 'react-hot-toast';

interface Product {
  id: number;
  name: string;
  price: string;
  compare_price?: string;
  images?: any[];
  vendor_name: string;
  stock: number;
  featured?: boolean;
  created_at?: string;
}

export default function ProductCard({ product }: { product: Product }) {
  const addItem = useCartStore((state) => state.addItem);

  const handleAddToCart = () => {
    addItem({
      id: product.id,
      name: product.name,
      price: parseFloat(product.price),
      quantity: 1,
      vendor: product.vendor_name,
    });
    toast.success('Added to cart!');
  };

  // Check if product is new (created within last 7 days)
  const isNew = product.created_at 
    ? new Date().getTime() - new Date(product.created_at).getTime() < 7 * 24 * 60 * 60 * 1000
    : false;

  // Calculate discount percentage
  const discount = product.compare_price 
    ? Math.round(((parseFloat(product.compare_price) - parseFloat(product.price)) / parseFloat(product.compare_price)) * 100)
    : 0;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition">
      <Link href={`/products/${product.id}`}>
        <div className="h-48 bg-gray-200 flex items-center justify-center relative">
          {product.images?.[0] ? (
            <img src={product.images[0].image} alt={product.name} className="w-full h-full object-cover" />
          ) : (
            <span className="text-gray-400">No Image</span>
          )}
          
          {/* Badges */}
          <div className="absolute top-2 left-2 flex flex-col gap-2">
            {product.featured && (
              <span className="bg-yellow-500 text-white px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                ⭐ Featured
              </span>
            )}
            {isNew && (
              <span className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                🆕 New
              </span>
            )}
          </div>
          
          {/* Discount Badge */}
          {discount > 0 && (
            <div className="absolute top-2 right-2">
              <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                -{discount}%
              </span>
            </div>
          )}
        </div>
      </Link>
      
      <div className="p-4">
        <Link href={`/products/${product.id}`}>
          <h3 className="font-semibold text-lg mb-2 hover:text-primary line-clamp-2">{product.name}</h3>
        </Link>
        <p className="text-sm text-gray-600 mb-3">by {product.vendor_name}</p>
        
        {/* Price Section */}
        <div className="mb-3">
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-primary">${parseFloat(product.price).toFixed(2)}</span>
            {product.compare_price && (
              <span className="text-sm text-gray-400 line-through">
                ${parseFloat(product.compare_price).toFixed(2)}
              </span>
            )}
          </div>
        </div>
        
        {/* Stock Status */}
        <div className="mb-3">
          {product.stock > 0 ? (
            <span className="text-xs text-green-600 font-medium">
              ✓ In Stock ({product.stock} available)
            </span>
          ) : (
            <span className="text-xs text-red-600 font-medium">
              ✗ Out of Stock
            </span>
          )}
        </div>
        
        {/* Add to Cart Button */}
        <button
          onClick={handleAddToCart}
          disabled={product.stock === 0}
          className="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 font-medium transition"
        >
          {product.stock > 0 ? 'Add to Cart' : 'Out of Stock'}
        </button>
      </div>
    </div>
  );
}
