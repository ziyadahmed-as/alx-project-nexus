'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

export default function AdminUsersPage() {
  const { user, isAuthenticated } = useAuthStore();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterRole, setFilterRole] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') {
      router.push('/');
      return;
    }
    fetchUsers();
  }, [isAuthenticated, user]);

  const fetchUsers = async () => {
    try {
      const response = await api.get('/auth/users/');
      const userData = response.data.results || response.data;
      setUsers(Array.isArray(userData) ? userData : []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    try {
      await api.patch(`/auth/${userId}/`, { is_active: !currentStatus });
      toast.success(`User ${!currentStatus ? 'activated' : 'deactivated'} successfully`);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error('Failed to update user status');
    }
  };

  const handleToggleVerified = async (userId: number, currentStatus: boolean) => {
    try {
      await api.patch(`/auth/${userId}/`, { is_verified: !currentStatus });
      toast.success(`User ${!currentStatus ? 'verified' : 'unverified'} successfully`);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error('Failed to update user verification');
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesSearch = 
      u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.username?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'all' || u.role === filterRole;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="flex">
        {/* Admin Sidebar */}
        <aside className="w-64 bg-white shadow-lg min-h-screen">
          <div className="p-6">
            <h2 className="text-xl font-bold mb-6 text-red-600">Admin Panel</h2>
            <nav className="space-y-2">
              <button
                onClick={() => router.push('/admin/dashboard')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                Dashboard
              </button>
              <button
                onClick={() => router.push('/admin/vendors')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                Vendor Management
              </button>
              <button
                onClick={() => router.push('/admin/products')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                Products
              </button>
              <button
                onClick={() => router.push('/admin/orders')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
                Orders
              </button>
              <button
                onClick={() => router.push('/admin/users')}
                className="w-full text-left px-4 py-3 bg-red-50 text-red-600 rounded-lg font-medium flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                Users
              </button>
              <button
                onClick={() => router.push('/admin/categories')}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 rounded-lg flex items-center gap-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                Categories
              </button>
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <h1 className="text-3xl font-bold mb-6">User Management</h1>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Search</label>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by name, email, username..."
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Role Filter</label>
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                >
                  <option value="all">All Roles</option>
                  <option value="customer">Customers</option>
                  <option value="vendor">Vendors</option>
                  <option value="admin">Admins</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={fetchUsers}
                  className="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600"
                >
                  Refresh
                </button>
              </div>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">All Users ({filteredUsers.length})</h2>
              
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-gray-600">Loading users...</p>
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <p className="text-gray-600">No users found</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left py-3 px-4 font-semibold">Name</th>
                        <th className="text-left py-3 px-4 font-semibold">Email</th>
                        <th className="text-left py-3 px-4 font-semibold">Username</th>
                        <th className="text-left py-3 px-4 font-semibold">Role</th>
                        <th className="text-left py-3 px-4 font-semibold">Status</th>
                        <th className="text-left py-3 px-4 font-semibold">Joined</th>
                        <th className="text-center py-3 px-4 font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((u: any) => (
                        <tr key={u.id} className="border-b hover:bg-gray-50">
                          <td className="py-3 px-4 font-medium">
                            {u.first_name || u.last_name ? `${u.first_name} ${u.last_name}` : 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-gray-600">{u.email}</td>
                          <td className="py-3 px-4 text-gray-600">{u.username}</td>
                          <td className="py-3 px-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              u.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                              u.role === 'vendor' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {u.role.charAt(0).toUpperCase() + u.role.slice(1)}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex flex-col gap-1">
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold inline-block ${
                                u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                              {u.is_verified && (
                                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 inline-block">
                                  Verified
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {new Date(u.date_joined).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex justify-center gap-2">
                              <button
                                onClick={() => handleToggleActive(u.id, u.is_active)}
                                className={`p-2 rounded-lg ${
                                  u.is_active 
                                    ? 'text-red-600 hover:bg-red-50' 
                                    : 'text-green-600 hover:bg-green-50'
                                }`}
                                title={u.is_active ? 'Deactivate User' : 'Activate User'}
                              >
                                {u.is_active ? (
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                                  </svg>
                                ) : (
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                )}
                              </button>
                              
                              <button
                                onClick={() => handleToggleVerified(u.id, u.is_verified)}
                                className={`p-2 rounded-lg ${
                                  u.is_verified 
                                    ? 'text-gray-600 hover:bg-gray-50' 
                                    : 'text-blue-600 hover:bg-blue-50'
                                }`}
                                title={u.is_verified ? 'Unverify User' : 'Verify User'}
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
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
