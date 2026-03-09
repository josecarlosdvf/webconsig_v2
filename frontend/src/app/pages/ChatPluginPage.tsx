import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { usePermission } from "../../features/authz/AccessControlProvider";

type ChatMessage = {
  room: string;
  message: string;
  actor: string;
  created_at: string;
};

export function ChatPluginPage() {
  const [room, setRoom] = useState("geral");
  const [message, setMessage] = useState("");

  const canView = usePermission("ui:/plugins/chat", "view");
  const canSend = usePermission("ui:/plugins/chat/send", "create");

  const pluginsQuery = useQuery({
    queryKey: ["plugins-list"],
    queryFn: async () => (await api.get<{ items: Array<{ slug: string; enabled: boolean }> }>("/plugins")).data.items,
    enabled: Boolean(canView.data),
  });

  const chatPlugin = useMemo(
    () => (pluginsQuery.data ?? []).find((item) => item.slug === "chat-hub"),
    [pluginsQuery.data]
  );

  const messagesQuery = useQuery({
    queryKey: ["chat-plugin", room],
    queryFn: async () => (await api.post<{ items: ChatMessage[]; total: number }>("/plugins/chat/messages/list", { room, limit: 100 })).data,
    enabled: Boolean(canView.data && chatPlugin?.enabled),
    refetchInterval: 5000,
  });

  const sendMutation = useMutation({
    mutationFn: async () => api.post("/plugins/chat/messages", { room, message }),
    onSuccess: async () => {
      setMessage("");
      await messagesQuery.refetch();
    },
  });

  useEffect(() => {
    if (!canView.data) {
      return;
    }
    void messagesQuery.refetch();
  }, [room, canView.data]);

  const items = useMemo(() => messagesQuery.data?.items ?? [], [messagesQuery.data]);

  if (canView.isLoading) {
    return <section className="rounded-xl bg-white p-4 shadow-sm">Carregando permissões...</section>;
  }

  if (!canView.data) {
    return <section className="rounded-xl bg-white p-4 text-sm text-red-600 shadow-sm">Você não possui permissão para acessar o Chat Plugin.</section>;
  }

  if (!chatPlugin) {
    return <section className="rounded-xl bg-white p-4 text-sm text-amber-700 shadow-sm">Plugin `chat-hub` não registrado. Acesse Admin → Permissões para registrar.</section>;
  }

  if (!chatPlugin.enabled) {
    return <section className="rounded-xl bg-white p-4 text-sm text-amber-700 shadow-sm">Plugin `chat-hub` está desabilitado no gerenciamento de plugins.</section>;
  }

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">Plugin • Chat Hub</h2>

      <div className="mb-4 rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
        <div className="grid gap-3 sm:grid-cols-[200px_1fr_auto]">
          <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={room} onChange={(e) => setRoom(e.target.value.toLowerCase())} placeholder="Sala" />
          <input className="rounded border border-slate-300 px-3 py-2 text-sm" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Digite sua mensagem" disabled={!canSend.data} />
          <button
            type="button"
            disabled={!canSend.data || !message.trim() || sendMutation.isPending}
            onClick={() => sendMutation.mutate()}
            className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700 disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
        {!canSend.data ? <p className="mt-2 text-xs text-amber-600">Sem permissão para enviar mensagens.</p> : null}
      </div>

      <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
        <h3 className="mb-2 text-sm font-semibold">Mensagens da sala: {room}</h3>
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li key={`${item.actor}-${item.created_at}-${index}`} className="rounded border border-slate-200 p-2">
              <p className="text-sm text-slate-800 dark:text-slate-100">{item.message}</p>
              <p className="mt-1 text-[11px] text-slate-500">{item.actor} • {new Date(item.created_at).toLocaleString("pt-BR")}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
