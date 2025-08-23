'use client';

import { useRouter } from 'next/navigation';

export default function WalletAccessLanding() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-sm text-center space-y-6">
        <h1 className="text-3xl font-bold text-gray-800">Wallet Access</h1>
        <p className="text-gray-600">Choose an option to get started with your wallet:</p>

        <div className="flex flex-col gap-4">
          <button
            className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors duration-200 font-semibold"
            onClick={() => router.push('/wallet-access/create')}
          >
            Create New Wallet
          </button>

          <button
            className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors duration-200 font-semibold"
            onClick={() => router.push('/wallet-access/import')}
          >
            Import Existing Wallet
          </button>
        </div>

        <p className="text-sm text-gray-500 mt-4">
          New users can create a wallet. Existing users can import using their mnemonic or Google Drive backup.
        </p>
      </div>
    </div>
  );
}
