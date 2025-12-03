import React from "react";
import { Form, Input, Button, Card, Typography, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { useLogin } from "@refinedev/core";

const { Title, Text } = Typography;

export const LoginPage: React.FC = () => {
  const { mutate: login } = useLogin();
  const [loading, setLoading] = React.useState(false);

  const onFinish = (values: { email: string; password: string }) => {
    setLoading(true);
    login(values, {
      onSuccess: () => {
        message.success("Login realizado com sucesso!");
        setLoading(false);
      },
      onError: (error) => {
        message.error(error?.message || "Erro ao fazer login");
        setLoading(false);
      },
    });
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <Title level={2} style={{ marginBottom: 8 }}>
            WebConsig
          </Title>
          <Text type="secondary">Sistema de Gestão de Consignados</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: "Digite seu e-mail" },
              { type: "email", message: "E-mail inválido" },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="E-mail"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: "Digite sua senha" }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Senha"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loading}
            >
              Entrar
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: "center" }}>
          <Text type="secondary">
            Esqueceu a senha?{" "}
            <a href="/forgot-password">Recuperar acesso</a>
          </Text>
        </div>
      </Card>
    </div>
  );
};
