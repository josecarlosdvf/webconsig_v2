import React from "react";
import { Card, Row, Col, Statistic, Table, Typography, Space, Progress } from "antd";
import {
  UserOutlined,
  FileTextOutlined,
  DollarOutlined,
  RiseOutlined,
  TeamOutlined,
} from "@ant-design/icons";

const { Title, Text } = Typography;

// Dados mock - serão substituídos por dados reais da API
const recentPropostas = [
  { id: 1, cliente: "João Silva", valor: 15000, status: "pendente", data: "2025-12-03" },
  { id: 2, cliente: "Maria Santos", valor: 25000, status: "aprovada", data: "2025-12-02" },
  { id: 3, cliente: "Pedro Costa", valor: 8500, status: "em_analise", data: "2025-12-01" },
];

const statusColors: Record<string, string> = {
  pendente: "orange",
  aprovada: "green",
  em_analise: "blue",
  recusada: "red",
};

export const Dashboard: React.FC = () => {
  return (
    <div style={{ padding: "24px" }}>
      <Title level={2}>Dashboard</Title>
      <Text type="secondary">Visão geral do sistema</Text>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total de Clientes"
              value={1254}
              prefix={<UserOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Propostas do Mês"
              value={87}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Valor Total"
              value={458750}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: "#722ed1" }}
              formatter={(value) =>
                `R$ ${Number(value).toLocaleString("pt-BR", {
                  minimumFractionDigits: 2,
                })}`
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Taxa de Conversão"
              value={68.5}
              prefix={<RiseOutlined />}
              suffix="%"
              valueStyle={{ color: "#fa8c16" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="Propostas Recentes">
            <Table
              dataSource={recentPropostas}
              rowKey="id"
              pagination={false}
              size="small"
            >
              <Table.Column dataIndex="cliente" title="Cliente" />
              <Table.Column
                dataIndex="valor"
                title="Valor"
                render={(value) =>
                  `R$ ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`
                }
              />
              <Table.Column
                dataIndex="status"
                title="Status"
                render={(value) => (
                  <span style={{ color: statusColors[value] }}>
                    {value.replace("_", " ").toUpperCase()}
                  </span>
                )}
              />
              <Table.Column
                dataIndex="data"
                title="Data"
                render={(value) => new Date(value).toLocaleDateString("pt-BR")}
              />
            </Table>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Metas do Mês">
            <Space direction="vertical" style={{ width: "100%" }}>
              <div>
                <Text>Propostas</Text>
                <Progress percent={72} status="active" />
              </div>
              <div>
                <Text>Contratos</Text>
                <Progress percent={45} status="active" strokeColor="#52c41a" />
              </div>
              <div>
                <Text>Faturamento</Text>
                <Progress percent={88} status="active" strokeColor="#722ed1" />
              </div>
            </Space>
          </Card>

          <Card title="Equipe" style={{ marginTop: 16 }}>
            <Statistic
              title="Usuários Ativos"
              value={12}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
