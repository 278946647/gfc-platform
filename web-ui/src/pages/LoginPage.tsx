import { Button, Card, Form, Input, Typography, message } from "antd";
import { useNavigate } from "react-router-dom";
import { mapUser, setAuth } from "../api/auth";
import { apiPost } from "../api/client";

export function LoginPage() {
  const nav = useNavigate();
  const [form] = Form.useForm();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #e6f4ff 0%, #f5f5f5 100%)",
      }}
    >
      <Card style={{ width: 400 }}>
        <Typography.Title level={3} style={{ marginTop: 0, textAlign: "center" }}>
          应用加速平台
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ textAlign: "center" }}>
          请使用控制台账号登录
        </Typography.Paragraph>
        <Form
          form={form}
          layout="vertical"
          onFinish={async (v) => {
            try {
              const res = await apiPost<{ token: string; user: Record<string, unknown> }>(
                "/auth/login",
                { username: v.username, password: v.password }
              );
              setAuth(res.token, mapUser(res.user));
              message.success("登录成功");
              nav("/", { replace: true });
            } catch (e) {
              message.error(String(e));
            }
          }}
        >
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>
            登录
          </Button>
        </Form>
        <Typography.Paragraph type="secondary" style={{ marginTop: 16, fontSize: 12 }}>
          首次部署默认账号 admin，默认密码 admin123（可通过环境变量 GFC_ADMIN_DEFAULT_PASSWORD 修改）。
        </Typography.Paragraph>
      </Card>
    </div>
  );
}
