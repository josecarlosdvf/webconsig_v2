import { Refine, Authenticated } from "@refinedev/core";
import { RefineKbar, RefineKbarProvider } from "@refinedev/kbar";
import { 
  useNotificationProvider,
  ThemedLayout,
  ErrorComponent,
  RefineThemes
} from "@refinedev/antd";
import routerProvider, {
  DocumentTitleHandler,
  NavigateToResource,
  UnsavedChangesNotifier,
  CatchAllNavigate,
} from "@refinedev/react-router";
import { BrowserRouter, Outlet, Route, Routes } from "react-router";
import { ConfigProvider, App as AntApp } from "antd";
import ptBR from "antd/locale/pt_BR";

import "@refinedev/antd/dist/reset.css";

import { flaskDataProvider } from "./providers/flaskDataProvider";
import { authProvider } from "./providers/authProvider";
import { resources } from "./config/resources";

// Pages
import { Dashboard } from "./pages/dashboard";
import { LoginPage } from "./pages/login";
import { 
  ClienteList, 
  ClienteCreate, 
  ClienteEdit, 
  ClienteShow 
} from "./pages/clientes";

function App() {
  return (
    <BrowserRouter>
      <RefineKbarProvider>
        <ConfigProvider 
          theme={RefineThemes.Blue}
          locale={ptBR}
        >
          <AntApp>
            <Refine
              dataProvider={flaskDataProvider}
              authProvider={authProvider}
              routerProvider={routerProvider}
              notificationProvider={useNotificationProvider}
              resources={resources}
              options={{
                syncWithLocation: true,
                warnWhenUnsavedChanges: true,
                projectId: "webconsig-v2",
              }}
            >
              <Routes>
                {/* Rotas Autenticadas */}
                <Route
                  element={
                    <Authenticated
                      key="authenticated-inner"
                      fallback={<CatchAllNavigate to="/login" />}
                    >
                      <ThemedLayout
                        Title={() => (
                          <div style={{ 
                            padding: "8px 16px", 
                            fontWeight: "bold",
                            fontSize: "18px",
                            color: "#1677ff"
                          }}>
                            WebConsig
                          </div>
                        )}
                      >
                        <Outlet />
                      </ThemedLayout>
                    </Authenticated>
                  }
                >
                  <Route index element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  
                  {/* Clientes */}
                  <Route path="/clientes">
                    <Route index element={<ClienteList />} />
                    <Route path="create" element={<ClienteCreate />} />
                    <Route path="edit/:id" element={<ClienteEdit />} />
                    <Route path="show/:id" element={<ClienteShow />} />
                  </Route>

                  {/* Catch all */}
                  <Route path="*" element={<ErrorComponent />} />
                </Route>

                {/* Rotas Públicas */}
                <Route
                  element={
                    <Authenticated
                      key="authenticated-outer"
                      fallback={<Outlet />}
                    >
                      <NavigateToResource />
                    </Authenticated>
                  }
                >
                  <Route path="/login" element={<LoginPage />} />
                </Route>
              </Routes>

              <RefineKbar />
              <UnsavedChangesNotifier />
              <DocumentTitleHandler />
            </Refine>
          </AntApp>
        </ConfigProvider>
      </RefineKbarProvider>
    </BrowserRouter>
  );
}

export default App;
