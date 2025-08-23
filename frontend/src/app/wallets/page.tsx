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

  // --- Modal States ---
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [restoreWalletId, setRestoreWalletId] = useState('');
  const [isRestoreOpen, setIsRestoreOpen] = useState(false);
  const [backupWalletId, setBackupWalletId] = useState('');
  const [isBackupOpen, setIsBackupOpen] = useState(false);
  const [driveWalletId, setDriveWalletId] = useState('');
  const [isDriveOpen, setIsDriveOpen] = useState(false);

  // Fetch wallets
  useEffect(() => {
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
    fetchWallets();
  }, []);

  // --- Modal Handlers ---
  const openRestore = (walletId: string) => {
    setRestoreWalletId(walletId);
    setIsRestoreOpen(true);
  };

  const openBackup = (walletId: string) => {
    setBackupWalletId(walletId);
    setIsBackupOpen(true);
  };

  const openDriveModal = (walletId: string) => {
    setDriveWalletId(walletId);
    setIsDriveOpen(true);
  };

  const addWallet = (newWallet: Wallet) => {
    setWallets((prev) => [...prev, newWallet]);
  };

  if (loading) return <p className="text-center mt-10">Loading wallets...</p>;
  if (error) return <p className="text-center mt-10 text-red-500">{error}</p>;

  return (
    <div className="p-6">
      <h2 className="text-2xl mb-4 flex justify-between items-center">
        Your Wallets
        <button
          className="bg-green-500 text-white px-4 py-2 rounded"
          onClick={() => setIsImportOpen(true)}
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
            onRestore={openRestore}
            onSetBackup={openBackup}
            onDrive={openDriveModal}
          />
        ))}
      </div>

      {/* --- Modals --- */}
      <ImportModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        onSuccess={addWallet}
      />

      <RestoreModal
        isOpen={isRestoreOpen}
        walletId={restoreWalletId}
        onClose={() => setIsRestoreOpen(false)}
      />

      <BackupModal
        isOpen={isBackupOpen}
        walletId={backupWalletId}
        onClose={() => setIsBackupOpen(false)}
      />

      <DriveModal
        isOpen={isDriveOpen}
        walletId={driveWalletId}
        onClose={() => setIsDriveOpen(false)}
      />
    </div>
  );
}
