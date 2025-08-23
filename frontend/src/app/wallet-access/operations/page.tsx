'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { authApi } from '@/lib/auth';
import axios from 'axios';
import { ClipLoader } from 'react-spinners';
import SendPage from './send/page';
import TokenPage from './token/page';
import ContractCallPage from './contract/page';

interface TokenBalance {
  symbol: string;
  balance: string;
}

interface Transaction {
  hash: string;
  type: string;
  amount: string;
  to: string;
  timestamp: string;
}

interface WalletDataResponse {
  avax_balance: string;
  tokens: TokenBalance[];
  transactions: Transaction[];
}

type TabType = 'send' | 'token' | 'contract';

export default function WalletOperationsPage() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab');
  const initialTab: TabType =
    tabParam === 'send' || tabParam === 'token' || tabParam === 'contract'
      ? tabParam
      : 'send';

  const publicKey = searchParams.get('public_key') || '';

  const [activeTab, setActiveTab] = useState<TabType>(initialTab);
  const [avaxBalance, setAvaxBalance] = useState('0');
  const [tokenBalances, setTokenBalances] = useState<TokenBalance[]>([]);
  const [recentTxs, setRecentTxs] = useState<Transaction[]>([]);
  const [fetching, setFetching] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  const [error, setError] = useState('');

  const operations = [
    { key: 'send', title: 'Send AVAX' },
    { key: 'token', title: 'Send Token' },
    { key: 'contract', title: 'Smart Contract Call' },
  ] as const;

  const fetchWalletData = async () => {
    setFetching(true);
    setError('');

    try {
      const res = await authApi.get<WalletDataResponse>('/wallets/wallets/me/');
      setAvaxBalance(res.data.avax_balance || '0');
      setTokenBalances(res.data.tokens || []);
      setRecentTxs(res.data.transactions || []);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || 'Failed to fetch wallet data');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch wallet data');
      }
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    fetchWalletData();
  }, []);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const handleTabChange = (tab: TabType) => {
    setTabLoading(true);
    setActiveTab(tab);
    setTimeout(() => setTabLoading(false), 300); // spinner delay
  };

  return (
    <div className="flex flex-col min-h-screen items-center justify-start bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Wallet Operations</h1>

      {/* Wallet Balances */}
      <div className="bg-white p-6 rounded shadow-md w-full max-w-3xl mb-6">
        <h2 className="text-2xl font-semibold mb-4">Wallet Balances</h2>
        {fetching ? (
          <div className="flex justify-center items-center py-10">
            <ClipLoader size={30} color="#1D4ED8" />
          </div>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          <div>
            <p className="mb-2 flex items-center">
              <strong>AVAX:</strong> {avaxBalance}
              <button
                onClick={() => handleCopy(avaxBalance)}
                className="ml-2 text-blue-500 hover:underline"
              >
                Copy
              </button>
            </p>
            {tokenBalances.length ? (
              <ul className="ml-4 list-disc">
                {tokenBalances.map((t) => (
                  <li key={t.symbol} className="flex items-center">
                    {t.symbol}: {t.balance}
                    <button
                      onClick={() => handleCopy(t.balance)}
                      className="ml-2 text-blue-500 hover:underline"
                    >
                      Copy
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No tokens found.</p>
            )}
          </div>
        )}
      </div>

      {/* Recent Transactions */}
      <div className="bg-white p-6 rounded shadow-md w-full max-w-3xl mb-6 overflow-x-auto">
        <h2 className="text-2xl font-semibold mb-4">Recent Transactions</h2>
        {fetching ? (
          <div className="flex justify-center items-center py-10">
            <ClipLoader size={30} color="#1D4ED8" />
          </div>
        ) : recentTxs.length === 0 ? (
          <p>No recent transactions</p>
        ) : (
          <table className="w-full border-collapse min-w-[600px]">
            <thead>
              <tr>
                <th className="border px-2 py-1 text-left">Type</th>
                <th className="border px-2 py-1 text-left">Amount</th>
                <th className="border px-2 py-1 text-left">To</th>
                <th className="border px-2 py-1 text-left">Hash</th>
                <th className="border px-2 py-1 text-left">Time</th>
              </tr>
            </thead>
            <tbody>
              {recentTxs.map((tx) => (
                <tr key={tx.hash}>
                  <td className="border px-2 py-1">{tx.type}</td>
                  <td className="border px-2 py-1">{tx.amount}</td>
                  <td className="border px-2 py-1">{tx.to}</td>
                  <td className="border px-2 py-1 truncate flex items-center">
                    {tx.hash}
                    <button
                      onClick={() => handleCopy(tx.hash)}
                      className="ml-2 text-blue-500 hover:underline transition-colors duration-150"
                    >
                      Copy
                    </button>
                  </td>
                  <td className="border px-2 py-1">{tx.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-4">
        {operations.map((op) => (
          <button
            key={op.key}
            className={`py-2 px-4 rounded ${
              activeTab === op.key ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
            onClick={() => handleTabChange(op.key)}
          >
            {op.title}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="w-full max-w-3xl">
        {tabLoading ? (
          <div className="flex justify-center items-center py-10">
            <ClipLoader size={30} color="#1D4ED8" />
          </div>
        ) : activeTab === 'send' ? (
          <SendPage publicKey={publicKey} onTransactionSuccess={fetchWalletData} />
        ) : activeTab === 'token' ? (
          <TokenPage publicKey={publicKey} onTransactionSuccess={fetchWalletData} />
        ) : (
          <ContractCallPage publicKey={publicKey} onTransactionSuccess={fetchWalletData} />
        )}
      </div>
    </div>
  );
}
