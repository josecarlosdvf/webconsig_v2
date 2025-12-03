import {
  TeamOutlined,
  UserOutlined,
  FileOutlined,
  DollarOutlined,
  WhatsAppOutlined,
  SettingOutlined,
  DashboardOutlined,
  FileTextOutlined,
  BankOutlined,
} from "@ant-design/icons";

export const resources = [
  {
    name: "dashboard",
    list: "/",
    meta: {
      label: "Dashboard",
      icon: <DashboardOutlined />,
    },
  },
  {
    name: "clientes",
    list: "/clientes",
    create: "/clientes/create",
    edit: "/clientes/edit/:id",
    show: "/clientes/show/:id",
    meta: {
      label: "Clientes",
      icon: <UserOutlined />,
      canDelete: true,
    },
  },
  {
    name: "propostas",
    list: "/propostas",
    create: "/propostas/create",
    edit: "/propostas/edit/:id",
    show: "/propostas/show/:id",
    meta: {
      label: "Propostas",
      icon: <FileTextOutlined />,
      canDelete: true,
    },
  },
  {
    name: "tabelas",
    list: "/tabelas",
    create: "/tabelas/create",
    edit: "/tabelas/edit/:id",
    show: "/tabelas/show/:id",
    meta: {
      label: "Tabelas de Empréstimo",
      icon: <BankOutlined />,
      parent: "propostas",
      canDelete: true,
    },
  },
  {
    name: "contratos",
    list: "/contratos",
    create: "/contratos/create",
    edit: "/contratos/edit/:id",
    show: "/contratos/show/:id",
    meta: {
      label: "Contratos",
      icon: <FileOutlined />,
      canDelete: true,
    },
  },
  {
    name: "financeiro",
    list: "/financeiro",
    meta: {
      label: "Financeiro",
      icon: <DollarOutlined />,
    },
  },
  {
    name: "funcionarios",
    list: "/funcionarios",
    create: "/funcionarios/create",
    edit: "/funcionarios/edit/:id",
    show: "/funcionarios/show/:id",
    meta: {
      label: "Funcionários",
      icon: <TeamOutlined />,
      canDelete: true,
    },
  },
  {
    name: "equipes",
    list: "/equipes",
    create: "/equipes/create",
    edit: "/equipes/edit/:id",
    show: "/equipes/show/:id",
    meta: {
      label: "Equipes",
      icon: <TeamOutlined />,
      parent: "funcionarios",
      canDelete: true,
    },
  },
  {
    name: "messaging",
    list: "/messaging",
    meta: {
      label: "WhatsApp",
      icon: <WhatsAppOutlined />,
    },
  },
  {
    name: "usuarios",
    list: "/admin/usuarios",
    create: "/admin/usuarios/create",
    edit: "/admin/usuarios/edit/:id",
    show: "/admin/usuarios/show/:id",
    meta: {
      label: "Usuários",
      icon: <UserOutlined />,
      parent: "admin",
      canDelete: true,
    },
  },
  {
    name: "admin",
    meta: {
      label: "Administração",
      icon: <SettingOutlined />,
    },
  },
];
