import { useEffect, useState } from 'react';
import { Card, Form, Input, Button, Select, message, Table, Modal, Space, Tag, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../services/api';

export default function SystemSettings() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchUsers = () => {
    setLoading(true);
    api.get('/users').then(({ data }) => setUsers(data)).finally(() => setLoading(false));
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreateUser = () => {
    setEditingUser(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEditUser = (u: any) => {
    setEditingUser(u);
    form.setFieldsValue({ username: u.username, role: u.role, password: '' });
    setModalOpen(true);
  };

  const handleDeleteUser = async (id: number) => {
    await api.delete(`/users/${id}`);
    message.success('已删除');
    fetchUsers();
  };

  const handleSubmit = async () => {
    const vals = await form.validateFields();
    if (editingUser) {
      await api.put(`/users/${editingUser.id}`, vals);
      message.success('更新成功');
    } else {
      await api.post('/users', vals);
      message.success('账号创建成功');
    }
    setModalOpen(false);
    fetchUsers();
  };

  const columns = [
    { title: '用户名', dataIndex: 'username' },
    {
      title: '角色', dataIndex: 'role',
      render: (v: string) => <Tag color={v === 'admin' ? 'red' : 'blue'}>{v === 'admin' ? '管理员' : '普通用户'}</Tag>,
    },
    {
      title: '状态', dataIndex: 'is_active',
      render: (v: boolean) => v ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>,
    },
    { title: '最后登录', dataIndex: 'last_login' },
    {
      title: '操作', render: (_: any, u: any) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditUser(u)}>编辑</Button>
          {u.role !== 'admin' && (
            <Popconfirm title="确认删除?" onConfirm={() => handleDeleteUser(u.id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>系统设置</h2>

      <Card title="用户管理" extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateUser}>添加用户</Button>} style={{ marginBottom: 16 }}>
        <Table columns={columns} dataSource={users} rowKey="id" loading={loading} pagination={false} size="small" />
      </Card>

      <Card title="修改密码" style={{ maxWidth: 600 }}>
        <Form layout="vertical" onFinish={async (vals) => {
          try {
            await api.put('/auth/change-password', { old_password: vals.old_password, new_password: vals.new_password });
            message.success('密码修改成功');
          } catch (e: any) {
            message.error(e.response?.data?.detail || '修改失败');
          }
        }}>
          <Form.Item name="old_password" label="原密码" rules={[{ required: true, message: '请输入原密码' }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="new_password" label="新密码" rules={[{ required: true, min: 6, message: '新密码至少6位' }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">修改密码</Button>
          </Form.Item>
        </Form>
      </Card>

      <Modal title={editingUser ? '编辑用户' : '添加用户'} open={modalOpen}
        onOk={handleSubmit} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input disabled={!!editingUser} />
          </Form.Item>
          <Form.Item name="password" label={editingUser ? '新密码（留空不修改）' : '密码'} rules={editingUser ? [] : [{ required: true, message: '请输入密码' }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}>
            <Select options={[
              { label: '普通用户 (user)', value: 'user' },
              { label: '管理员 (admin)', value: 'admin' },
              { label: '经理 (manager)', value: 'manager' },
              { label: '只读 (viewer)', value: 'viewer' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
