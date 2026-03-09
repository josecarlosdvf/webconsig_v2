import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";
import { AdminLayout } from "./layouts/AdminLayout";
import { CustomersPage } from "./pages/CustomersPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FinancePage } from "./pages/FinancePage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PipelinePage } from "./pages/PipelinePage";
import { SettingsPage } from "./pages/SettingsPage";
import { useAuth } from "../features/auth/AuthProvider";

function ProtectedLayout() {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <AdminLayout />;
}

function LoginRoute() {
  const { user } = useAuth();
  if (user) {
    return <Navigate to="/" replace />;
  }

  return <LoginPage />;
}

const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginRoute />
  },
  {
    path: "/",
    element: <ProtectedLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "crm/clientes", element: <CustomersPage /> },
      { path: "crm/pipeline", element: <PipelinePage /> },
      { path: "erp/financeiro", element: <FinancePage /> },
      { path: "admin/configuracoes", element: <SettingsPage /> }
    ]
  },
  {
    path: "*",
    element: <NotFoundPage />
  }
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
