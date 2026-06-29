import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { trainingAPI } from '../../services/api';

export default function TrainingRecords() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = () => {
    setLoading(true);
    trainingAPI.listRecords({ page, page_size: 20 })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page]);

  const columns = [
    { title: '员工姓名', dataIndex: 'employee_name' },
    { title: '培训计划ID', dataIndex: 'plan_id' },
    { title: '考核分数', dataIndex: 'score' },
    { title: '学时', dataIndex: 'hours' },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : v === '已参加' ? 'blue' : 'default'}>{v}</Tag>,
    },
    { title: '获得证书', dataIndex: 'certificate' },
    { title: '培训反馈', dataIndex: 'feedback', ellipsis: true },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModalOpen(true); }}>编辑</Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>培训记录</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          添加记录
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title={editing ? '编辑记录' : '添加记录'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          if (editing) { await trainingAPI.updateRecord(editing.id, vals); }
          else { await trainingAPI.createRecord(vals); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="plan_id" label="培训计划ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="employee_id" label="员工ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="score" label="考核分数"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="hours" label="学时"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="status" label="状态"><Select options={[
            { label: '已报名', value: '已报名' }, { label: '已参加', value: '已参加' },
            { label: '已完成', value: '已完成' }, { label: '未通过', value: '未通过' },
          ]} /></Form.Item>
          <Form.Item name="certificate" label="证书"><Input /></Form.Item>
          <Form.Item name="feedback" label="反馈"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
