import React from "react";
import { useShow } from "@refinedev/core";
import { Show } from "@refinedev/antd";
import { Descriptions, Tag, Card, Row, Col, Typography, Divider, Space, Button } from "antd";
import { UserOutlined, PhoneOutlined, MailOutlined, HomeOutlined, FileTextOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router";

const { Title, Text } = Typography;

interface Cliente {
  id: number;
  cpf: string;
  nome_completo: string;
  data_nascimento?: string;
  rg?: string;
  rg_orgao?: string;
  email?: string;
  telefone?: string;
  telefone2?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  orgao?: string;
  matricula?: string;
  status: string;
  observacoes?: string;
  created_at: string;
}

export const ClienteShow: React.FC = () => {
  const { query } = useShow<Cliente>();
  const { data, isLoading } = query;
  const record = data?.data;
  const navigate = useNavigate();

  return (
    <Show isLoading={isLoading}>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Title level={4}>
                <UserOutlined /> {record?.nome_completo}
              </Title>
              <Tag color={record?.status === "ativo" ? "green" : "red"}>
                {record?.status?.toUpperCase()}
              </Tag>
            </Space>

            <Divider />

            <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
              <Descriptions.Item label="CPF">{record?.cpf}</Descriptions.Item>
              <Descriptions.Item label="RG">
                {record?.rg} {record?.rg_orgao && `- ${record?.rg_orgao}`}
              </Descriptions.Item>
              <Descriptions.Item label="Data de Nascimento">
                {record?.data_nascimento || "-"}
              </Descriptions.Item>
            </Descriptions>

            <Divider>
              <PhoneOutlined /> Contato
            </Divider>

            <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
              <Descriptions.Item label="Telefone">
                {record?.telefone || "-"}
              </Descriptions.Item>
              <Descriptions.Item label="Telefone 2">
                {record?.telefone2 || "-"}
              </Descriptions.Item>
              <Descriptions.Item label="E-mail">
                {record?.email || "-"}
              </Descriptions.Item>
            </Descriptions>

            <Divider>
              <HomeOutlined /> Endereço
            </Divider>

            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="Endereço">
                {record?.logradouro
                  ? `${record.logradouro}, ${record.numero || "S/N"}${
                      record.complemento ? ` - ${record.complemento}` : ""
                    }`
                  : "-"}
              </Descriptions.Item>
              <Descriptions.Item label="Bairro">
                {record?.bairro || "-"}
              </Descriptions.Item>
              <Descriptions.Item label="Cidade/UF">
                {record?.cidade ? `${record.cidade}/${record.uf}` : "-"}
              </Descriptions.Item>
              <Descriptions.Item label="CEP">{record?.cep || "-"}</Descriptions.Item>
            </Descriptions>

            <Divider>Informações Adicionais</Divider>

            <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
              <Descriptions.Item label="Órgão">{record?.orgao || "-"}</Descriptions.Item>
              <Descriptions.Item label="Matrícula">
                {record?.matricula || "-"}
              </Descriptions.Item>
            </Descriptions>

            {record?.observacoes && (
              <>
                <Divider>Observações</Divider>
                <Text>{record.observacoes}</Text>
              </>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Ações Rápidas">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                block
                onClick={() => navigate(`/propostas/create?cliente_id=${record?.id}`)}
              >
                Nova Proposta
              </Button>
              <Button
                icon={<MailOutlined />}
                block
                onClick={() => navigate(`/messaging?telefone=${record?.telefone}`)}
              >
                Enviar WhatsApp
              </Button>
            </Space>
          </Card>

          <Card title="Resumo" style={{ marginTop: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Cadastrado em">
                {record?.created_at
                  ? new Date(record.created_at).toLocaleDateString("pt-BR")
                  : "-"}
              </Descriptions.Item>
              <Descriptions.Item label="Propostas">0</Descriptions.Item>
              <Descriptions.Item label="Contratos">0</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </Show>
  );
};
