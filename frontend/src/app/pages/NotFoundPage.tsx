import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="rounded-xl bg-white p-6 text-center shadow-sm">
        <h1 className="text-2xl font-semibold">Página não encontrada</h1>
        <p className="mt-2 text-sm text-slate-600">A rota solicitada não existe.</p>
        <Link to="/" className="mt-4 inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm text-white">
          Voltar ao dashboard
        </Link>
      </div>
    </div>
  );
}
