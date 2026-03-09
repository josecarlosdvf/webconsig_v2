import { BarChart3, BriefcaseBusiness, LayoutDashboard, LogOut, Menu, MessageCircle, Settings, ShieldCheck, Users, X } from "lucide-react";
import { useMemo, useState } from "react";
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
  const { settings, effectiveSettings, viewportPreset } = useUISettings();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isTopMenu = effectiveSettings.menuMode === "top";
  const menuWidth = effectiveSettings.menuMode === "compact" ? "w-20" : "w-72";
  const asideOrder = effectiveSettings.menuPosition === "right" ? "order-2" : "order-1";
  const mainOrder = effectiveSettings.menuPosition === "right" ? "order-1" : "order-2";
  const isAdmin = Boolean(user?.roles?.includes("admin") || user?.role === "admin");
  const isTv = viewportPreset === "tv";

  const permissionItems = useMemo(() => menu.map((item) => ({ resource: item.resource, action: item.action })), []);
  const menuPermissions = useBatchPermissions(permissionItems);
  const visibleMenu = useMemo(
    () => {
      if (!menuPermissions.data) {
        return menu;
      }
      if (isAdmin) {
        return menu;
      }
      return menu.filter((item) => permissionMapLookup(menuPermissions.data, item.resource, item.action));
    },
    [isAdmin, menuPermissions.data]
  );

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
      <div className={cn("mx-auto w-full max-w-screen-2xl px-3 py-3 sm:px-4 lg:px-6 2xl:max-w-[1800px]", isTv && "3xl:max-w-[2200px]")}>
        <header className={cn("mb-4 flex items-center justify-between rounded-2xl bg-white px-3 py-3 shadow-sm transition-all duration-200 dark:bg-slate-900 sm:px-4", isTv && "py-4") }>
          <div className="flex items-center gap-2">
            {!isTopMenu ? (
              <button
                type="button"
                onClick={() => setMobileOpen((current) => !current)}
                className="inline-flex items-center rounded-md border border-slate-300 p-1.5 text-slate-700 lg:hidden"
                aria-label="Alternar menu"
              >
                {mobileOpen ? <X size={16} /> : <Menu size={16} />}
              </button>
            ) : null}
            <div>
            <h2 className={cn("text-lg font-semibold", isTv && "text-2xl")} style={{ color: "var(--brand-color)" }}>Painel Administrativo</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Usuário: {user?.username}</p>
            </div>
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

        {!isTopMenu && mobileOpen ? (
          <div className="mb-4 rounded-2xl bg-slate-900 p-3 text-slate-100 shadow-sm lg:hidden">
            <nav className="space-y-2">
              {visibleMenu.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={`mobile-${item.to}`}
                    to={item.to}
                    onClick={() => setMobileOpen(false)}
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
          </div>
        ) : null}

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
            <aside className={cn("hidden shrink-0 rounded-2xl bg-slate-900 p-4 text-slate-100 shadow-lg transition-all duration-200 lg:block", menuWidth, asideOrder)}>
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
                        effectiveSettings.menuMode === "compact" && "justify-center",
                      isActive ? "bg-slate-100 text-slate-900" : "hover:bg-slate-800"
                    )
                  }
                >
                  <Icon size={16} />
                  {effectiveSettings.menuMode === "compact" ? null : item.label}
                </NavLink>
              );
            })}
          </nav>

          <div className="mt-6 rounded-lg border border-slate-700 p-3 text-xs text-slate-300">
            <p>Layout: {effectiveSettings.menuMode}</p>
            <p>Posição: {effectiveSettings.menuPosition}</p>
            <p>Preset: {settings.presetMode === "custom" ? "custom" : settings.presetMode === "auto" ? viewportPreset : settings.manualPreset}</p>
          </div>
        </aside>
          ) : null}

        <main className={cn("min-w-0 flex-1", mainOrder)}>
          <Outlet />
        </main>
        </div>
      </div>
    </div>
  );
}
