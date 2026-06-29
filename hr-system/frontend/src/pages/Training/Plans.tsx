import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, DatePicker, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { trainingAPI } from '../../services/api';
import dayjs from 'dayjs';

export default function TrainingPlans() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = () => {
    setLoading(true);
    trainingAPI.listPlans({ page, page_size: 20 })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page]);

  const columns = [
    { title: '培训主题', dataIndex: 'title' },
    { title: '类型', dataIndex: 'type' },
    { title: '讲师/机构', dataIndex: 'trainer' },
    { title: '开始日期', dataIndex: 'start_date' },
    { title: '结束日期', dataIndex: 'end_date' },
    { title: '地点', dataIndex: 'location' },
    { title: '预算', dataIndex: 'budget', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '参与人数', dataIndex: 'participant_count' },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : v === '进行中' ? 'processing' : 'default'}>{v}</Tag>,
    },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => {
          setEditing(r);
          form.setFieldsValue({ ...r, start_date: r.start_date ? dayjs(r.start_date) : null, end_date: r.end_date ? dayjs(r.end_date) : null });
          setModalOpen(true);
        }}>编辑</Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>培训计划</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          新增计划
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title={editing ? '编辑计划' : '新增计划'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          const payload = {
            ...vals,
            start_date: vals.start_date?.format('YYYY-MM-DD'),
            end_date: vals.end_date?.format('YYYY-MM-DD'),
          };
          if (editing) { await trainingAPI.updatePlan(editing.id, payload); }
          else { await trainingAPI.createPlan(payload); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)} width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="培训主题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="类型"><Select options={[
            { label: '新员工培训', value: '新员工培训' }, { label: '技能提升', value: '技能提升' },
            { label: '管理培训', value: '管理培训' }, { label: '外部培训', value: '外部培训' },
          ]} /></Form.Item>
          <Form.Item name="trainer" label="讲师/机构"><Input /></Form.Item>
          <Form.Item name="start_date" label="开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="location" label="培训地点"><Input /></Form.Item>
          <Form.Item name="budget" label="预算"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="max_participants" label="人数上限"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="培训内容"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="status" label="状态"><Select options={[
            { label: '计划中', value: '计划中' }, { label: '进行中', value: '进行中' },
            { label: '已完成', value: '已完成' }, { label: '已取消', value: '已取消' },
          ]} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
