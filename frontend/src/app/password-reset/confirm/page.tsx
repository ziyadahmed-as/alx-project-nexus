'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import Navbar from '@/components/Navbar';

function PasswordResetConfirmForm() {
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    const confirmPasswordReset = useAuthStore((state) => state.confirmPasswordReset);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!token) {
            toast.error('Invalid or missing reset token.');
            return;
        }

        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match.');
            return;
        }

        if (newPassword.length < 8) {
            toast.error('Password must be at least 8 characters long.');
            return;
        }

        setLoading(true);

        try {
            await confirmPasswordReset({
                token,
                new_password: newPassword,
                new_password_confirm: confirmPassword,
            });
            toast.success('Password reset successfully! Please login with your new password.');
            router.push('/login');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || error.response?.data?.token?.[0] || 'Password reset failed');
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="text-center">
                <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 inline-block">
                    <p className="font-medium">Invalid or missing reset token</p>
                    <p className="text-sm mt-1">Please ensure you used the full link from your email.</p>
                </div>
                <div>
                    <Link href="/password-reset" className="text-primary hover:underline">
                        Request a new reset link
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium mb-2">New Password</label>
                <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                    required
                    minLength={8}
                />
            </div>

            <div>
                <label className="block text-sm font-medium mb-2">Confirm New Password</label>
                <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
                    required
                    minLength={8}
                />
            </div>

            <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
            >
                {loading ? 'Resetting...' : 'Reset Password'}
            </button>
        </form>
    );
}

export default function PasswordResetConfirmPage() {
    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <div className="container mx-auto px-4 py-12">
                <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
                    <h1 className="text-3xl font-bold mb-6 text-center">Set New Password</h1>
                    <Suspense fallback={<div className="text-center">Loading...</div>}>
                        <PasswordResetConfirmForm />
                    </Suspense>
                </div>
            </div>
        </div>
    );
}
