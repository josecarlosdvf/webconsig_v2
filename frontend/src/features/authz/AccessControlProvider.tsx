import { ReactNode, createContext, useContext, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";

type BatchAuthorizeItem = { resource: string; action: string };
type BatchAuthorizeResult = { resource: string; action: string; allowed: boolean };

type AccessControlContextType = {
  check: (resource: string, action: string) => Promise<boolean>;
  checkBatch: (items: BatchAuthorizeItem[]) => Promise<Record<string, boolean>>;
};

const AccessControlContext = createContext<AccessControlContextType | undefined>(undefined);

function toKey(resource: string, action: string) {
  return `${resource}::${action}`;
}

export function AccessControlProvider({ children }: { children: ReactNode }) {
  const value = useMemo<AccessControlContextType>(
    () => ({
      check: async (resource: string, action: string) => {
        const response = await api.post<{ allowed: boolean }>("/access-control/authorize", { resource, action });
        return Boolean(response.data.allowed);
      },
      checkBatch: async (items: BatchAuthorizeItem[]) => {
        if (!items.length) {
          return {};
        }

        const response = await api.post<{ items: BatchAuthorizeResult[] }>("/access-control/authorize/batch", { items });
        const mapped: Record<string, boolean> = {};
        for (const item of response.data.items) {
          mapped[toKey(item.resource, item.action)] = item.allowed;
        }
        return mapped;
      },
    }),
    []
  );

  return <AccessControlContext.Provider value={value}>{children}</AccessControlContext.Provider>;
}

export function useAccessControl() {
  const context = useContext(AccessControlContext);
  if (!context) {
    throw new Error("useAccessControl must be used within AccessControlProvider");
  }
  return context;
}

export function usePermission(resource: string, action: string) {
  const { check } = useAccessControl();
  return useQuery({
    queryKey: ["permission", resource, action],
    queryFn: () => check(resource, action),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useBatchPermissions(items: BatchAuthorizeItem[]) {
  const { checkBatch } = useAccessControl();
  return useQuery({
    queryKey: ["permission-batch", items],
    queryFn: () => checkBatch(items),
    staleTime: 30_000,
    retry: 1,
    enabled: items.length > 0,
  });
}

export function permissionMapLookup(map: Record<string, boolean> | undefined, resource: string, action: string): boolean {
  if (!map) {
    return false;
  }
  return Boolean(map[toKey(resource, action)]);
}
