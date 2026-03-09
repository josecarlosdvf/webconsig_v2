export type AppResourceDefinition = {
  resourceKey: string;
  resourceType: "menu" | "screen" | "component" | "api";
  name: string;
  path?: string;
  httpMethod?: string;
  parentKey?: string;
  metadata?: Record<string, unknown>;
  isActive?: boolean;
};

export const appResourceCatalog: AppResourceDefinition[] = [
  { resourceKey: "menu:dashboard", resourceType: "menu", name: "Menu Dashboard", path: "/", metadata: { action: "view", resource: "ui:/dashboard" } },
  { resourceKey: "menu:clientes", resourceType: "menu", name: "Menu Clientes", path: "/crm/clientes", metadata: { action: "view", resource: "ui:/crm/clientes" } },
  { resourceKey: "menu:pipeline", resourceType: "menu", name: "Menu Pipeline", path: "/crm/pipeline", metadata: { action: "view", resource: "ui:/crm/pipeline" } },
  { resourceKey: "menu:financeiro", resourceType: "menu", name: "Menu Financeiro", path: "/erp/financeiro", metadata: { action: "view", resource: "ui:/erp/financeiro" } },
  { resourceKey: "menu:chat", resourceType: "menu", name: "Menu Chat Plugin", path: "/plugins/chat", metadata: { action: "view", resource: "ui:/plugins/chat" } },
  { resourceKey: "menu:permissoes", resourceType: "menu", name: "Menu Permissões", path: "/admin/permissoes", metadata: { action: "view", resource: "ui:/admin/permissoes" } },
  { resourceKey: "menu:configuracoes", resourceType: "menu", name: "Menu Configurações", path: "/admin/configuracoes", metadata: { action: "view", resource: "ui:/admin/configuracoes" } },

  { resourceKey: "screen:dashboard", resourceType: "screen", name: "Tela Dashboard", path: "/", metadata: { resource: "ui:/dashboard", action: "view" } },
  { resourceKey: "screen:chat", resourceType: "screen", name: "Tela Chat Plugin", path: "/plugins/chat", metadata: { resource: "ui:/plugins/chat", action: "view" } },
  { resourceKey: "screen:permissions", resourceType: "screen", name: "Tela Permissões", path: "/admin/permissoes", metadata: { resource: "ui:/admin/permissoes", action: "view" } },

  { resourceKey: "component:chat_send", resourceType: "component", name: "Componente Enviar Chat", path: "/plugins/chat", metadata: { resource: "ui:/plugins/chat/send", action: "create" } },
  { resourceKey: "component:permissions_manage", resourceType: "component", name: "Componente Gerenciar Políticas", path: "/admin/permissoes", metadata: { resource: "ui:/admin/permissoes/manage", action: "edit" } },
];
