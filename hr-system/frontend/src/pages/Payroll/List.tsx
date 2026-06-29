import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, InputNumber, message, Tag, Card, Row, Col } from 'antd';
import { PlusOutlined, CalculatorOutlined, CheckOutlined, EditOutlined } from '@ant-design/icons';
import { payrollAPI } from '../../services/api';

export default function PayrollList() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);

  const fetchData = () => {
    setLoading(true);
    payrollAPI.list({ page, page_size: 20, year, month })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page, year, month]);
  useEffect(() => {
    payrollAPI.getSummary(year, month).then(({ data }) => setSummary(data));
  }, [year, month]);

  const handleBatchGenerate = async () => {
    await payrollAPI.batchGenerate(year, month);
    message.success('批量生成成功');
    fetchData();
  };

  const columns = [
    { title: '员工', dataIndex: 'employee_name' },
    { title: '部门', dataIndex: 'department_name' },
    { title: '基本工资', dataIndex: 'base_salary', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '绩效奖金', dataIndex: 'performance_bonus', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '补贴', dataIndex: 'subsidy', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '应发合计', dataIndex: 'total_income', render: (v: number) => <strong>¥{v?.toLocaleString()}</strong> },
    { title: '社保', dataIndex: 'social_insurance', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '公积金', dataIndex: 'housing_fund', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '个税', dataIndex: 'tax', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '实发', dataIndex: 'net_salary', render: (v: number) => <strong style={{ color: '#3f8600' }}>¥{v?.toLocaleString()}</strong> },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已确认' ? 'green' : v === '已发放' ? 'blue' : 'default'}>{v}</Tag>,
    },
    {
      title: '操作', render: (_: any, r: any) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => { form.setFieldsValue(r); setModalOpen(true); }}>编辑</Button>
          {r.status === '草稿' && (
            <Button size="small" icon={<CheckOutlined />} onClick={async () => { await payrollAPI.confirm(r.id); message.success('已确认'); fetchData(); }}>确认</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>工资表</h2>
      {summary && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}><Card size="small"><span>员工: {summary.employee_count}人</span></Card></Col>
          <Col span={4}><Card size="small"><span>应发合计: ¥{summary.total_income?.toLocaleString()}</span></Card></Col>
          <Col span={4}><Card size="small"><span>个税合计: ¥{summary.total_tax?.toLocaleString()}</span></Card></Col>
          <Col span={4}><Card size="small"><span>社保合计: ¥{summary.total_social_insurance?.toLocaleString()}</span></Card></Col>
          <Col span={4}><Card size="small"><span>公积金合计: ¥{summary.total_housing_fund?.toLocaleString()}</span></Card></Col>
          <Col span={4}><Card size="small"><span style={{ color: '#3f8600', fontWeight: 600 }}>实发合计: ¥{summary.total_net_salary?.toLocaleString()}</span></Card></Col>
        </Row>
      )}
      <Space style={{ marginBottom: 16 }}>
        <span>年份:</span>
        <InputNumber value={year} onChange={(v) => v && setYear(v)} />
        <span>月份:</span>
        <InputNumber min={1} max={12} value={month} onChange={(v) => v && setMonth(v)} />
        <Button icon={<CalculatorOutlined />} onClick={handleBatchGenerate}>批量生成当月工资</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); form.setFieldsValue({ year, month }); setModalOpen(true); }}>单条录入</Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        scroll={{ x: 1800 }}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title="工资录入/编辑" open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          if (vals.id) { await payrollAPI.update(vals.id, vals); }
          else { await payrollAPI.create(vals); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)} width={600}>
        <Form form={form} layout="vertical">
          <Form.Item name="employee_id" label="员工ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="year" label="年份"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="month" label="月份"><InputNumber min={1} max={12} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="base_salary" label="基本工资"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="performance_bonus" label="绩效奖金"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="subsidy" label="补贴"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="overtime_pay" label="加班费"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="absence_deduction" label="缺勤扣款"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="other_deduction" label="其他扣款"><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
