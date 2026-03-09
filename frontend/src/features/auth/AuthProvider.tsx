import Keycloak from "keycloak-js";
import { ReactNode, createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

type AuthUser = {
  username: string;
  role: string;
  roles: string[];
  groups: string[];
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  isReady: boolean;
  isSsoMode: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);
export const AUTH_STORAGE_KEY = "webconsig_admin_auth";

type StoredAuth = {
  user: AuthUser;
  token: string | null;
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const authMode = (import.meta.env.VITE_AUTH_MODE ?? "local").toLowerCase();
  const isSsoMode = authMode === "keycloak";
  const keycloakRef = useRef<Keycloak | null>(null);

  const [isReady, setIsReady] = useState(!isSsoMode);
  const [user, setUser] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!saved) {
      return null;
    }
    const parsed = JSON.parse(saved) as StoredAuth;
    return parsed.user;
  });
  const [token, setToken] = useState<string | null>(() => {
    const saved = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!saved) {
      return null;
    }
    const parsed = JSON.parse(saved) as StoredAuth;
    return parsed.token;
  });

  function persist(nextUser: AuthUser | null, nextToken: string | null) {
    if (!nextUser) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return;
    }

    const payload: StoredAuth = {
      user: nextUser,
      token: nextToken,
    };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(payload));
  }

  useEffect(() => {
    if (!isSsoMode) {
      return;
    }

    const keycloak = new Keycloak({
      url: import.meta.env.VITE_KEYCLOAK_URL,
      realm: import.meta.env.VITE_KEYCLOAK_REALM,
      clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
    });
    keycloakRef.current = keycloak;

    keycloak
      .init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false })
      .then((authenticated: boolean) => {
        if (!authenticated || !keycloak.tokenParsed) {
          setUser(null);
          setToken(null);
          persist(null, null);
          return;
        }

        const realmRoles = ((keycloak.tokenParsed.realm_access as { roles?: string[] } | undefined)?.roles ?? []).map(String);
        const groups = ((keycloak.tokenParsed.groups as string[] | undefined) ?? []).map((item) => item.replace(/^\//, ""));
        const username = String(keycloak.tokenParsed.preferred_username ?? keycloak.tokenParsed.sub ?? "anonymous");
        const nextUser: AuthUser = {
          username,
          role: realmRoles.includes("admin") ? "admin" : realmRoles[0] ?? "user",
          roles: realmRoles,
          groups,
        };

        setUser(nextUser);
        setToken(keycloak.token ?? null);
        persist(nextUser, keycloak.token ?? null);
      })
      .finally(() => setIsReady(true));

    const refreshHandle = window.setInterval(() => {
      if (!keycloakRef.current?.authenticated) {
        return;
      }
      keycloakRef.current
        .updateToken(60)
        .then(() => {
          setToken(keycloakRef.current?.token ?? null);
          setUser((current) => {
            if (!current) {
              return current;
            }
            persist(current, keycloakRef.current?.token ?? null);
            return current;
          });
        })
        .catch(() => {
          setToken(null);
        });
    }, 30000);

    return () => {
      window.clearInterval(refreshHandle);
    };
  }, [isSsoMode]);

  async function login(username: string, password: string): Promise<boolean> {
    if (isSsoMode && keycloakRef.current) {
      await keycloakRef.current.login();
      return false;
    }

    if (username === "admin" && password === "Admin@123!ChangeMe") {
      const authUser: AuthUser = { username: "admin", role: "admin", roles: ["admin"], groups: [] };
      setUser(authUser);
      setToken(null);
      persist(authUser, null);
      return true;
    }

    return false;
  }

  function logout() {
    if (isSsoMode && keycloakRef.current) {
      void keycloakRef.current.logout({ redirectUri: `${window.location.origin}/login` });
      return;
    }

    setUser(null);
    setToken(null);
    persist(null, null);
  }

  const value = useMemo(() => ({ user, token, isReady, isSsoMode, login, logout }), [user, token, isReady, isSsoMode]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
