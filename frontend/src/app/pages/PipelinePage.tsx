const stages = [
  { name: "Novo lead", count: 48 },
  { name: "Qualificação", count: 22 },
  { name: "Proposta", count: 14 },
  { name: "Negociação", count: 9 },
  { name: "Fechado", count: 31 }
];

export function PipelinePage() {
  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">CRM • Pipeline Comercial</h2>
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
        {stages.map((stage) => (
          <div key={stage.name} className="rounded-xl bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-slate-700">{stage.name}</h3>
            <p className="mt-2 text-2xl font-semibold">{stage.count}</p>
            <p className="mt-1 text-xs text-slate-400">oportunidades</p>
          </div>
        ))}
      </div>
    </section>
  );
}
