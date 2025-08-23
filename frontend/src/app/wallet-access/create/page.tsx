'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AxiosError } from 'axios';
import { request } from '@/lib/api';

interface Wallet {
  id: number;
  wallet_name: string;
  public_key: string;
  backup_drive_file_id?: string;
}

interface CreateWalletResponse {
  mnemonic: string;
  wallet: Wallet;
  message?: string;
}

export default function CreateWalletPage() {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const router = useRouter();
  const [walletName, setWalletName] = useState('');
  const [backupPassword, setBackupPassword] = useState('');
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [mnemonic, setMnemonic] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [createdWallet, setCreatedWallet] = useState<Wallet | null>(null);

  if (!isClient) return null; // Avoid SSR hydration issues

  // ---- Step 1: Create Wallet (no JWT required) ----
  const handleCreateWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await request.post<CreateWalletResponse>(
        '/wallets/',
        { wallet_name: walletName },
        undefined,
        false // disable auth for creation
      );

      setMnemonic(res.data.mnemonic);
      setCreatedWallet(res.data.wallet);
      setShowBackupModal(true);
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.error || 'Failed to create wallet');
      } else {
        setError('Failed to create wallet');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // ---- Step 2: Setup optional Google Drive backup ----
  const handleBackup = async () => {
    if (!createdWallet) return;

    setError('');
    setLoading(true);

    try {
      await request.post(
        '/wallets/set-backup-password/',
        { password: backupPassword },
        { headers: { 'X-Wallet-Key': createdWallet.public_key } }
      );

      router.push('/wallets'); // Go to wallet dashboard
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.error || 'Backup setup failed');
      } else {
        setError('Backup setup failed');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Create Wallet</h1>

        <form onSubmit={handleCreateWallet} className="space-y-4">
          <div>
            <label className="block mb-2 font-medium text-gray-700">Wallet Name</label>
            <input
              type="text"
              value={walletName}
              onChange={(e) => setWalletName(e.target.value)}
              className="border p-3 w-full rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Enter wallet name"
              required
            />
          </div>

          {error && <p className="text-red-500">{error}</p>}

          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors duration-200"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Wallet'}
          </button>
        </form>

        {/* ---- Step 3: Backup modal (optional) ---- */}
        {showBackupModal && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50 p-4">
            <div className="bg-white p-6 rounded-xl shadow-lg w-full max-w-sm space-y-4">
              <h2 className="text-xl font-bold text-gray-800">Backup Wallet (Optional)</h2>

              <div>
                <p className="mb-1 font-medium text-gray-700">Your wallet mnemonic:</p>
                <textarea
                  rows={2}
                  readOnly
                  value={mnemonic}
                  className="border p-2 w-full rounded bg-gray-100"
                />
              </div>

              <div>
                <label className="block mb-1 font-medium text-gray-700">
                  Set Backup Password (for Google Drive)
                </label>
                <input
                  type="password"
                  value={backupPassword}
                  onChange={(e) => setBackupPassword(e.target.value)}
                  className="border p-2 w-full rounded"
                  placeholder="Enter password"
                />
              </div>

              {error && <p className="text-red-500">{error}</p>}

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => router.push('/wallets')}
                  className="bg-gray-300 text-black py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors duration-200"
                >
                  Skip Backup
                </button>
                <button
                  onClick={handleBackup}
                  className="bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors duration-200"
                  disabled={loading || !backupPassword}
                >
                  {loading ? 'Backing up...' : 'Backup'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
