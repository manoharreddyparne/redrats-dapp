'use client';

import { useState } from "react";
import { authApi } from "@/lib/auth";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import Input from '../components/Input';
import Button from '../components/Button';


interface SendTokenResponse {
  tx_hash: string;
}

interface TokenProps {
  publicKey: string;
  onTransactionSuccess?: () => void;
}

export default function TokenPage({ publicKey, onTransactionSuccess }: TokenProps) {
  const [tokenAddress, setTokenAddress] = useState("");
  const [toAddress, setToAddress] = useState("");
  const [amount, setAmount] = useState("");
  const [txHash, setTxHash] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isValidAddress = (addr: string) => /^0x[a-fA-F0-9]{40}$/.test(addr);

  const handleSendToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setTxHash("");

    if (!isValidAddress(tokenAddress)) {
      setError("Invalid token contract address");
      return;
    }
    if (!isValidAddress(toAddress)) {
      setError("Invalid recipient address");
      return;
    }

    setLoading(true);

    try {
      const res = await authApi.post<SendTokenResponse>("/wallets/send-token/", {
        token_address: tokenAddress,
        to_address: toAddress,
        amount: parseFloat(amount)
      });

      setTxHash(res.data.tx_hash);
      toast.success("Token sent successfully!");

      if (onTransactionSuccess) onTransactionSuccess();

    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || "Token send failed");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Token send failed");
      }
      toast.error(error || "Token send failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <Toaster position="top-right" />
      <form onSubmit={handleSendToken} className="bg-white p-6 rounded shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">Send Token</h1>
        <p className="mb-3 text-gray-500">From wallet: {publicKey}</p>

        <Input
          type="text"
          placeholder="Token contract address"
          value={tokenAddress}
          onChange={e => setTokenAddress(e.target.value)}
          required
        />

        <Input
          type="text"
          placeholder="Recipient address"
          value={toAddress}
          onChange={e => setToAddress(e.target.value)}
          required
        />

        <Input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          required
        />

        {error && <p className="text-red-500 mb-3">{error}</p>}
        {txHash && <p className="text-green-500 mb-3">Tx Hash: {txHash}</p>}

        <Button type="submit" disabled={loading} loading={loading}>
          Send Token
        </Button>
      </form>
    </div>
  );
}
