'use client';

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import api from '@/lib/api';

interface BackupModalProps {
  isOpen: boolean;
  walletId: string;
  walletName?: string;   // optional for wallet list page
  publicKey?: string;    // optional for create wallet page
  onClose: () => void;
}

export default function BackupModal({
  isOpen,
  walletId,
  walletName,
  onClose,
}: BackupModalProps) {
  const [passwordHint, setPasswordHint] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/wallets/set-backup-password/', {
        wallet_id: walletId,
        password_hint: passwordHint,
      });
      alert('Backup password set successfully!');
      setPasswordHint('');
      setError('');
      onClose();
    } catch {
      setError('Failed to set backup password.');
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded bg-white p-6 shadow-xl transition-all">
                <Dialog.Title className="text-lg font-medium text-gray-900">
                  {walletName
                    ? `Set Backup for "${walletName}"`
                    : 'Set Backup Password'}
                </Dialog.Title>

                <form className="mt-4" onSubmit={handleSubmit}>
                  <input
                    type="text"
                    placeholder="Password Hint"
                    className="border p-2 mb-2 w-full rounded"
                    value={passwordHint}
                    onChange={(e) => setPasswordHint(e.target.value)}
                    required
                  />
                  {error && <p className="text-red-500 mb-2">{error}</p>}
                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      type="button"
                      className="px-4 py-2 bg-gray-300 rounded"
                      onClick={onClose}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-yellow-500 text-white rounded"
                    >
                      Set
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
