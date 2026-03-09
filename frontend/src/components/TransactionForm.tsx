import { FormEvent, useState } from "react";
import { Button } from "./ui/button";
import { api } from "../lib/api";
import { logFrontend } from "../lib/logger";

type TransactionResponse = {
  id: string;
  external_ref: string;
  status: string;
  amount: string;
  currency: string;
  replayed: boolean;
};

export function TransactionForm() {
  const [externalRef, setExternalRef] = useState("");
  const [customerDocument, setCustomerDocument] = useState("");
  const [amount, setAmount] = useState("");
  const [result, setResult] = useState<TransactionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setResult(null);
    const idemKey = crypto.randomUUID();
    await logFrontend("debug", "Início de criação de transação", { externalRef, idemKey });

    try {
      const response = await api.post<TransactionResponse>(
        "/financial/transactions",
        {
          external_ref: externalRef,
          customer_document: customerDocument,
          amount: Number(amount),
          currency: "BRL"
        },
        {
          headers: {
            "Idempotency-Key": idemKey,
            "X-Actor": "frontend-user"
          }
        }
      );
      setResult(response.data);
      await logFrontend("info", "Transação criada no frontend", {
        externalRef,
        idemKey,
        transactionId: response.data.id
      });
    } catch (error) {
      await logFrontend("error", "Erro ao criar transação", { externalRef, error: String(error) });
      alert("Falha ao criar transação. Veja logs para depuração.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <input
        className="rounded-md border border-slate-300 px-3 py-2"
        placeholder="Referência externa"
        value={externalRef}
        onChange={(e) => setExternalRef(e.target.value)}
        required
      />
      <input
        className="rounded-md border border-slate-300 px-3 py-2"
        placeholder="CPF/CNPJ"
        value={customerDocument}
        onChange={(e) => setCustomerDocument(e.target.value)}
        required
      />
      <input
        className="rounded-md border border-slate-300 px-3 py-2"
        placeholder="Valor"
        type="number"
        min="0.01"
        step="0.01"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        required
      />
      <Button type="submit" disabled={loading}>
        {loading ? "Enviando..." : "Criar transação"}
      </Button>

      {result ? (
        <pre className="rounded bg-slate-900 p-3 text-xs text-green-300">{JSON.stringify(result, null, 2)}</pre>
      ) : null}
    </form>
  );
}
