import { BarChart3, BriefcaseBusiness, LayoutDashboard, LogOut, MessageCircle, Settings, ShieldCheck, Users } from "lucide-react";
import { useMemo } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { NotificationCenter } from "../../components/NotificationCenter";
import { useAuth } from "../../features/auth/AuthProvider";
import { permissionMapLookup, useBatchPermissions } from "../../features/authz/AccessControlProvider";
import { useUISettings } from "../../features/ui/UISettingsProvider";
import { cn } from "../../lib/utils";

const menu = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, resource: "ui:/dashboard", action: "view" },
  { to: "/crm/clientes", label: "Clientes", icon: Users, resource: "ui:/crm/clientes", action: "view" },
  { to: "/crm/pipeline", label: "Pipeline", icon: BriefcaseBusiness, resource: "ui:/crm/pipeline", action: "view" },
  { to: "/erp/financeiro", label: "Financeiro", icon: BarChart3, resource: "ui:/erp/financeiro", action: "view" },
  { to: "/plugins/chat", label: "Chat", icon: MessageCircle, resource: "ui:/plugins/chat", action: "view" },
  { to: "/admin/permissoes", label: "Permissões", icon: ShieldCheck, resource: "ui:/admin/permissoes", action: "view" },
  { to: "/admin/configuracoes", label: "Configurações", icon: Settings, resource: "ui:/admin/configuracoes", action: "view" }
];

export function AdminLayout() {
  const { user, logout } = useAuth();
  const { settings } = useUISettings();

  const isTopMenu = settings.menuMode === "top";
  const menuWidth = settings.menuMode === "compact" ? "w-20" : "w-72";
  const asideOrder = settings.menuPosition === "right" ? "order-2" : "order-1";
  const mainOrder = settings.menuPosition === "right" ? "order-1" : "order-2";

  const permissionItems = useMemo(() => menu.map((item) => ({ resource: item.resource, action: item.action })), []);
  const menuPermissions = useBatchPermissions(permissionItems);
  const visibleMenu = useMemo(
    () => {
      if (!menuPermissions.data) {
        return menu;
      }
      return menu.filter((item) => permissionMapLookup(menuPermissions.data, item.resource, item.action));
    },
    [menuPermissions.data]
  );

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-7xl p-4 lg:p-6">
        <header className="mb-4 flex items-center justify-between rounded-2xl bg-white px-4 py-3 shadow-sm dark:bg-slate-900">
          <div>
            <h2 className="text-lg font-semibold" style={{ color: "var(--brand-color)" }}>Painel Administrativo</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Usuário: {user?.username}</p>
          </div>
          <div className="flex items-center gap-3">
            <NotificationCenter />
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-md bg-red-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-400"
              onClick={logout}
            >
              <LogOut size={14} />
              Sair
            </button>
          </div>
        </header>

        {isTopMenu ? (
          <nav className="mb-4 flex flex-wrap gap-2 rounded-2xl bg-slate-900 p-3 text-slate-100 shadow-sm">
            {visibleMenu.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm transition",
                      isActive ? "bg-white text-slate-900" : "hover:bg-slate-800"
                    )
                  }
                >
                  <Icon size={16} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        ) : null}

        <div className="flex gap-4">
          {!isTopMenu ? (
            <aside className={cn("hidden shrink-0 rounded-2xl bg-slate-900 p-4 text-slate-100 shadow-lg lg:block", menuWidth, asideOrder)}>
          <h1 className="mb-5 text-lg font-semibold">Webconsig Admin</h1>
          <nav className="space-y-2">
            {visibleMenu.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition",
                      settings.menuMode === "compact" && "justify-center",
                      isActive ? "bg-slate-100 text-slate-900" : "hover:bg-slate-800"
                    )
                  }
                >
                  <Icon size={16} />
                  {settings.menuMode === "compact" ? null : item.label}
                </NavLink>
              );
            })}
          </nav>

          <div className="mt-6 rounded-lg border border-slate-700 p-3 text-xs text-slate-300">
            <p>Layout: {settings.menuMode}</p>
            <p>Posição: {settings.menuPosition}</p>
          </div>
        </aside>
          ) : null}

        <main className={cn("flex-1", mainOrder)}>
          <Outlet />
        </main>
        </div>
      </div>
    </div>
  );
}
