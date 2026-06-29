import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, InputNumber, DatePicker, Input, Select, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { contractAPI } from '../../services/api';
import dayjs from 'dayjs';

export default function ContractResignation() {
  const [data, setData] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchData = () => {
    contractAPI.listResignation().then(({ data }) => setData(Array.isArray(data) ? data : []));
  };

  useEffect(() => { fetchData(); }, []);

  const columns = [
    { title: '员工', dataIndex: 'employee_name' },
    { title: '申请日期', dataIndex: 'apply_date' },
    { title: '最后工作日', dataIndex: 'resign_date' },
    {
      title: '类型', dataIndex: 'type',
      render: (v: string) => <Tag>{v}</Tag>,
    },
    { title: '离职原因', dataIndex: 'reason', ellipsis: true },
    { title: '交接人', dataIndex: 'handover_person' },
    {
      title: '交接状态', dataIndex: 'handover_status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : 'orange'}>{v}</Tag>,
    },
    { title: '资产归还', dataIndex: 'asset_returned', render: (v: number) => v ? <Tag color="green">已归还</Tag> : <Tag color="red">未归还</Tag> },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : 'orange'}>{v}</Tag>,
    },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => {
          setEditing(r);
          form.setFieldsValue({ ...r, apply_date: r.apply_date ? dayjs(r.apply_date) : null, resign_date: r.resign_date ? dayjs(r.resign_date) : null });
          setModalOpen(true);
        }}>编辑</Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>离职管理</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          新增离职
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} />

      <Modal title={editing ? '编辑离职记录' : '新增离职'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          const payload = { ...vals, apply_date: vals.apply_date?.format('YYYY-MM-DD'), resign_date: vals.resign_date?.format('YYYY-MM-DD') };
          if (editing) { await contractAPI.updateResignation(editing.id, payload); }
          else { await contractAPI.createResignation(payload); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="employee_id" label="员工ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="apply_date" label="申请日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="resign_date" label="最后工作日"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="type" label="类型"><Select options={[
            { label: '主动离职', value: '主动离职' }, { label: '协商解除', value: '协商解除' },
            { label: '辞退', value: '辞退' }, { label: '退休', value: '退休' },
          ]} /></Form.Item>
          <Form.Item name="reason" label="离职原因"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="handover_person" label="交接人"><Input /></Form.Item>
          <Form.Item name="exit_interview" label="离职面谈"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
