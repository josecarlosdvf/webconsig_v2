import React from "react";
import {
  useTable,
  List,
  EditButton,
  ShowButton,
  DeleteButton,
  CreateButton,
  FilterDropdown,
} from "@refinedev/antd";
import { Table, Space, Input, Tag, Typography } from "antd";
import { SearchOutlined, UserOutlined } from "@ant-design/icons";

const { Text } = Typography;

interface Cliente {
  id: number;
  cpf: string;
  nome_completo: string;
  email?: string;
  telefone?: string;
  cidade?: string;
  uf?: string;
  status: string;
  created_at: string;
}

export const ClienteList: React.FC = () => {
  const { tableProps } = useTable<Cliente>({
    syncWithLocation: true,
  });

  const columns = [
    {
      dataIndex: "cpf",
      title: "CPF",
      key: "cpf",
      filterDropdown: (props: any) => (
        <FilterDropdown {...props}>
          <Input placeholder="Buscar CPF" prefix={<SearchOutlined />} />
        </FilterDropdown>
      ),
    },
    {
      dataIndex: "nome_completo",
      title: "Nome",
      key: "nome_completo",
      render: (value: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{value}</Text>
        </Space>
      ),
      filterDropdown: (props: any) => (
        <FilterDropdown {...props}>
          <Input placeholder="Buscar nome" prefix={<SearchOutlined />} />
        </FilterDropdown>
      ),
    },
    {
      dataIndex: "email",
      title: "E-mail",
      key: "email",
    },
    {
      dataIndex: "telefone",
      title: "Telefone",
      key: "telefone",
    },
    {
      dataIndex: "cidade",
      title: "Cidade/UF",
      key: "cidade",
      render: (_: any, record: Cliente) =>
        record.cidade ? `${record.cidade}/${record.uf}` : "-",
    },
    {
      dataIndex: "status",
      title: "Status",
      key: "status",
      render: (value: string) => (
        <Tag color={value === "ativo" ? "green" : "red"}>
          {value?.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: "Ações",
      key: "actions",
      render: (_: any, record: Cliente) => (
        <Space>
          <ShowButton hideText size="small" recordItemId={record.id} />
          <EditButton hideText size="small" recordItemId={record.id} />
          <DeleteButton hideText size="small" recordItemId={record.id} />
        </Space>
      ),
    },
  ];

  return (
    <List
      headerButtons={({ createButtonProps }) => (
        <CreateButton {...createButtonProps}>Novo Cliente</CreateButton>
      )}
    >
      <Table
        {...tableProps}
        rowKey="id"
        columns={columns as any}
      />
    </List>
  );
};
