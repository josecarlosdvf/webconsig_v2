import { BarChart3, BriefcaseBusiness, LayoutDashboard, LogOut, Settings, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import { cn } from "../../lib/utils";

const menu = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/crm/clientes", label: "Clientes", icon: Users },
  { to: "/crm/pipeline", label: "Pipeline", icon: BriefcaseBusiness },
  { to: "/erp/financeiro", label: "Financeiro", icon: BarChart3 },
  { to: "/admin/configuracoes", label: "Configurações", icon: Settings }
];

export function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto flex max-w-7xl gap-4 p-4 lg:p-6">
        <aside className="hidden w-72 shrink-0 rounded-2xl bg-slate-900 p-4 text-slate-100 shadow-lg lg:block">
          <h1 className="mb-5 text-lg font-semibold">Webconsig Admin</h1>
          <nav className="space-y-2">
            {menu.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition",
                      isActive ? "bg-slate-100 text-slate-900" : "hover:bg-slate-800"
                    )
                  }
                >
                  <Icon size={16} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          <div className="mt-6 rounded-lg border border-slate-700 p-3 text-xs text-slate-300">
            <p>Usuário: {user?.username}</p>
            <button
              type="button"
              className="mt-3 inline-flex items-center gap-2 rounded-md bg-red-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-400"
              onClick={logout}
            >
              <LogOut size={14} />
              Sair
            </button>
          </div>
        </aside>

        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
