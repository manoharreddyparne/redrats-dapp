'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/auth';
import { AxiosError } from 'axios';

interface Transaction {
  hash: string;
  from: string;
  to: string;
  value: number;
  timestamp: string;
}

interface WalletData {
  id: number;
  wallet_name: string;
  public_key: string;
  avax_balance: number;
  recent_transactions: Transaction[];
}

export default function WalletDashboardPage() {
  const router = useRouter();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ---- Fetch wallet data ----
  const fetchWallet = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await authApi.get<WalletData>('/wallets/me/');
      setWallet(res.data);
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.error || 'Failed to fetch wallet data');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch wallet data');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWallet();
  }, []);

  // ---- Navigate to operations pages ----
  const goToOperation = (tab: 'send' | 'token' | 'contract') => {
    if (!wallet) return;
    router.push(`/wallet-access/operations?public_key=${wallet.public_key}&tab=${tab}`);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">My Wallet</h1>

      {loading && <p className="text-center text-gray-500">Loading wallet data...</p>}
      {error && <p className="text-center text-red-500">{error}</p>}

      {wallet ? (
        <div className="bg-white p-6 rounded shadow-md">
          <h2 className="text-xl font-semibold mb-2">{wallet.wallet_name}</h2>
          <p className="text-gray-700 mb-1">
            <span className="font-medium">Public Key:</span> {wallet.public_key}
          </p>
          <p className="text-gray-700 mb-3">
            <span className="font-medium">AVAX Balance:</span> {wallet.avax_balance.toFixed(4)} AVAX
          </p>

          {/* Recent Transactions */}
          <div className="mb-3">
            <h3 className="font-medium mb-1">Recent Transactions:</h3>
            {wallet.recent_transactions.length === 0 ? (
              <p className="text-gray-500 text-sm">No transactions yet.</p>
            ) : (
              <ul className="text-gray-700 text-sm max-h-32 overflow-y-auto">
                {wallet.recent_transactions.map((tx) => (
                  <li key={tx.hash} className="mb-1 border-b py-1">
                    <p><span className="font-medium">Hash:</span> {tx.hash.slice(0, 10)}...</p>
                    <p><span className="font-medium">From:</span> {tx.from.slice(0, 6)}...</p>
                    <p><span className="font-medium">To:</span> {tx.to.slice(0, 6)}...</p>
                    <p><span className="font-medium">Value:</span> {tx.value.toFixed(4)} AVAX</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Operations Buttons */}
          <div className="flex justify-between mt-3">
            <button
              onClick={() => goToOperation('send')}
              className="bg-blue-500 text-white py-1 px-3 rounded hover:bg-blue-600"
            >
              Send
            </button>
            <button
              onClick={() => goToOperation('token')}
              className="bg-green-500 text-white py-1 px-3 rounded hover:bg-green-600"
            >
              Swap
            </button>
            <button
              onClick={() => goToOperation('contract')}
              className="bg-purple-500 text-white py-1 px-3 rounded hover:bg-purple-600"
            >
              Contract
            </button>
          </div>
        </div>
      ) : (
        !loading && <p className="text-center text-gray-500">No wallet found.</p>
      )}
    </div>
  );
}
