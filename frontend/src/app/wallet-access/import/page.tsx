'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/auth';
import { AxiosError } from 'axios';

interface Wallet {
  id: number;
  wallet_name: string;
  public_key: string;
  backup_drive_file_id?: string;
}

interface ImportWalletResponse {
  wallet: Wallet;
  message?: string;
}

export default function ImportWalletPage() {
  const router = useRouter();
  const [mnemonic, setMnemonic] = useState('');
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [googlePassword, setGooglePassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // ---- Manual mnemonic import ----
  const handleManualImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authApi.post<ImportWalletResponse>('/wallets/import/', { mnemonic });
      router.push('/wallets'); // redirect to wallet dashboard
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.error || 'Failed to import wallet');
      } else {
        setError('Failed to import wallet');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // ---- Google Drive restore ----
  const handleGoogleRestore = async () => {
    setError('');
    setLoading(true);

    try {
      // Trigger Google OAuth flow
      const initRes = await fetch('/api/drive/auth/init/');
      if (!initRes.ok) throw new Error('Failed to initiate Google auth');

      // Complete wallet restore with backup password
      await authApi.post<ImportWalletResponse>('/wallets/restore/', { password: googlePassword });
      router.push('/wallets');
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.error || 'Google Drive restore failed');
      } else {
        setError('Google Drive restore failed');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md space-y-6">
        <h1 className="text-3xl font-bold text-gray-800 text-center">Import Wallet</h1>

        {/* --- Manual mnemonic import --- */}
        <form onSubmit={handleManualImport} className="space-y-4">
          <label className="block mb-2 font-medium text-gray-700">
            Enter 15-word mnemonic
          </label>
          <textarea
            rows={3}
            value={mnemonic}
            onChange={(e) => setMnemonic(e.target.value)}
            className="border p-3 w-full rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="word1 word2 ... word15"
            required
          />

          {error && <p className="text-red-500">{error}</p>}

          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors duration-200"
            disabled={loading}
          >
            {loading ? 'Importing...' : 'Import Wallet'}
          </button>
        </form>

        <div className="border-t"></div>

        {/* --- Google Drive restore --- */}
        <button
          onClick={() => setShowGoogleModal(true)}
          className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors duration-200"
        >
          Restore from Google Drive
        </button>

        {showGoogleModal && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50 p-4">
            <div className="bg-white p-6 rounded-xl shadow-lg w-full max-w-sm space-y-4">
              <h2 className="text-xl font-bold text-gray-800">Enter Backup Password</h2>

              <input
                type="password"
                value={googlePassword}
                onChange={(e) => setGooglePassword(e.target.value)}
                className="border p-3 w-full rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
                placeholder="Backup password"
              />

              {error && <p className="text-red-500">{error}</p>}

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowGoogleModal(false)}
                  className="bg-gray-300 text-black py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors duration-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGoogleRestore}
                  className="bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors duration-200"
                  disabled={loading || !googlePassword}
                >
                  {loading ? 'Restoring...' : 'Restore'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
