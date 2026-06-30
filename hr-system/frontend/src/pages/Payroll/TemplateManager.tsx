/** 薪资结构模板管理 */
import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, Space, Popconfirm, message, Card, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { payrollAPI } from '../../services/api';

export default function TemplateManager() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [items, setItems] = useState<any[]>([]);
  const [form] = Form.useForm();

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const res = await payrollAPI.listTemplates();
      setTemplates(res.data || []);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadTemplates(); }, []);

  const handleSave = async () => {
    const vals = await form.validateFields();
    const payload = { name: vals.name, description: vals.description, items };
    if (editing) {
      await payrollAPI.updateTemplate(editing.id, payload);
    } else {
      await payrollAPI.createTemplate(payload);
    }
    message.success(editing ? '模板已更新' : '模板已创建');
    setModalOpen(false);
    setEditing(null);
    setItems([]);
    loadTemplates();
  };

  const handleEdit = async (t: any) => {
    setEditing(t);
    form.setFieldsValue({ name: t.name, description: t.description });
    try {
      const res = await payrollAPI.listTemplateItems(t.id);
      setItems((res.data || []).map((i: any) => ({ ...i, key: i.id || Math.random() })));
    } catch { setItems([]); }
    setModalOpen(true);
  };

  const addItemRow = () => {
    setItems([...items, { key: Date.now(), name: '', type: 'income', is_taxable: 1, sort_order: items.length }]);
  };

  const updateItemRow = (key: any, field: string, val: any) => {
    setItems(items.map(i => i.key === key ? { ...i, [field]: val } : i));
  };

  const removeItemRow = (key: any) => setItems(items.filter(i => i.key !== key));

  return (
    <Card title="薪资结构模板" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setItems([]); setModalOpen(true); }}>新建模板</Button>}>
      <Table
        dataSource={templates}
        rowKey="id"
        loading={loading}
        columns={[
          { title: '模板名称', dataIndex: 'name' },
          { title: '说明', dataIndex: 'description' },
          { title: '项目数', dataIndex: 'item_count' },
          { title: '创建时间', dataIndex: 'created_at' },
          {
            title: '操作', render: (_, r) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)}>编辑</Button>
                <Popconfirm title="确认删除?" onConfirm={async () => { await payrollAPI.deleteTemplate(r.id); loadTemplates(); }}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal title={editing ? '编辑模板' : '新建模板'} open={modalOpen} onOk={handleSave} onCancel={() => setModalOpen(false)} width={700}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="说明"><Input.TextArea rows={2} /></Form.Item>
        </Form>

        <div style={{ marginTop: 16 }}>
          <h4>薪资项目 <Button size="small" icon={<PlusOutlined />} onClick={addItemRow}>添加项目</Button></h4>
          <Table
            dataSource={items}
            rowKey="key"
            pagination={false}
            size="small"
            columns={[
              { title: '项目名', render: (_, r) => <Input size="small" value={r.name} onChange={e => updateItemRow(r.key, 'name', e.target.value)} /> },
              { title: '类型', width: 100, render: (_, r) => (
                <Select size="small" value={r.type} onChange={v => updateItemRow(r.key, 'type', v)} options={[
                  { value: 'income', label: '收入' }, { value: 'deduction', label: '扣款' },
                ]} />
              )},
              { title: '计税', width: 80, render: (_, r) => (
                <Select size="small" value={r.is_taxable} onChange={v => updateItemRow(r.key, 'is_taxable', v)} options={[
                  { value: 1, label: '是' }, { value: 0, label: '否' },
                ]} />
              )},
              { title: '操作', width: 60, render: (_, r) => (
                <Button size="small" danger icon={<DeleteOutlined />} onClick={() => removeItemRow(r.key)} />
              )},
            ]}
          />
        </div>
      </Modal>
    </Card>
  );
}
