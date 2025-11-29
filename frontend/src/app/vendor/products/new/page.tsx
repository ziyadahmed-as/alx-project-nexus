'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

interface ProductVariation {
  id: string;
  name: string;
  value: string;
  price_adjustment: string;
  stock: string;
  sku: string;
}

interface ProductImage {
  id: string;
  file: File | null;
  preview: string;
  is_primary: boolean;
  order: number;
}

export default function AddProductPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [categories, setCategories] = useState<any[]>([]);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    compare_price: '',
    stock: '',
    sku: '',
    category: '',
    is_active: true,
    featured: false,
  });

  const [images, setImages] = useState<ProductImage[]>([]);
  const [variations, setVariations] = useState<ProductVariation[]>([]);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/products/categories/');
      const categoryData = response.data.results || response.data;
      setCategories(Array.isArray(categoryData) ? categoryData : []);
    } catch (error) {
      console.error('Error fetching categories:', error);
      toast.error('Failed to load categories');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
      return;
    }

    setLoading(true);

    try {
      const formDataToSend = new FormData();
      
      // Basic product info
      formDataToSend.append('name', formData.name);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('price', formData.price);
      formDataToSend.append('stock', formData.stock);
      formDataToSend.append('sku', formData.sku);
      formDataToSend.append('slug', formData.name.toLowerCase().replace(/\s+/g, '-'));
      formDataToSend.append('is_active', String(formData.is_active));
      formDataToSend.append('featured', String(formData.featured));
      
      if (formData.compare_price) {
        formDataToSend.append('compare_price', formData.compare_price);
      }
      
      if (formData.category) {
        formDataToSend.append('category', formData.category);
      }

      // Add images
      images.forEach((img, index) => {
        if (img.file) {
          formDataToSend.append(`images`, img.file);
          formDataToSend.append(`image_${index}_is_primary`, String(img.is_primary));
          formDataToSend.append(`image_${index}_order`, String(img.order));
        }
      });

      // Add variations as JSON
      if (variations.length > 0) {
        formDataToSend.append('variations', JSON.stringify(variations));
      }

      await api.post('/products/create/', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      toast.success('Product created successfully!');
      router.push('/vendor/dashboard');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create product');
      console.error('Product creation error:', error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newImages: ProductImage[] = Array.from(files).map((file, index) => ({
      id: `${Date.now()}-${index}`,
      file,
      preview: URL.createObjectURL(file),
      is_primary: images.length === 0 && index === 0,
      order: images.length + index,
    }));

    setImages([...images, ...newImages]);
  };

  const removeImage = (id: string) => {
    setImages(images.filter(img => img.id !== id));
  };

  const setPrimaryImage = (id: string) => {
    setImages(images.map(img => ({
      ...img,
      is_primary: img.id === id
    })));
  };

  const addVariation = () => {
    setVariations([
      ...variations,
      {
        id: `${Date.now()}`,
        name: '',
        value: '',
        price_adjustment: '0',
        stock: '0',
        sku: `${formData.sku}-VAR-${variations.length + 1}`,
      }
    ]);
  };

  const removeVariation = (id: string) => {
    setVariations(variations.filter(v => v.id !== id));
  };

  const updateVariation = (id: string, field: keyof ProductVariation, value: string) => {
    setVariations(variations.map(v => 
      v.id === id ? { ...v, [field]: value } : v
    ));
  };

  const validateStep = () => {
    if (currentStep === 1) {
      if (!formData.name || !formData.description || !formData.price || !formData.stock || !formData.sku) {
        toast.error('Please fill in all required fields');
        return false;
      }
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">Add New Product</h1>
          <p className="text-gray-600 mb-6">Complete all steps to create your product listing</p>

          {/* Progress Steps */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center flex-1">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold ${
                    currentStep >= step ? 'bg-primary text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {step}
                  </div>
                  <div className="flex-1 mx-2">
                    <div className={`h-1 ${currentStep > step ? 'bg-primary' : 'bg-gray-200'}`}></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2">
              <span className={`text-sm ${currentStep >= 1 ? 'text-primary font-medium' : 'text-gray-500'}`}>
                Basic Info
              </span>
              <span className={`text-sm ${currentStep >= 2 ? 'text-primary font-medium' : 'text-gray-500'}`}>
                Images
              </span>
              <span className={`text-sm ${currentStep >= 3 ? 'text-primary font-medium' : 'text-gray-500'}`}>
                Variations
              </span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              
              {/* Step 1: Basic Information */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-bold mb-4">Basic Product Information</h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-2">Product Name *</label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                        placeholder="e.g., Premium Cotton T-Shirt"
                        required
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-2">Description *</label>
                      <textarea
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        rows={5}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                        placeholder="Describe your product in detail..."
                        required
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-2">Category *</label>
                      <select
                        name="category"
                        value={formData.category}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                        required
                      >
                        <option value="">Select a category</option>
                        {categories.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Price *</label>
                      <div className="relative">
                        <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                        <input
                          type="number"
                          name="price"
                          value={formData.price}
                          onChange={handleChange}
                          step="0.01"
                          min="0"
                          className="w-full pl-8 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                          placeholder="0.00"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Compare at Price</label>
                      <div className="relative">
                        <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                        <input
                          type="number"
                          name="compare_price"
                          value={formData.compare_price}
                          onChange={handleChange}
                          step="0.01"
                          min="0"
                          className="w-full pl-8 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                          placeholder="0.00"
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Original price for showing discounts</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">Stock Quantity *</label>
                      <input
                        type="number"
                        name="stock"
                        value={formData.stock}
                        onChange={handleChange}
                        min="0"
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                        placeholder="0"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">SKU (Stock Keeping Unit) *</label>
                      <input
                        type="text"
                        name="sku"
                        value={formData.sku}
                        onChange={handleChange}
                        className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                        placeholder="e.g., TSHIRT-001"
                        required
                      />
                    </div>

                    <div className="md:col-span-2">
                      <div className="flex items-center gap-6">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            name="is_active"
                            checked={formData.is_active}
                            onChange={handleChange}
                            className="w-4 h-4 text-primary"
                          />
                          <span className="text-sm font-medium">Active (visible to customers)</span>
                        </label>

                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            name="featured"
                            checked={formData.featured}
                            onChange={handleChange}
                            className="w-4 h-4 text-primary"
                          />
                          <span className="text-sm font-medium">Featured Product</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Product Images */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-bold mb-4">Product Images</h2>
                  
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                    <input
                      type="file"
                      id="image-upload"
                      multiple
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                    />
                    <label htmlFor="image-upload" className="cursor-pointer">
                      <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <p className="text-lg font-medium text-gray-700 mb-2">Click to upload images</p>
                      <p className="text-sm text-gray-500">PNG, JPG, GIF up to 5MB each</p>
                    </label>
                  </div>

                  {images.length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {images.map((img) => (
                        <div key={img.id} className="relative group">
                          <img
                            src={img.preview}
                            alt="Product"
                            className={`w-full h-40 object-cover rounded-lg ${img.is_primary ? 'ring-4 ring-primary' : ''}`}
                          />
                          <div className="absolute top-2 right-2 flex gap-2">
                            {!img.is_primary && (
                              <button
                                type="button"
                                onClick={() => setPrimaryImage(img.id)}
                                className="bg-white p-1.5 rounded-full shadow hover:bg-gray-100"
                                title="Set as primary"
                              >
                                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => removeImage(img.id)}
                              className="bg-red-500 p-1.5 rounded-full shadow hover:bg-red-600"
                              title="Remove"
                            >
                              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </div>
                          {img.is_primary && (
                            <div className="absolute bottom-2 left-2 bg-primary text-white text-xs px-2 py-1 rounded">
                              Primary
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Step 3: Product Variations */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center">
                    <div>
                      <h2 className="text-xl font-bold">Product Variations</h2>
                      <p className="text-sm text-gray-600">Add variations like size, color, or material (optional)</p>
                    </div>
                    <button
                      type="button"
                      onClick={addVariation}
                      className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center gap-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add Variation
                    </button>
                  </div>

                  {variations.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-lg">
                      <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                      </svg>
                      <p className="text-gray-600 mb-2">No variations added yet</p>
                      <p className="text-sm text-gray-500">Click "Add Variation" to create product variants</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {variations.map((variation, index) => (
                        <div key={variation.id} className="border rounded-lg p-4 bg-gray-50">
                          <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold">Variation {index + 1}</h3>
                            <button
                              type="button"
                              onClick={() => removeVariation(variation.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                            <div>
                              <label className="block text-sm font-medium mb-1">Type</label>
                              <input
                                type="text"
                                value={variation.name}
                                onChange={(e) => updateVariation(variation.id, 'name', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg text-sm"
                                placeholder="e.g., Size, Color"
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium mb-1">Value</label>
                              <input
                                type="text"
                                value={variation.value}
                                onChange={(e) => updateVariation(variation.id, 'value', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg text-sm"
                                placeholder="e.g., Large, Red"
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium mb-1">Price +/-</label>
                              <input
                                type="number"
                                value={variation.price_adjustment}
                                onChange={(e) => updateVariation(variation.id, 'price_adjustment', e.target.value)}
                                step="0.01"
                                className="w-full px-3 py-2 border rounded-lg text-sm"
                                placeholder="0.00"
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium mb-1">Stock</label>
                              <input
                                type="number"
                                value={variation.stock}
                                onChange={(e) => updateVariation(variation.id, 'stock', e.target.value)}
                                min="0"
                                className="w-full px-3 py-2 border rounded-lg text-sm"
                                placeholder="0"
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium mb-1">SKU</label>
                              <input
                                type="text"
                                value={variation.sku}
                                onChange={(e) => updateVariation(variation.id, 'sku', e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg text-sm"
                                placeholder="SKU-001"
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between pt-6 border-t">
                <button
                  type="button"
                  onClick={prevStep}
                  disabled={currentStep === 1}
                  className="px-6 py-3 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Previous
                </button>

                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={() => router.back()}
                    className="px-6 py-3 border rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  
                  {currentStep < 3 ? (
                    <button
                      type="button"
                      onClick={nextStep}
                      className="bg-primary text-white px-6 py-3 rounded-lg hover:bg-blue-600 flex items-center gap-2"
                    >
                      Next
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2"
                    >
                      {loading ? (
                        <>
                          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Creating...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Create Product
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
