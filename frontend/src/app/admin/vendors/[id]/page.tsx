'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

export default function VendorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [vendor, setVendor] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verificationNotes, setVerificationNotes] = useState('');

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') {
      router.push('/');
      return;
    }
    fetchVendorDetails();
  }, [isAuthenticated, user]);

  const fetchVendorDetails = async () => {
    try {
      const response = await api.get(`/vendors/${params.id}/`);
      setVendor(response.data);
      setVerificationNotes(response.data.verification_notes || '');
    } catch (error) {
      toast.error('Failed to load vendor details');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (status: string) => {
    try {
      await api.post(`/vendors/${params.id}/verify/`, {
        status,
        verification_notes: verificationNotes
      });
      toast.success(`Vendor ${status} successfully!`);
      fetchVendorDetails();
    } catch (error) {
      toast.error('Failed to update vendor status');
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

  if (!vendor) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-gray-600">Vendor not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900 mb-4"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold">Vendor Application Details</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Information */}
          <div className="lg:col-span-2 space-y-6">
            {/* Business Information */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Business Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Business Name</label>
                  <p className="font-medium">{vendor.business_name}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Business Email</label>
                  <p className="font-medium">{vendor.business_email}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Business Phone</label>
                  <p className="font-medium">{vendor.business_phone}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Tax ID</label>
                  <p className="font-medium">{vendor.tax_id || 'N/A'}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-sm text-gray-600">Business Description</label>
                  <p className="font-medium">{vendor.business_description}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-sm text-gray-600">Business Address</label>
                  <p className="font-medium">{vendor.business_address}</p>
                </div>
              </div>
            </div>

            {/* Office Address */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Physical Office Address</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="text-sm text-gray-600">Office Address</label>
                  <p className="font-medium">{vendor.office_address || 'Not provided'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">City</label>
                  <p className="font-medium">{vendor.office_city || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">State/Region</label>
                  <p className="font-medium">{vendor.office_state || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Country</label>
                  <p className="font-medium">{vendor.office_country || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Postal Code</label>
                  <p className="font-medium">{vendor.office_postal_code || 'N/A'}</p>
                </div>
              </div>
            </div>

            {/* Verification Documents */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Verification Documents</h2>
              <div className="space-y-3">
                {vendor.business_license && (
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">Business License</p>
                      <p className="text-xs text-gray-600">Required document</p>
                    </div>
                    <a
                      href={vendor.business_license}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      View Document →
                    </a>
                  </div>
                )}

                {vendor.tax_certificate && (
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">Tax Certificate</p>
                      <p className="text-xs text-gray-600">Optional document</p>
                    </div>
                    <a
                      href={vendor.tax_certificate}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      View Document →
                    </a>
                  </div>
                )}

                {vendor.id_document && (
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">ID Document</p>
                      <p className="text-xs text-gray-600">Owner's ID or Passport</p>
                    </div>
                    <a
                      href={vendor.id_document}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      View Document →
                    </a>
                  </div>
                )}

                {vendor.bank_statement && (
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">Bank Statement</p>
                      <p className="text-xs text-gray-600">Optional document</p>
                    </div>
                    <a
                      href={vendor.bank_statement}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      View Document →
                    </a>
                  </div>
                )}

                {vendor.additional_document && (
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">Additional Document</p>
                      <p className="text-xs text-gray-600">Supporting document</p>
                    </div>
                    <a
                      href={vendor.additional_document}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      View Document →
                    </a>
                  </div>
                )}

                {!vendor.business_license && !vendor.tax_certificate && !vendor.id_document && 
                 !vendor.bank_statement && !vendor.additional_document && (
                  <p className="text-gray-500 text-center py-4">No documents uploaded</p>
                )}
              </div>
            </div>
          </div>

          {/* Verification Panel */}
          <div>
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
              <h2 className="text-xl font-bold mb-4">Verification</h2>
              
              <div className="mb-4">
                <label className="text-sm text-gray-600">Current Status</label>
                <p className={`inline-block px-3 py-1 rounded-full text-sm font-medium mt-1 ${
                  vendor.status === 'approved' ? 'bg-green-100 text-green-800' :
                  vendor.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                  vendor.status === 'rejected' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {vendor.status.charAt(0).toUpperCase() + vendor.status.slice(1)}
                </p>
              </div>

              <div className="mb-4">
                <label className="text-sm text-gray-600">Applied On</label>
                <p className="font-medium">{new Date(vendor.created_at).toLocaleDateString()}</p>
              </div>

              {vendor.verified_at && (
                <div className="mb-4">
                  <label className="text-sm text-gray-600">Verified On</label>
                  <p className="font-medium">{new Date(vendor.verified_at).toLocaleDateString()}</p>
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Verification Notes</label>
                <textarea
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="Add notes about this vendor..."
                />
              </div>

              {vendor.status === 'pending' && (
                <div className="space-y-2">
                  <button
                    onClick={() => handleVerify('approved')}
                    className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
                  >
                    Approve Vendor
                  </button>
                  <button
                    onClick={() => handleVerify('rejected')}
                    className="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700"
                  >
                    Reject Application
                  </button>
                </div>
              )}

              {vendor.status === 'approved' && (
                <button
                  onClick={() => handleVerify('suspended')}
                  className="w-full bg-orange-600 text-white py-2 rounded-lg hover:bg-orange-700"
                >
                  Suspend Vendor
                </button>
              )}

              {vendor.status === 'suspended' && (
                <button
                  onClick={() => handleVerify('approved')}
                  className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
                >
                  Reactivate Vendor
                </button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
