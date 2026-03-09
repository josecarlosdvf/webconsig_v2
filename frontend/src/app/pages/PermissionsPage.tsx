import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { appResourceCatalog } from "../../features/authz/resourceCatalog";
import { usePermission } from "../../features/authz/AccessControlProvider";

type ResourceItem = {
  id: string;
  resource_key: string;
  resource_type: string;
  name: string;
  path: string | null;
  metadata: Record<string, unknown>;
};

type PolicyItem = {
  priority: string;
  subject: string;
  resource_regex: string;
  action_regex: string;
  effect: "allow" | "deny";
};

type GroupItem = {
  subject: string;
  role: string;
};

export function PermissionsPage() {
  const queryClient = useQueryClient();
  const canView = usePermission("ui:/admin/permissoes", "view");
  const canManage = usePermission("ui:/admin/permissoes/manage", "edit");
  const [subject, setSubject] = useState("role:manager");
  const [resourceRegex, setResourceRegex] = useState("ui:/plugins/chat");
  const [actionRegex, setActionRegex] = useState("view");
  const [effect, setEffect] = useState<"allow" | "deny">("allow");

  const [groupSubject, setGroupSubject] = useState("user:manager");
  const [groupRole, setGroupRole] = useState("role:manager");

  const resourcesQuery = useQuery({
    queryKey: ["access-resources"],
    queryFn: async () => (await api.get<{ items: ResourceItem[] }>("/access-control/resources")).data.items,
  });

  const policiesQuery = useQuery({
    queryKey: ["access-policies"],
    queryFn: async () => (await api.get<{ items: PolicyItem[] }>("/access-control/policies")).data.items,
  });

  const groupingQuery = useQuery({
    queryKey: ["access-grouping"],
    queryFn: async () => (await api.get<{ items: GroupItem[] }>("/access-control/grouping")).data.items,
  });

  const discoverPluginsQuery = useQuery({
    queryKey: ["plugins-discover"],
    queryFn: async () => (await api.get<{ items: Array<{ slug: string; name: string; version: string; module_path: string }> }>("/plugins/discover")).data.items,
    enabled: Boolean(canManage.data),
  });

  const syncApiMutation = useMutation({
    mutationFn: async () => api.post("/access-control/resources/sync-api"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["access-resources"] });
    },
  });

  const syncUiMutation = useMutation({
    mutationFn: async () =>
      api.post("/access-control/resources/upsert", appResourceCatalog.map((item) => ({
        resource_key: item.resourceKey,
        resource_type: item.resourceType,
        name: item.name,
        path: item.path ?? null,
        http_method: item.httpMethod ?? null,
        parent_key: item.parentKey ?? null,
        metadata: item.metadata ?? {},
        is_active: item.isActive ?? true,
      }))),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["access-resources"] });
    },
  });

  const addPolicyMutation = useMutation({
    mutationFn: async () =>
      api.post("/access-control/policies", {
        priority: "100",
        subject,
        resource_regex: resourceRegex,
        action_regex: actionRegex,
        effect,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["access-policies"] });
    },
  });

  const addGroupingMutation = useMutation({
    mutationFn: async () => api.post("/access-control/grouping", { subject: groupSubject, role: groupRole }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["access-grouping"] });
    },
  });

  const registerChatPluginMutation = useMutation({
    mutationFn: async () => {
      const chat = (discoverPluginsQuery.data ?? []).find((item) => item.slug === "chat-hub");
      if (!chat) {
        throw new Error("Manifesto do chat-hub não encontrado");
      }
      return api.post("/plugins/register", {
        slug: chat.slug,
        name: chat.name,
        version: chat.version,
        module_path: chat.module_path,
        config: {},
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["access-resources"] });
    },
  });

  const resourceCount = useMemo(() => resourcesQuery.data?.length ?? 0, [resourcesQuery.data]);

  if (canView.isLoading) {
    return <section className="rounded-xl bg-white p-4 shadow-sm">Carregando permissões...</section>;
  }

  if (!canView.data) {
    return <section className="rounded-xl bg-white p-4 text-sm text-red-600 shadow-sm">Você não possui permissão para acessar esta tela.</section>;
  }

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">Admin • Permissões Dinâmicas</h2>

      <div className="mb-4 grid gap-4 lg:grid-cols-3">
        <button
          type="button"
          onClick={() => syncApiMutation.mutate()}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700"
        >
          Sincronizar recursos da API
        </button>
        <button
          type="button"
          onClick={() => syncUiMutation.mutate()}
          disabled={!canManage.data}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700"
        >
          Sincronizar recursos de UI
        </button>
        <button
          type="button"
          onClick={() => registerChatPluginMutation.mutate()}
          disabled={!canManage.data}
          className="rounded-lg bg-indigo-700 px-4 py-2 text-sm text-white hover:bg-indigo-600 disabled:opacity-50"
        >
          Registrar plugin Chat Hub
        </button>
        <div className="rounded-lg bg-white px-4 py-2 text-sm shadow-sm dark:bg-slate-900">Recursos catalogados: {resourceCount}</div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-2 text-sm font-semibold">Nova política</h3>
          <div className="grid gap-2">
            <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="subject (ex: role:manager)" />
            <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={resourceRegex} onChange={(e) => setResourceRegex(e.target.value)} placeholder="resource regex" />
            <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={actionRegex} onChange={(e) => setActionRegex(e.target.value)} placeholder="action regex" />
            <select className="rounded border border-slate-300 px-3 py-2 text-sm" value={effect} onChange={(e) => setEffect(e.target.value as "allow" | "deny")}>
              <option value="allow">allow</option>
              <option value="deny">deny</option>
            </select>
            <button type="button" disabled={!canManage.data} onClick={() => addPolicyMutation.mutate()} className="rounded bg-emerald-600 px-3 py-2 text-sm text-white hover:bg-emerald-500 disabled:opacity-50">
              Adicionar política
            </button>
          </div>
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-2 text-sm font-semibold">Vincular sujeito a papel</h3>
          <div className="grid gap-2">
            <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={groupSubject} onChange={(e) => setGroupSubject(e.target.value)} placeholder="subject (ex: user:joao)" />
            <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={groupRole} onChange={(e) => setGroupRole(e.target.value)} placeholder="role (ex: role:manager)" />
            <button type="button" disabled={!canManage.data} onClick={() => addGroupingMutation.mutate()} className="rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50">
              Adicionar vínculo
            </button>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-2 text-sm font-semibold">Políticas ativas</h3>
          <ul className="space-y-2 text-xs">
            {(policiesQuery.data ?? []).map((item, index) => (
              <li key={`${item.subject}-${item.resource_regex}-${index}`} className="rounded border border-slate-200 p-2">
                <strong>{item.effect.toUpperCase()}</strong> • {item.subject} • {item.resource_regex} • {item.action_regex}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-2 text-sm font-semibold">Agrupamentos</h3>
          <ul className="space-y-2 text-xs">
            {(groupingQuery.data ?? []).map((item, index) => (
              <li key={`${item.subject}-${item.role}-${index}`} className="rounded border border-slate-200 p-2">
                {item.subject} → {item.role}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
