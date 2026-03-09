import { useEffect, useState } from "react";
import { createRealtimeClient } from "../lib/realtime";

type FeedEvent = {
  event_type: string;
  timestamp: string | null;
  payload: Record<string, unknown>;
};

export function RealtimeFeed() {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  useEffect(() => {
    const socket = createRealtimeClient((event) => {
      if (event.event_type === "system.heartbeat") {
        return;
      }

      setEvents((current) => [event, ...current].slice(0, 20));
    });

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("disconnected");
    socket.onerror = () => setStatus("disconnected");

    return () => {
      socket.close();
    };
  }, []);

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Eventos em tempo real</h3>
        <span
          className={`rounded-full px-2 py-1 text-xs ${
            status === "connected"
              ? "bg-emerald-100 text-emerald-700"
              : status === "connecting"
                ? "bg-amber-100 text-amber-700"
                : "bg-red-100 text-red-700"
          }`}
        >
          {status}
        </span>
      </div>

      {!events.length ? (
        <p className="text-sm text-slate-500">Aguardando eventos...</p>
      ) : (
        <ul className="space-y-2">
          {events.map((event, idx) => (
            <li key={`${event.event_type}-${idx}`} className="rounded-lg border border-slate-100 px-3 py-2 text-sm">
              <p className="font-medium text-slate-800">{event.event_type}</p>
              <p className="text-xs text-slate-500">{event.timestamp ?? "agora"}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
