'use client';

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { uploadWalletBackup, downloadWalletBackup } from '@/lib/drive/driveApi';

interface DriveModalProps {
  isOpen: boolean;
  walletId: string;
  onClose: () => void;
}

export default function DriveModal({ isOpen, walletId, onClose }: DriveModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');

  const handleUpload = async () => {
    if (!file) return setError('Select a file first.');
    try {
      await uploadWalletBackup(walletId, file);
      alert('Backup uploaded successfully!');
      setFile(null);
      setError('');
      onClose();
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to upload backup.');
    }
  };

  const handleDownload = async () => {
    try {
      const res = await downloadWalletBackup(walletId);
      const blob = new Blob([res.data as BlobPart]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `wallet-${walletId}.backup`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to download backup.');
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
                  Wallet Backup
                </Dialog.Title>

                <div className="mt-4 flex flex-col gap-2">
                  <input
                    type="file"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                  {error && <p className="text-red-500">{error}</p>}
                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      type="button"
                      className="px-4 py-2 bg-gray-300 rounded"
                      onClick={onClose}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="px-4 py-2 bg-blue-500 text-white rounded"
                      onClick={handleUpload}
                    >
                      Upload
                    </button>
                    <button
                      type="button"
                      className="px-4 py-2 bg-green-500 text-white rounded"
                      onClick={handleDownload}
                    >
                      Download
                    </button>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
