import { FormEvent, useEffect, useMemo, useState } from "react";
import { Button } from "./ui/button";
import { api } from "../lib/api";
import { logFrontend } from "../lib/logger";

type Plugin = {
  id: number;
  slug: string;
  name: string;
  version: string;
  module_path: string;
  enabled: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type PluginListResponse = {
  items: Plugin[];
  total: number;
};

type DiscoverManifest = {
  slug: string;
  name: string;
  version: string;
  module_path: string;
};

type DiscoverResponse = {
  items: DiscoverManifest[];
  total: number;
};

type TaskLog = {
  id: number;
  plugin_id: number;
  plugin_slug: string;
  actor: string;
  task: string;
  success: boolean;
  request_id: string;
  payload: Record<string, unknown> | unknown[] | string;
  result: Record<string, unknown> | unknown[] | string;
  error?: string | null;
  created_at: string;
};

type TaskLogListResponse = {
  items: TaskLog[];
  total: number;
};

export function PluginManager() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPluginId, setSelectedPluginId] = useState<number | null>(null);
  const [task, setTask] = useState("health");
  const [payloadText, setPayloadText] = useState("{}");
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);
  const [logs, setLogs] = useState<TaskLog[]>([]);

  const selectedPlugin = useMemo(
    () => plugins.find((plugin) => plugin.id === selectedPluginId) ?? null,
    [plugins, selectedPluginId]
  );

  async function loadPlugins() {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<PluginListResponse>("/plugins");
      setPlugins(response.data.items);
      if (!selectedPluginId && response.data.items.length) {
        setSelectedPluginId(response.data.items[0].id);
      }
      await logFrontend("debug", "Plugins carregados", { total: response.data.total });
    } catch (loadError) {
      setError("Falha ao carregar plugins.");
      await logFrontend("error", "Erro ao carregar plugins", { error: String(loadError) });
    } finally {
      setLoading(false);
    }
  }

  async function discoverAndRegister() {
    setDiscovering(true);
    setError(null);
    try {
      const discover = await api.get<DiscoverResponse>("/plugins/discover");
      const existing = new Set(plugins.map((plugin) => plugin.slug));

      for (const manifest of discover.data.items) {
        if (existing.has(manifest.slug)) {
          continue;
        }
        await api.post("/plugins/register", {
          slug: manifest.slug,
          name: manifest.name,
          version: manifest.version,
          module_path: manifest.module_path,
          config: {}
        });
      }

      await loadPlugins();
      await logFrontend("info", "Descoberta de plugins concluída", { found: discover.data.total });
    } catch (discoverError) {
      setError("Falha ao descobrir/registrar plugins locais.");
      await logFrontend("error", "Erro na descoberta de plugins", { error: String(discoverError) });
    } finally {
      setDiscovering(false);
    }
  }

  async function togglePlugin(plugin: Plugin) {
    try {
      await api.patch(`/plugins/${plugin.id}/state`, { enabled: !plugin.enabled });
      await loadPlugins();
      await logFrontend("info", "Estado de plugin alterado", { plugin: plugin.slug, enabled: !plugin.enabled });
    } catch (toggleError) {
      setError("Falha ao alterar estado do plugin.");
      await logFrontend("error", "Erro ao alterar estado do plugin", { error: String(toggleError), plugin: plugin.slug });
    }
  }

  async function loadLogs(pluginId: number) {
    try {
      const response = await api.get<TaskLogListResponse>(`/plugins/${pluginId}/tasks/logs`, {
        params: { limit: 30 }
      });
      setLogs(response.data.items);
    } catch (logError) {
      await logFrontend("warn", "Falha ao carregar logs de plugin", { error: String(logError), pluginId });
    }
  }

  async function runTask(event: FormEvent) {
    event.preventDefault();
    if (!selectedPlugin) {
      return;
    }

    let payload: Record<string, unknown> = {};
    try {
      payload = JSON.parse(payloadText) as Record<string, unknown>;
    } catch {
      setError("Payload JSON inválido.");
      return;
    }

    try {
      const response = await api.post(`/plugins/${selectedPlugin.id}/tasks/run`, { task, payload });
      setLastResult(response.data);
      await loadLogs(selectedPlugin.id);
      await logFrontend("info", "Tarefa de plugin executada", {
        plugin: selectedPlugin.slug,
        task,
        success: response.data?.success
      });
    } catch (runError) {
      setError("Falha ao executar tarefa do plugin.");
      await logFrontend("error", "Erro ao executar tarefa de plugin", {
        error: String(runError),
        plugin: selectedPlugin.slug,
        task
      });
    }
  }

  useEffect(() => {
    void loadPlugins();
  }, []);

  useEffect(() => {
    if (selectedPluginId) {
      void loadLogs(selectedPluginId);
    }
  }, [selectedPluginId]);

  if (loading) {
    return <p className="text-sm text-slate-600">Carregando plugins...</p>;
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" onClick={discoverAndRegister} disabled={discovering}>
          {discovering ? "Descobrindo..." : "Descobrir plugins locais"}
        </Button>
        {error ? <span className="text-sm text-red-600">{error}</span> : null}
      </div>

      {!plugins.length ? (
        <p className="text-sm text-slate-600">Nenhum plugin registrado.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 p-3">
            <h3 className="mb-2 text-sm font-semibold text-slate-800">Plugins</h3>
            <ul className="space-y-2">
              {plugins.map((plugin) => (
                <li key={plugin.id} className="rounded border border-slate-200 p-2">
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedPluginId(plugin.id)}
                      className={`text-left text-sm ${selectedPluginId === plugin.id ? "font-semibold text-slate-900" : "text-slate-700"}`}
                    >
                      {plugin.name} ({plugin.slug})
                    </button>
                    <Button type="button" onClick={() => togglePlugin(plugin)}>
                      {plugin.enabled ? "Desabilitar" : "Habilitar"}
                    </Button>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">v{plugin.version} · {plugin.module_path}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3 rounded-lg border border-slate-200 p-3">
            <h3 className="text-sm font-semibold text-slate-800">Execução de tarefa</h3>
            {selectedPlugin ? (
              <form onSubmit={runTask} className="space-y-2">
                <input
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  placeholder="Task (ex: health, echo)"
                  required
                />
                <textarea
                  className="h-24 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs"
                  value={payloadText}
                  onChange={(e) => setPayloadText(e.target.value)}
                />
                <Button type="submit">Executar</Button>
              </form>
            ) : (
              <p className="text-sm text-slate-600">Selecione um plugin.</p>
            )}

            {lastResult ? (
              <pre className="rounded bg-slate-900 p-3 text-xs text-emerald-300">{JSON.stringify(lastResult, null, 2)}</pre>
            ) : null}
          </div>
        </div>
      )}

      {selectedPlugin ? (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-700">
              <tr>
                <th className="px-3 py-2">Quando</th>
                <th className="px-3 py-2">Task</th>
                <th className="px-3 py-2">Sucesso</th>
                <th className="px-3 py-2">Ator</th>
                <th className="px-3 py-2">Request ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="whitespace-nowrap px-3 py-2">{new Date(log.created_at).toLocaleString("pt-BR")}</td>
                  <td className="px-3 py-2">{log.task}</td>
                  <td className="px-3 py-2">{log.success ? "OK" : "ERRO"}</td>
                  <td className="px-3 py-2">{log.actor}</td>
                  <td className="px-3 py-2 font-mono text-xs">{log.request_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
