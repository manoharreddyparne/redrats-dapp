// src/app/wallet-access/test-landing/page.tsx
'use client';

import Link from 'next/link';

export default function WalletAccessTestLanding() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-sm text-center">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Wallet Access Test</h1>
        <p className="mb-6 text-gray-600">Quick test: choose an option:</p>
        <div className="flex flex-col space-y-4">
          <Link
            href="/wallet-access/create"
            className="block bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors duration-200"
          >
            Test Create New Wallet
          </Link>
          <Link
            href="/wallet-access/import"
            className="block bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors duration-200"
          >
            Test Import Existing Wallet
          </Link>
        </div>
      </div>
    </div>
  );
}
