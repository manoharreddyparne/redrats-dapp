'use client';

import { useEffect, useState } from 'react';
import { authApi, logout } from '@/lib/auth';
import WalletCard from './components/WalletCard';
import ImportModal from './components/ImportModal';
import RestoreModal from './components/RestoreModal';
import BackupModal from './components/BackupModal';
import DriveModal from './components/DriveModal';

interface Wallet {
  id: string;
  name: string;
  public_key: string;
  backup_drive_file_id?: string;
}

export default function WalletsPage() {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [modals, setModals] = useState({
    import: false,
    restore: { open: false, walletId: '' },
    backup: { open: false, walletId: '' },
    drive: { open: false, walletId: '' }
  });

  const fetchWallets = async () => {
    try {
      const res = await authApi.get<Wallet[]>('/wallets/me/');
      setWallets(res.data);
    } catch {
      setError('Failed to fetch wallets. Please login again.');
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWallets();
  }, []);

  const openModal = (type: 'restore' | 'backup' | 'drive', walletId: string) => {
    setModals((prev) => ({
      ...prev,
      [type]: { open: true, walletId }
    }));
  };

  const closeModal = (type: 'restore' | 'backup' | 'drive' | 'import') => {
    if (type === 'import') setModals((prev) => ({ ...prev, import: false }));
    else setModals((prev) => ({ ...prev, [type]: { open: false, walletId: '' } }));
  };

  const addWallet = (newWallet: Wallet) => setWallets((prev) => [...prev, newWallet]);

  if (loading) return <p className="text-center mt-10">Loading wallets...</p>;
  if (error) return <p className="text-center mt-10 text-red-500">{error}</p>;

  return (
    <div className="p-6">
      <h2 className="text-2xl mb-4 flex justify-between items-center">
        Your Wallets
        <button
          className="bg-green-500 text-white px-4 py-2 rounded"
          onClick={() => setModals((prev) => ({ ...prev, import: true }))}
        >
          Import Wallet
        </button>
      </h2>

      {wallets.length === 0 && <p>No wallets found.</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {wallets.map((wallet) => (
          <WalletCard
            key={wallet.id}
            wallet={wallet}
            onRestore={(id) => openModal('restore', id)}
            onSetBackup={(id) => openModal('backup', id)}
            onDrive={(id) => openModal('drive', id)}
          />
        ))}
      </div>

      <ImportModal
        isOpen={modals.import}
        onClose={() => closeModal('import')}
        onSuccess={addWallet}
      />
      <RestoreModal
        isOpen={modals.restore.open}
        walletId={modals.restore.walletId}
        onClose={() => closeModal('restore')}
      />
      <BackupModal
        isOpen={modals.backup.open}
        walletId={modals.backup.walletId}
        onClose={() => closeModal('backup')}
      />
      <DriveModal
        isOpen={modals.drive.open}
        walletId={modals.drive.walletId}
        onClose={() => closeModal('drive')}
      />
    </div>
  );
}
