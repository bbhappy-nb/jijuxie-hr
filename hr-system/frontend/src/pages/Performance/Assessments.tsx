import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, InputNumber, Input, message, Tag, Card, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { performanceAPI } from '../../services/api';

export default function PerformanceAssessments() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [scoreModal, setScoreModal] = useState(false);
  const [currentAss, setCurrentAss] = useState<any>(null);
  const [form] = Form.useForm();
  const [scoreForm] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<any>(null);

  const fetchData = () => {
    setLoading(true);
    performanceAPI.listAssessments({ page, page_size: 20 })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page]);
  useEffect(() => {
    performanceAPI.getStats().then(({ data }) => setStats(data));
  }, []);

  const columns = [
    { title: '员工姓名', dataIndex: 'employee_name' },
    { title: '考核人', dataIndex: 'evaluator_name' },
    { title: '方案ID', dataIndex: 'plan_id' },
    { title: '总分', dataIndex: 'total_score' },
    {
      title: '等级', dataIndex: 'grade',
      render: (v: string) => {
        const colors: Record<string, string> = { S: 'purple', A: 'green', B: 'blue', C: 'orange', D: 'red' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : v === '待考核' ? 'orange' : 'default'}>{v}</Tag>,
    },
    { title: '考评语', dataIndex: 'evaluator_comment', ellipsis: true },
    {
      title: '操作', render: (_: any, r: any) => (
        <Space>
          <Button size="small" onClick={async () => { setCurrentAss(r); scoreForm.resetFields(); setScoreModal(true); }}>评分</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => { form.setFieldsValue(r); setModalOpen(true); }}>编辑</Button>
        </Space>
      ),
    },
  ];

  const gradeOption = stats?.grade_distribution ? {
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '60%', data: stats.grade_distribution.map((g: any) => ({ name: g.grade, value: g.count })), label: { formatter: '{b}: {c}' } }],
  } : {};

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>考核记录</h2>
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}><Card title="等级分布"><ReactECharts option={gradeOption} style={{ height: 250 }} /></Card></Col>
          <Col span={12}>
            <Card size="small" style={{ marginBottom: 8 }}><span>总考核数: {stats.total_assessments}</span></Card>
          </Col>
        </Row>
      )}
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalOpen(true); }}>
          新增考核
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title="新增考核" open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          await performanceAPI.createAssessment(vals);
          message.success('创建成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="plan_id" label="方案ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="employee_id" label="被考核人ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="evaluator_id" label="考核人ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>

      <Modal title="评分" open={scoreModal}
        onOk={async () => {
          const vals = await scoreForm.validateFields();
          await performanceAPI.createScore({ ...vals, assessment_id: currentAss.id });
          message.success('评分成功'); setScoreModal(false); fetchData();
        }} onCancel={() => setScoreModal(false)}>
        <Form form={scoreForm} layout="vertical">
          <Form.Item name="item_id" label="指标ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="score" label="得分" rules={[{ required: true }]}><InputNumber min={0} max={100} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="comment" label="评分说明"><Input.TextArea /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
