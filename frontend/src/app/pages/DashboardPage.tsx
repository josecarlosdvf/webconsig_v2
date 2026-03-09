import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

function MetricCard({ title, value, hint }: { title: string; value: string; hint: string }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{hint}</p>
    </div>
  );
}

export function DashboardPage() {
  const { data: auditSummary } = useQuery({
    queryKey: ["audit-summary"],
    queryFn: async () => (await api.get("/audit/summary")).data,
    refetchInterval: 15000
  });

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">Dashboard Executivo</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Eventos" value={String(auditSummary?.total ?? 0)} hint="Auditoria total" />
        <MetricCard title="Clientes ativos" value="1.284" hint="Base CRM" />
        <MetricCard title="Propostas abertas" value="312" hint="Pipeline" />
        <MetricCard title="Conversão" value="24.8%" hint="Últimos 30 dias" />
      </div>

      <div className="mt-4 rounded-xl bg-white p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-800">Resumo de operação</h3>
        <p className="mt-2 text-sm text-slate-600">Plataforma pronta para evolução de módulos administrativos, CRM e ERP com arquitetura modular.</p>
      </div>
    </section>
  );
}
