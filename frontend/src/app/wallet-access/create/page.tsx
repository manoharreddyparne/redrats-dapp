'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

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
  useEffect(() => setIsClient(true), []);

  const router = useRouter();
  const [walletName, setWalletName] = useState('');
  const [mnemonic, setMnemonic] = useState('');
  const [createdWallet, setCreatedWallet] = useState<Wallet | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isClient) return null;

  const handleCreateWallet = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await axios.post<CreateWalletResponse>(
        'http://localhost:8000/api/wallet/wallets/',
        { wallet_name: walletName },
        { withCredentials: true }
      );
      setMnemonic(res.data.mnemonic);
      setCreatedWallet(res.data.wallet);
    } catch (err: unknown) {
      console.error(err);
      setError(
        axios.isAxiosError(err)
          ? err.response?.data?.error || 'Failed to create wallet'
          : 'Failed to create wallet'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleEnableBackup = async () => {
    if (!createdWallet) return;

    try {
      // ⚡ Pass wallet public_key directly to backend
      const res = await axios.get<{ url: string }>(
        `http://localhost:8000/api/drive/oauth-url/?wallet_id=${createdWallet.public_key}`,
        { withCredentials: true }
      );

      // Redirect directly to the URL provided by backend
      window.location.href = res.data.url;
    } catch (err) {
      console.error('Failed to initiate Google OAuth', err);
      setError('Failed to start Google backup setup.');
    }
  };

  const handleSkipBackup = () => {
    router.push('/wallets');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Create Wallet</h1>

        {!createdWallet ? (
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
        ) : (
          <div className="space-y-4">
            <div>
              <p className="mb-1 font-medium text-gray-700">Your wallet mnemonic:</p>
              <textarea
                rows={2}
                readOnly
                value={mnemonic}
                className="border p-2 w-full rounded bg-gray-100"
              />
            </div>

            <div className="flex flex-col gap-2">
              <button
                onClick={handleEnableBackup}
                className="w-full bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition-colors duration-200"
              >
                Enable Backup via Google
              </button>
              <button
                onClick={handleSkipBackup}
                className="w-full bg-gray-300 text-black py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors duration-200"
              >
                Skip Backup
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
