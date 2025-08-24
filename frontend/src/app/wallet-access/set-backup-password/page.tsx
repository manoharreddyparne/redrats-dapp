'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import axios from 'axios';
import { getGoogleOAuthUrl } from '@/lib/drive/driveApi';

export default function SetBackupPasswordPage() {
  const searchParams = useSearchParams();
  const walletPublicKey = searchParams.get('wallet'); // from query string
  const errorParam = searchParams.get('error');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(errorParam || '');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  const [googleAuthorized, setGoogleAuthorized] = useState(false);

  // ⚡ Check if Google OAuth is authorized
  useEffect(() => {
    async function checkOAuth() {
      try {
        const res = await axios.get('http://localhost:8000/api/drive/oauth-check/', {
          withCredentials: true,
        });

        setGoogleAuthorized(res.data.success);

        if (!res.data.success && walletPublicKey) {
          // redirect to Google OAuth flow
          const urlRes = await getGoogleOAuthUrl(walletPublicKey);
          window.location.href = urlRes.url;
        }
      } catch (err) {
        console.error('OAuth check failed', err);
        setError('Failed to check Google authorization');
      } finally {
        setLoading(false);
      }
    }

    if (walletPublicKey) checkOAuth();
  }, [walletPublicKey]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!walletPublicKey) return setError('Invalid wallet. Please retry backup.');
    if (password.trim() !== confirmPassword.trim()) return setError('Passwords do not match');

    try {
      // 🔑 Direct axios call with cookie auth, no JWT
      await axios.post(
        'http://localhost:8000/api/wallet/wallets/set-backup-password/',
        {
          password,
          password_hint: '',
        },
        {
          headers: { 'X-Wallet-Key': walletPublicKey },
          withCredentials: true, // ✅ use session cookie
        }
      );

      setSuccess('Backup password set successfully!');
      setPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      console.error('Backup password error:', err);
      if (axios.isAxiosError(err)) {
        setError(
          err.response?.data?.error ||
            JSON.stringify(err.response?.data) ||
            'Something went wrong'
        );
      } else {
        setError('Unexpected error');
      }
    }
  };

  if (loading || !googleAuthorized) {
    return (
      <p className="text-center mt-10 text-gray-700">
        Checking Google authorization...
      </p>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white p-6 rounded-xl shadow">
        <h1 className="text-xl font-bold mb-4">Set Backup Password</h1>

        {error && <p className="text-red-600 mb-2">{error}</p>}
        {success && <p className="text-green-600 mb-2">{success}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            placeholder="Enter backup password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
          <input
            type="password"
            placeholder="Confirm backup password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            Save Password
          </button>
        </form>
      </div>
    </div>
  );
}
