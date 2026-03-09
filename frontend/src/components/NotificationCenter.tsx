import { Bell, CheckCheck, Circle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../features/auth/AuthProvider";
import { api } from "../lib/api";

type NotificationItem = {
  id: string;
  title: string;
  message: string;
  sender: string;
  recipient: string;
  category: string;
  metadata: Record<string, unknown>;
  created_at: string;
  read_at: string | null;
  is_read: boolean;
};

type NotificationListResponse = {
  items: NotificationItem[];
  total: number;
  unread_total: number;
};

export function NotificationCenter() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unreadTotal, setUnreadTotal] = useState(0);

  async function loadNotifications() {
    const response = await api.get<NotificationListResponse>("/notifications", { params: { limit: 30 } });
    setItems(response.data.items);
    setUnreadTotal(response.data.unread_total);
  }

  async function markRead(id: string) {
    await api.patch(`/notifications/${id}/read`);
    await loadNotifications();
  }

  async function markAllRead() {
    await api.patch("/notifications/read-all");
    await loadNotifications();
  }

  useEffect(() => {
    void loadNotifications();
  }, []);

  useEffect(() => {
    if (!user) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/api/v1/notifications/ws?actor=${encodeURIComponent(user.username)}`);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as NotificationItem | { event_type: string };
        if ("event_type" in payload) {
          return;
        }
        setItems((current) => [payload, ...current].slice(0, 30));
        setUnreadTotal((current) => current + 1);
      } catch {
        // ignore malformed payloads
      }
    };

    return () => socket.close();
  }, [user]);

  const recent = useMemo(() => items.slice(0, 8), [items]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="relative rounded-full border border-slate-200 bg-white p-2 text-slate-700 hover:bg-slate-50"
      >
        <Bell size={18} />
        {unreadTotal > 0 ? (
          <span className="absolute -right-1 -top-1 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
            {unreadTotal > 99 ? "99+" : unreadTotal}
          </span>
        ) : null}
      </button>

      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-[360px] rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Notificações</h3>
            <button type="button" className="text-xs text-slate-500 hover:text-slate-700" onClick={markAllRead}>
              <span className="inline-flex items-center gap-1"><CheckCheck size={14} /> Marcar todas como lidas</span>
            </button>
          </div>

          {!recent.length ? (
            <p className="text-sm text-slate-500">Sem notificações.</p>
          ) : (
            <ul className="space-y-2">
              {recent.map((item) => (
                <li key={item.id} className="rounded-lg border border-slate-100 p-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-slate-800">{item.title}</p>
                      <p className="mt-1 text-xs text-slate-600">{item.message}</p>
                      <p className="mt-1 text-[11px] text-slate-400">De: {item.sender} • {new Date(item.created_at).toLocaleString("pt-BR")}</p>
                    </div>
                    {!item.is_read ? <Circle className="mt-1 text-emerald-500" size={10} fill="currentColor" /> : null}
                  </div>
                  {!item.is_read ? (
                    <button type="button" className="mt-2 rounded bg-slate-100 px-2 py-1 text-xs text-slate-700 hover:bg-slate-200" onClick={() => markRead(item.id)}>
                      Marcar como lida
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}
