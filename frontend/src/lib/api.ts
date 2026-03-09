import axios from "axios";
import { AUTH_STORAGE_KEY } from "../features/auth/AuthProvider";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api/v1",
  timeout: 15000
});

api.interceptors.request.use((config) => {
  const saved = localStorage.getItem(AUTH_STORAGE_KEY);
  if (saved) {
    const parsed = JSON.parse(saved) as { user?: { username?: string }; token?: string | null };
    if (parsed.user?.username && !config.headers["X-Actor"]) {
      config.headers["X-Actor"] = parsed.user.username;
    }
    if (parsed.token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${parsed.token}`;
    }
  }
  return config;
});
