import { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../features/auth/AuthProvider";
import { AccessControlProvider } from "../features/authz/AccessControlProvider";
import { UISettingsProvider } from "../features/ui/UISettingsProvider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AccessControlProvider>
          <UISettingsProvider>{children}</UISettingsProvider>
        </AccessControlProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
