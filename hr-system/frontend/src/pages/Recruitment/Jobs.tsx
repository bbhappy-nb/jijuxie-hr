import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { recruitmentAPI } from '../../services/api';

export default function RecruitmentJobs() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = () => {
    setLoading(true);
    recruitmentAPI.listJobs({ page, page_size: 20 })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page]);

  const columns = [
    { title: '岗位名称', dataIndex: 'title' },
    { title: '招聘人数', dataIndex: 'headcount' },
    { title: '薪资范围', dataIndex: 'salary_range' },
    { title: '渠道', dataIndex: 'channel' },
    {
      title: '优先级', dataIndex: 'priority',
      render: (v: string) => <Tag color={v === '紧急' ? 'red' : v === '普通' ? 'blue' : 'default'}>{v}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '招聘中' ? 'processing' : 'default'}>{v}</Tag>,
    },
    { title: '候选人', dataIndex: 'candidate_count' },
    { title: '发布日期', dataIndex: 'publish_date' },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModalOpen(true); }}>
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>招聘岗位</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          发布岗位
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title={editing ? '编辑岗位' : '发布岗位'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          if (editing) { await recruitmentAPI.updateJob(editing.id, vals); }
          else { await recruitmentAPI.createJob(vals); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)} width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="岗位名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="department_id" label="需求部门ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="headcount" label="招聘人数"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="salary_range" label="薪资范围"><Input placeholder="如: 15k-25k" /></Form.Item>
          <Form.Item name="channel" label="招聘渠道"><Input placeholder="Boss直聘/猎头/内推" /></Form.Item>
          <Form.Item name="priority" label="优先级"><Select options={[{ label: '紧急', value: '紧急' }, { label: '普通', value: '普通' }, { label: '储备', value: '储备' }]} /></Form.Item>
          <Form.Item name="requirements" label="岗位要求"><Input.TextArea rows={4} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
