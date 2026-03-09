import { api } from "./api";

type Level = "debug" | "info" | "warn" | "error";

export async function logFrontend(level: Level, message: string, context: Record<string, unknown> = {}) {
  const payload = { level, message, context };
  const fn = level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  fn(`[frontend:${level}]`, message, context);

  try {
    await api.post("/debug/frontend-log", payload, {
      headers: {
        "X-Actor": "frontend-ui"
      }
    });
  } catch (error) {
    console.warn("Falha ao enviar log para backend", error);
  }
}
