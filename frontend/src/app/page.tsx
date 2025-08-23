'use client';

import Link from 'next/link';

export default function HomePage() {
  const portals = [
    {
      title: 'My Wallets',
      description: 'View and manage all your wallets.',
      href: '/wallets',
    },
    {
      title: 'Create Wallet',
      description: 'Generate a new wallet and backup keys securely.',
      href: '/wallet-access/create',
    },
    {
      title: 'Import Wallet',
      description: 'Import an existing wallet using private key or mnemonic.',
      href: '/wallet-access/import',
    },
    {
      title: 'Wallet Operations',
      description: 'Send AVAX, tokens, or interact with smart contracts.',
      href: '/wallet-access/operations',
    },
  ];

  return (
    <div className="flex flex-col min-h-screen items-center justify-start bg-gray-100 p-6">
      <h1 className="text-4xl font-bold mb-8 text-center">RedRats Wallet Portal</h1>
      <p className="text-gray-600 mb-6 text-center max-w-xl">
        Access and manage your wallets, send AVAX or tokens, and interact with smart contracts all in one place.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full max-w-4xl">
        {portals.map((portal) => (
          <Link key={portal.href} href={portal.href}>
            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer">
              <h2 className="text-2xl font-semibold mb-2">{portal.title}</h2>
              <p className="text-gray-600">{portal.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
