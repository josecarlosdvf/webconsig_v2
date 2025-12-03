import type { PropsWithChildren } from "react";
import { useState } from "react";
import { Layout as AntLayout, theme } from "antd";
import { ThemedSider, ThemedHeader, ThemedLayoutContextProvider } from "@refinedev/antd";

const { Content } = AntLayout;

export const Layout: React.FC<PropsWithChildren> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const { token } = theme.useToken();

  return (
    <ThemedLayoutContextProvider>
      <AntLayout style={{ minHeight: "100vh" }}>
        <ThemedSider 
          Title={() => (
            <div style={{ 
              padding: "16px", 
              textAlign: "center",
              color: token.colorPrimary,
              fontWeight: "bold",
              fontSize: "18px"
            }}>
              WebConsig
            </div>
          )}
        />
        <AntLayout>
          <ThemedHeader sticky />
          <Content
            style={{
              margin: "24px 16px",
              padding: 24,
              minHeight: 280,
              background: token.colorBgContainer,
              borderRadius: token.borderRadiusLG,
            }}
          >
            {children}
          </Content>
        </AntLayout>
      </AntLayout>
    </ThemedLayoutContextProvider>
  );
};
