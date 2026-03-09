type RealtimeEnvelope = {
  event_type: string;
  timestamp: string | null;
  payload: Record<string, unknown>;
};

export type RealtimeCallback = (event: RealtimeEnvelope) => void;

export function createRealtimeClient(callback: RealtimeCallback) {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/api/v1/realtime/ws`);

  socket.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data) as RealtimeEnvelope;
      callback(parsed);
    } catch {
      // ignore malformed payloads
    }
  };

  return socket;
}
