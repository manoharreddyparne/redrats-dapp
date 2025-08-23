import { authApi } from '../auth';

export const uploadWalletBackup = async (walletId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('wallet_id', walletId);

  return authApi.post<{ success: boolean }>('/drive/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const downloadWalletBackup = async (walletId: string) => {
  const token = localStorage.getItem('redrats_jwt');
  const res = await fetch(`http://localhost:8000/api/drive/download/`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ wallet_id: walletId }),
  });

  if (!res.ok) throw new Error('Download failed');
  const blob = await res.blob();
  return blob;
};
