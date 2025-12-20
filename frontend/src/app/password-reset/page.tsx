'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

export default function PasswordResetRequestPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const requestPasswordReset = useAuthStore((state) => state.requestPasswordReset);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            await requestPasswordReset(email);
            setSubmitted(true);
            toast.success('Password reset link sent to your email.');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to send reset link');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <div className="container mx-auto px-4 py-12">
                <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
                    <h1 className="text-3xl font-bold mb-6 text-center">Reset Password</h1>

                    {!submitted ? (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <p className="text-gray-600 mb-4 text-center">
                                Enter your email address and we'll send you a link to reset your password.
                            </p>

                            <div>
                                <label className="block text-sm font-medium mb-2">Email Address</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-primary text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
                            >
                                {loading ? 'Sending...' : 'Send Reset Link'}
                            </button>
                        </form>
                    ) : (
                        <div className="text-center">
                            <div className="mb-6 text-green-600">
                                <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <h3 className="text-xl font-medium">Check your email</h3>
                                <p className="mt-2 text-gray-600">
                                    We have sent a password reset link to <strong>{email}</strong>.
                                </p>
                            </div>
                        </div>
                    )}

                    <div className="mt-6 text-center">
                        <Link href="/login" className="text-primary hover:underline">
                            Back to Login
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
