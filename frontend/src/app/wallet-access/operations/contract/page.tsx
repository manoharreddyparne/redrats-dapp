'use client';

import { useState } from "react";
import { authApi } from "@/lib/auth";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import Input from '../components/Input';
import Textarea from '../components/Textarea';
import Button from '../components/Button';

interface ContractCallResponse {
  tx_hash: string;
}

interface ContractCallProps {
  publicKey: string;
  onTransactionSuccess?: () => void;
}

export default function ContractCallPage({ publicKey, onTransactionSuccess }: ContractCallProps) {
  const [contractAddress, setContractAddress] = useState("");
  const [abi, setAbi] = useState("");
  const [functionName, setFunctionName] = useState("");
  const [args, setArgs] = useState("");
  const [valueEther, setValueEther] = useState("");
  const [txHash, setTxHash] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isValidAddress = (addr: string) => /^0x[a-fA-F0-9]{40}$/.test(addr);

  const handleContractCall = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setTxHash("");

    if (!isValidAddress(contractAddress)) {
      setError("Invalid contract address");
      return;
    }

    let parsedAbi: unknown;
    let parsedArgs: unknown[] = [];

    try {
      parsedAbi = JSON.parse(abi);
    } catch {
      setError("Invalid ABI JSON");
      return;
    }

    if (args) {
      try {
        parsedArgs = JSON.parse(args);
        if (!Array.isArray(parsedArgs)) {
          setError("Arguments must be an array");
          return;
        }
      } catch {
        setError("Invalid arguments JSON");
        return;
      }
    }

    setLoading(true);

    try {
      const res = await authApi.post<ContractCallResponse>("/wallets/contract-call/", {
        contract_address: contractAddress,
        abi: parsedAbi,
        function_name: functionName,
        args: parsedArgs,
        value_ether: parseFloat(valueEther || "0")
      });

      setTxHash(res.data.tx_hash);
      toast.success("Contract called successfully!");

      if (onTransactionSuccess) onTransactionSuccess();

    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || "Contract call failed");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Contract call failed");
      }
      toast.error(error || "Contract call failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <Toaster position="top-right" />
      <form onSubmit={handleContractCall} className="bg-white p-6 rounded shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">Smart Contract Call</h1>
        <p className="mb-3 text-gray-500">From wallet: {publicKey}</p>

        <Input
          type="text"
          placeholder="Contract address"
          value={contractAddress}
          onChange={e => setContractAddress(e.target.value)}
          required
        />

        <Textarea
          placeholder="ABI JSON"
          value={abi}
          onChange={e => setAbi(e.target.value)}
          required
        />

        <Input
          type="text"
          placeholder="Function name"
          value={functionName}
          onChange={e => setFunctionName(e.target.value)}
          required
        />

        <Textarea
          placeholder="Arguments JSON"
          value={args}
          onChange={e => setArgs(e.target.value)}
        />

        <Input
          type="number"
          placeholder="Value in AVAX"
          value={valueEther}
          onChange={e => setValueEther(e.target.value)}
        />

        {error && <p className="text-red-500 mb-3">{error}</p>}
        {txHash && <p className="text-green-500 mb-3">Tx Hash: {txHash}</p>}

        <Button type="submit" disabled={loading}>
          {loading ? "Calling..." : "Call Contract"}
        </Button>
      </form>
    </div>
  );
}
