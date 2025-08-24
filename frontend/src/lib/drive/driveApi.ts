// frontend/src/lib/drive/driveApi.ts
import { request } from '../api';

// --- Get Google OAuth URL ---
export const getGoogleOAuthUrl = async (walletId: string): Promise<{ url: string }> => {
  const res = await request.get<{ url: string }>(
    `/drive/oauth-url/?wallet_id=${walletId}`,
    { withCredentials: true },
    false // 🚀 disable JWT, use session cookie
  );
  return res.data;
};

// --- Upload Wallet Backup (set backup password) ---
export const uploadWalletBackup = async (
  publicKey: string,
  password: string,
  passwordHint: string = ''
) => {
  const payload = {
    password,        // 🔑 backend expects this field
    password_hint: passwordHint,
  };

  return request.post(
    '/wallet/wallets/set-backup-password/',
    payload,
    {
      headers: { 
        'X-Wallet-Key': publicKey,       // 👈 required by backend
      },
      withCredentials: true,
    },
    true // ✅ enable JWT (required for /wallet/* endpoints)
  );
};

// --- Download Wallet Backup ---
export const downloadWalletBackup = async (publicKey: string) => {
  const res = await request.post(
    '/drive/download/',
    { wallet_id: publicKey },
    {
      headers: { 'X-Wallet-Key': publicKey },
      withCredentials: true,
    },
    true // ✅ needs JWT too
  );
  return res.data;
};
