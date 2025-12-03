import React from "react";
import { Edit, useForm } from "@refinedev/antd";
import { Form, Input, Select, Row, Col, Card, Divider } from "antd";
import { UserOutlined, PhoneOutlined, MailOutlined, HomeOutlined } from "@ant-design/icons";

export const ClienteEdit: React.FC = () => {
  const { formProps, saveButtonProps, query } = useForm();
  
  const clienteData = query?.data?.data;

  return (
    <Edit saveButtonProps={saveButtonProps}>
      <Form {...formProps} layout="vertical">
        <Card title="Dados Pessoais" size="small">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="CPF"
                name="cpf"
                rules={[{ required: true, message: "CPF é obrigatório" }]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="000.000.000-00"
                  maxLength={14}
                  disabled
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={16}>
              <Form.Item
                label="Nome Completo"
                name="nome_completo"
                rules={[{ required: true, message: "Nome é obrigatório" }]}
              >
                <Input placeholder="Nome completo do cliente" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="Data de Nascimento" name="data_nascimento">
                <Input type="date" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="RG" name="rg">
                <Input placeholder="Número do RG" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Órgão Emissor" name="rg_orgao">
                <Input placeholder="SSP/UF" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Divider />

        <Card title="Contato" size="small">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="Telefone" name="telefone">
                <Input
                  prefix={<PhoneOutlined />}
                  placeholder="(00) 00000-0000"
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Telefone Secundário" name="telefone2">
                <Input
                  prefix={<PhoneOutlined />}
                  placeholder="(00) 00000-0000"
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                label="E-mail"
                name="email"
                rules={[{ type: "email", message: "E-mail inválido" }]}
              >
                <Input prefix={<MailOutlined />} placeholder="email@exemplo.com" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Divider />

        <Card title="Endereço" size="small">
          <Row gutter={16}>
            <Col xs={24} md={6}>
              <Form.Item label="CEP" name="cep">
                <Input prefix={<HomeOutlined />} placeholder="00000-000" />
              </Form.Item>
            </Col>
            <Col xs={24} md={14}>
              <Form.Item label="Logradouro" name="logradouro">
                <Input placeholder="Rua, Avenida..." />
              </Form.Item>
            </Col>
            <Col xs={24} md={4}>
              <Form.Item label="Número" name="numero">
                <Input placeholder="Nº" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="Complemento" name="complemento">
                <Input placeholder="Apto, Bloco..." />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Bairro" name="bairro">
                <Input placeholder="Bairro" />
              </Form.Item>
            </Col>
            <Col xs={24} md={6}>
              <Form.Item label="Cidade" name="cidade">
                <Input placeholder="Cidade" />
              </Form.Item>
            </Col>
            <Col xs={24} md={2}>
              <Form.Item label="UF" name="uf">
                <Input placeholder="UF" maxLength={2} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Divider />

        <Card title="Informações Adicionais" size="small">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="Órgão" name="orgao">
                <Input placeholder="INSS, Exército..." />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Matrícula" name="matricula">
                <Input placeholder="Número da matrícula" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Status" name="status">
                <Select>
                  <Select.Option value="ativo">Ativo</Select.Option>
                  <Select.Option value="inativo">Inativo</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row>
            <Col span={24}>
              <Form.Item label="Observações" name="observacoes">
                <Input.TextArea rows={3} placeholder="Observações sobre o cliente..." />
              </Form.Item>
            </Col>
          </Row>
        </Card>
      </Form>
    </Edit>
  );
};
