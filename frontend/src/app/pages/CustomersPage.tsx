import { useMemo, useState } from "react";

type Customer = {
  id: string;
  nome: string;
  documento: string;
  status: "ativo" | "prospect";
  owner: string;
};

const mockCustomers: Customer[] = [
  { id: "C-001", nome: "Ana Oliveira", documento: "123.456.789-01", status: "ativo", owner: "admin" },
  { id: "C-002", nome: "Carlos Souza", documento: "987.654.321-00", status: "prospect", owner: "admin" },
  { id: "C-003", nome: "Mariana Lima", documento: "111.222.333-44", status: "ativo", owner: "admin" }
];

export function CustomersPage() {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return mockCustomers.filter((item) =>
      `${item.nome} ${item.documento}`.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  return (
    <section>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">CRM • Clientes</h2>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por nome/documento"
          className="w-full max-w-sm rounded-lg border border-slate-300 bg-white px-3 py-2"
        />
      </div>

      <div className="overflow-hidden rounded-xl bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Nome</th>
              <th className="px-4 py-3">Documento</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Responsável</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium">{item.id}</td>
                <td className="px-4 py-3">{item.nome}</td>
                <td className="px-4 py-3">{item.documento}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-1 text-xs ${item.status === "ativo" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                    {item.status}
                  </span>
                </td>
                <td className="px-4 py-3">{item.owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
