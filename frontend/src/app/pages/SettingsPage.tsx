import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import { useUISettings } from "../../features/ui/UISettingsProvider";
import { useAuth } from "../../features/auth/AuthProvider";
import { appResourceCatalog } from "../../features/authz/resourceCatalog";
import { api } from "../../lib/api";

type AccessResource = {
  resource_key: string;
  name: string;
  path: string | null;
  metadata: Record<string, unknown>;
};

type AccessPolicy = {
  priority: string;
  subject: string;
  resource_regex: string;
  action_regex: string;
  effect: "allow" | "deny";
};

export function SettingsPage() {
  const { settings, setTheme, setBrandColor, setMenuMode, setMenuPosition } = useUISettings();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [selectedSubject, setSelectedSubject] = useState(
    user?.role === "admin" ? "role:manager" : `user:${user?.username ?? "anonymous"}`
  );

  const resourcesQuery = useQuery({
    queryKey: ["settings-menu-resources"],
    queryFn: async () => (await api.get<{ items: AccessResource[] }>("/access-control/resources", { params: { resource_type: "menu" } })).data.items,
  });

  const policiesQuery = useQuery({
    queryKey: ["settings-access-policies"],
    queryFn: async () => (await api.get<{ items: AccessPolicy[] }>("/access-control/policies")).data.items,
  });

  const syncUiMutation = useMutation({
    mutationFn: async () => {
      return api.post(
        "/access-control/resources/upsert",
        appResourceCatalog
          .filter((item) => item.resourceType === "menu")
          .map((item) => ({
            resource_key: item.resourceKey,
            resource_type: item.resourceType,
            name: item.name,
            path: item.path ?? null,
            http_method: item.httpMethod ?? null,
            parent_key: item.parentKey ?? null,
            metadata: item.metadata ?? {},
            is_active: item.isActive ?? true,
          }))
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings-menu-resources"] });
    },
  });

  const updateMenuPolicyMutation = useMutation({
    mutationFn: async ({ resource, action, visible }: { resource: string; action: string; visible: boolean }) => {
      const currentPolicies = policiesQuery.data ?? [];
      const matches = currentPolicies.filter(
        (item) => item.subject === selectedSubject && item.resource_regex === resource && item.action_regex === action
      );

      for (const policy of matches) {
        await api.delete("/access-control/policies", { data: policy });
      }

      await api.post("/access-control/policies", {
        priority: visible ? "100" : "90",
        subject: selectedSubject,
        resource_regex: resource,
        action_regex: action,
        effect: visible ? "allow" : "deny",
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings-access-policies"] });
    },
  });

  function policyState(resource: string, action: string): "allow" | "deny" | "inherited" {
    const currentPolicies = policiesQuery.data ?? [];
    const found = currentPolicies.find(
      (item) => item.subject === selectedSubject && item.resource_regex === resource && item.action_regex === action
    );
    if (!found) {
      return "inherited";
    }
    return found.effect;
  }

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">Admin • Configurações</h2>
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">Tema e identidade visual</h3>

          <div className="mb-3">
            <label className="mb-1 block text-sm">Tema</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              value={settings.theme}
              onChange={(e) => setTheme(e.target.value as "light" | "dark")}
            >
              <option value="light">Claro</option>
              <option value="dark">Escuro</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm">Cor primária</label>
            <input
              type="color"
              value={settings.brandColor}
              onChange={(e) => setBrandColor(e.target.value)}
              className="h-10 w-20 rounded border border-slate-300"
            />
          </div>
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">Menu e navegação</h3>

          <div className="mb-3">
            <label className="mb-1 block text-sm">Tipo de menu</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              value={settings.menuMode}
              onChange={(e) => setMenuMode(e.target.value as "sidebar" | "compact" | "top")}
            >
              <option value="sidebar">Lateral completo</option>
              <option value="compact">Lateral compacto</option>
              <option value="top">Superior</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm">Posição do menu</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              value={settings.menuPosition}
              onChange={(e) => setMenuPosition(e.target.value as "left" | "right")}
              disabled={settings.menuMode === "top"}
            >
              <option value="left">Esquerda</option>
              <option value="right">Direita</option>
            </select>
          </div>
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900 xl:col-span-2">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">Gerenciador de Menus por Permissão</h3>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => syncUiMutation.mutate()}
                className="rounded bg-slate-900 px-3 py-1.5 text-xs text-white hover:bg-slate-700"
              >
                Sincronizar menus da UI
              </button>
              <Link to="/admin/permissoes" className="rounded bg-indigo-700 px-3 py-1.5 text-xs text-white hover:bg-indigo-600">
                Abrir tela avançada de permissões
              </Link>
            </div>
          </div>

          <p className="mb-3 text-xs text-slate-600 dark:text-slate-300">
            Editando visibilidade para sujeito:
          </p>
          <input
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="mb-3 w-full max-w-sm rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="role:manager, group:financeiro, user:joao"
          />

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="px-2 py-2">Menu</th>
                  <th className="px-2 py-2">Recurso</th>
                  <th className="px-2 py-2">Estado</th>
                  <th className="px-2 py-2 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {(resourcesQuery.data ?? []).map((item) => {
                  const metadata = item.metadata as { resource?: string; action?: string };
                  const resource = metadata.resource ?? "";
                  const action = metadata.action ?? "view";
                  const state = resource ? policyState(resource, action) : "inherited";

                  return (
                    <tr key={item.resource_key} className="border-b border-slate-100">
                      <td className="px-2 py-2">{item.name}</td>
                      <td className="px-2 py-2 text-xs text-slate-500">{resource || item.resource_key}</td>
                      <td className="px-2 py-2">
                        <span className="rounded bg-slate-100 px-2 py-1 text-xs uppercase">{state}</span>
                      </td>
                      <td className="px-2 py-2 text-right">
                        <div className="inline-flex gap-2">
                          <button
                            type="button"
                            disabled={!resource || updateMenuPolicyMutation.isPending}
                            onClick={() => updateMenuPolicyMutation.mutate({ resource, action, visible: true })}
                            className="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-500 disabled:opacity-50"
                          >
                            Permitir
                          </button>
                          <button
                            type="button"
                            disabled={!resource || updateMenuPolicyMutation.isPending}
                            onClick={() => updateMenuPolicyMutation.mutate({ resource, action, visible: false })}
                            className="rounded bg-rose-600 px-2 py-1 text-xs text-white hover:bg-rose-500 disabled:opacity-50"
                          >
                            Bloquear
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
