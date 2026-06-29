import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, DatePicker, message, Tag } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { performanceAPI } from '../../services/api';
import dayjs from 'dayjs';

export default function PerformancePlans() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [itemModal, setItemModal] = useState(false);
  const [currentPlan, setCurrentPlan] = useState<any>(null);
  const [items, setItems] = useState<any[]>([]);
  const [form] = Form.useForm();
  const [itemForm] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = () => {
    setLoading(true);
    performanceAPI.listPlans({ page, page_size: 20 })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page]);

  const columns = [
    { title: '方案名称', dataIndex: 'name' },
    { title: '考核周期', dataIndex: 'period' },
    { title: '年份', dataIndex: 'year' },
    { title: '类型', dataIndex: 'type' },
    { title: '开始日期', dataIndex: 'start_date' },
    { title: '结束日期', dataIndex: 'end_date' },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : v === '进行中' ? 'processing' : 'default'}>{v}</Tag>,
    },
    { title: '考核人数', dataIndex: 'assessment_count' },
    {
      title: '操作', render: (_: any, r: any) => (
        <Space>
          <Button size="small" onClick={async () => { setCurrentPlan(r); const { data } = await performanceAPI.listItems(r.id); setItems(data); setItemModal(true); }}>指标</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => { form.setFieldsValue({ ...r, start_date: r.start_date ? dayjs(r.start_date) : null, end_date: r.end_date ? dayjs(r.end_date) : null }); setModalOpen(true); }}>编辑</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>考核方案</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalOpen(true); }}>
          新增方案
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title="考核方案" open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          const payload = { ...vals, start_date: vals.start_date?.format('YYYY-MM-DD'), end_date: vals.end_date?.format('YYYY-MM-DD') };
          await performanceAPI.createPlan(payload);
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="方案名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="period" label="考核周期"><Select options={[{ label: '月度', value: '月度' }, { label: '季度', value: '季度' }, { label: '半年度', value: '半年度' }, { label: '年度', value: '年度' }]} /></Form.Item>
          <Form.Item name="year" label="年份"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="type" label="类型"><Select options={[{ label: 'KPI', value: 'KPI' }, { label: 'OKR', value: 'OKR' }, { label: '360度', value: '360度' }]} /></Form.Item>
          <Form.Item name="start_date" label="开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="方案说明"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>

      <Modal title={`指标管理 - ${currentPlan?.name || ''}`} open={itemModal}
        onCancel={() => setItemModal(false)} footer={null} width={700}>
        <Space style={{ marginBottom: 12 }}>
          <Button type="primary" size="small" onClick={async () => {
            const vals = await itemForm.validateFields();
            await performanceAPI.createItem(currentPlan.id, vals);
            message.success('指标添加成功');
            const { data } = await performanceAPI.listItems(currentPlan.id);
            setItems(data);
            itemForm.resetFields();
          }}>添加指标</Button>
        </Space>
        <Form form={itemForm} layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item name="name" label="指标名" rules={[{ required: true }]}><Input style={{ width: 150 }} /></Form.Item>
          <Form.Item name="weight" label="权重(%)"><InputNumber min={0} max={100} style={{ width: 100 }} /></Form.Item>
          <Form.Item name="target" label="目标值"><Input style={{ width: 150 }} /></Form.Item>
          <Form.Item name="sort_order" label="排序"><InputNumber style={{ width: 80 }} /></Form.Item>
        </Form>
        <Table dataSource={items} rowKey="id" size="small" pagination={false}
          columns={[
            { title: '指标名称', dataIndex: 'name' },
            { title: '权重(%)', dataIndex: 'weight' },
            { title: '目标值', dataIndex: 'target' },
            { title: '排序', dataIndex: 'sort_order' },
          ]} />
      </Modal>
    </div>
  );
}
