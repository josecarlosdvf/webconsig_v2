import type { AuthProvider } from "@refinedev/core";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: {
            name: "LoginError",
            message: error.message || "Credenciais inválidas",
          },
        };
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      return {
        success: true,
        redirectTo: "/",
      };
    } catch (error) {
      return {
        success: false,
        error: {
          name: "LoginError",
          message: "Erro de conexão com o servidor",
        },
      };
    }
  },

  logout: async () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    return {
      success: true,
      redirectTo: "/login",
    };
  },

  check: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      return {
        authenticated: false,
        redirectTo: "/login",
      };
    }

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        return {
          authenticated: false,
          redirectTo: "/login",
        };
      }

      return { authenticated: true };
    } catch {
      return {
        authenticated: false,
        redirectTo: "/login",
      };
    }
  },

  getPermissions: async () => {
    const user = localStorage.getItem("user");
    if (user) {
      const userData = JSON.parse(user);
      return userData.permissions || [];
    }
    return [];
  },

  getIdentity: async () => {
    const user = localStorage.getItem("user");
    if (user) {
      const userData = JSON.parse(user);
      return {
        id: userData.id,
        name: userData.name || userData.username,
        email: userData.email,
        avatar: userData.avatar_url,
      };
    }
    return null;
  },

  onError: async (error) => {
    if (error.status === 401 || error.status === 403) {
      return {
        logout: true,
        redirectTo: "/login",
      };
    }
    return { error };
  },
};
