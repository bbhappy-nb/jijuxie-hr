import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, message, Tag, Card, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { recruitmentAPI } from '../../services/api';

const STAGES = ['简历筛选', '初试', '复试', '终试', 'Offer', '入职', '放弃'];

export default function RecruitmentCandidates() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [stage, setStage] = useState<string | undefined>();
  const [stats, setStats] = useState<any>(null);

  const fetchData = () => {
    setLoading(true);
    recruitmentAPI.listCandidates({ page, page_size: 20, stage })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page, stage]);
  useEffect(() => {
    recruitmentAPI.getStats().then(({ data }) => setStats(data));
  }, []);

  const columns = [
    { title: '姓名', dataIndex: 'name' },
    { title: '手机号', dataIndex: 'phone' },
    { title: '学历', dataIndex: 'education' },
    { title: '应聘岗位', dataIndex: 'recruitment_title' },
    { title: '期望薪资', dataIndex: 'expected_salary' },
    {
      title: '阶段', dataIndex: 'stage',
      render: (v: string) => <Tag color={v === '入职' ? 'green' : v === '放弃' ? 'red' : 'blue'}>{v}</Tag>,
    },
    { title: '面试官', dataIndex: 'interviewer' },
    { title: '面试评价', dataIndex: 'interview_feedback', ellipsis: true },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModalOpen(true); }}>
          更新
        </Button>
      ),
    },
  ];

  const channelOption = stats ? {
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '60%', data: stats.by_channel, label: { formatter: '{b}: {c}' } }],
  } : {};

  const stageOption = stats ? {
    tooltip: { trigger: 'item' },
    xAxis: { type: 'category', data: stats.by_stage.map((s: any) => s.name) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: stats.by_stage.map((s: any) => s.value), itemStyle: { color: '#1677ff' } }],
  } : {};

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>候选人管理</h2>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card size="small"><span>招聘中岗位: {stats?.total_jobs || 0}</span></Card>
        </Col>
        <Col span={8}>
          <Card size="small"><span>候选人总数: {stats?.total_candidates || 0}</span></Card>
        </Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}><Card title="渠道分布"><ReactECharts option={channelOption} style={{ height: 250 }} /></Card></Col>
        <Col span={12}><Card title="阶段分布"><ReactECharts option={stageOption} style={{ height: 250 }} /></Card></Col>
      </Row>

      <Space style={{ marginBottom: 16 }}>
        <Select placeholder="筛选阶段" allowClear style={{ width: 140 }} value={stage}
          onChange={(v) => { setStage(v); setPage(1); }}
          options={STAGES.map(s => ({ label: s, value: s }))} />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          添加候选人
        </Button>
      </Space>

      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title={editing ? '更新候选人' : '添加候选人'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          if (editing) { await recruitmentAPI.updateCandidate(editing.id, vals); }
          else { await recruitmentAPI.createCandidate(vals); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="phone" label="手机号"><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="recruitment_id" label="应聘岗位ID" rules={[{ required: true }]}><Input type="number" /></Form.Item>
          <Form.Item name="education" label="学历"><Input /></Form.Item>
          <Form.Item name="expected_salary" label="期望薪资"><Input /></Form.Item>
          {editing && (
            <>
              <Form.Item name="stage" label="面试阶段"><Select options={STAGES.map(s => ({ label: s, value: s }))} /></Form.Item>
              <Form.Item name="interviewer" label="面试官"><Input /></Form.Item>
              <Form.Item name="interview_feedback" label="面试评价"><Input.TextArea rows={3} /></Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
}
