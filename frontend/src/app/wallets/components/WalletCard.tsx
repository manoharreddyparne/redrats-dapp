'use client';

interface WalletCardProps {
  wallet: {
    id: string;
    name: string;
    public_key: string;
    backup_drive_file_id?: string;
  };
  onRestore: (walletId: string) => void;
  onSetBackup: (walletId: string) => void;
  onDrive: (walletId: string) => void;
}

export default function WalletCard({ wallet, onRestore, onSetBackup, onDrive }: WalletCardProps) {
  return (
    <div className="border p-4 rounded shadow hover:shadow-lg transition">
      <h3 className="text-lg font-semibold">{wallet.name}</h3>
      <p className="text-sm text-gray-500">Public Key: {wallet.public_key}</p>

      <div className="flex gap-2 mt-2">
        <button
          className="px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={() => onRestore(wallet.id)}
        >
          Restore
        </button>
        <button
          className="px-2 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
          onClick={() => onSetBackup(wallet.id)}
        >
          Backup Password
        </button>
        <button
          className="px-2 py-1 bg-purple-500 text-white rounded hover:bg-purple-600"
          onClick={() => onDrive(wallet.id)}
        >
          Drive Backup
        </button>
      </div>
    </div>
  );
}
