import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { logFrontend } from "../lib/logger";

type AuditEvent = {
  id: number;
  area: string;
  action: string;
  actor: string;
  request_id: string;
  detail: Record<string, unknown> | unknown[] | string;
  created_at: string;
};

type AuditListResponse = {
  items: AuditEvent[];
  total: number;
};

export function AuditTrail() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAudit() {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<AuditListResponse>("/audit/events", { params: { limit: 50 } });
      setItems(response.data.items);
      await logFrontend("debug", "Auditoria carregada", { total: response.data.total });
    } catch (loadError) {
      setError("Falha ao carregar trilha de auditoria.");
      await logFrontend("error", "Erro ao carregar auditoria", { error: String(loadError) });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAudit();
  }, []);

  if (loading) {
    return <p className="text-sm text-slate-600">Carregando eventos de auditoria...</p>;
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (!items.length) {
    return <p className="text-sm text-slate-600">Sem eventos ainda.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-slate-700">
          <tr>
            <th className="px-3 py-2">Quando</th>
            <th className="px-3 py-2">Área</th>
            <th className="px-3 py-2">Ação</th>
            <th className="px-3 py-2">Ator</th>
            <th className="px-3 py-2">Request ID</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-slate-700">
          {items.map((event) => (
            <tr key={event.id}>
              <td className="whitespace-nowrap px-3 py-2">{new Date(event.created_at).toLocaleString("pt-BR")}</td>
              <td className="px-3 py-2">{event.area}</td>
              <td className="px-3 py-2">{event.action}</td>
              <td className="px-3 py-2">{event.actor}</td>
              <td className="px-3 py-2 font-mono text-xs">{event.request_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
