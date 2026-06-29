import { Card, Form, Input, Button, message } from 'antd';
import { useAuth } from '../stores/useAuth';

export default function SystemSettings() {
  const { user } = useAuth();

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>系统设置</h2>
      <Card title="基本信息" style={{ marginBottom: 16, maxWidth: 600 }}>
        <Form layout="vertical">
          <Form.Item label="系统名称">
            <Input value="寄居蟹一代 - 人力资源管理系统" disabled />
          </Form.Item>
          <Form.Item label="当前用户">
            <Input value={user?.username || ''} disabled />
          </Form.Item>
          <Form.Item label="用户角色">
            <Input value={user?.role === 'admin' ? '管理员' : '普通用户'} disabled />
          </Form.Item>
        </Form>
      </Card>
      <Card title="修改密码" style={{ maxWidth: 600 }}>
        <Form layout="vertical" onFinish={() => message.success('密码修改成功（演示）')}>
          <Form.Item name="old_password" label="原密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">修改密码</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
