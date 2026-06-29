import { useEffect, useState } from 'react';
import { Card, Row, Col, Table, Button, Modal, Form, Input, InputNumber, Space, message, Tabs, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { departmentAPI, positionAPI, contractAPI } from '../services/api';

export default function HRPlanning() {
  const [departments, setDepartments] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [deptModal, setDeptModal] = useState(false);
  const [posModal, setPosModal] = useState(false);
  const [budgetModal, setBudgetModal] = useState(false);
  const [editingDept, setEditingDept] = useState<any>(null);
  const [deptForm] = Form.useForm();
  const [posForm] = Form.useForm();
  const [budgetForm] = Form.useForm();

  const fetchData = () => {
    departmentAPI.list().then(({ data }) => setDepartments(data));
    positionAPI.list().then(({ data }) => setPositions(data));
    contractAPI.listBudget(new Date().getFullYear()).then(({ data }) => setBudgets(data));
  };

  useEffect(() => { fetchData(); }, []);

  const deptColumns = [
    { title: '部门名称', dataIndex: 'name' },
    { title: '员工数', dataIndex: 'employee_count' },
    { title: '描述', dataIndex: 'description' },
    {
      title: '操作', render: (_: any, r: any) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => { setEditingDept(r); deptForm.setFieldsValue(r); setDeptModal(true); }}>编辑</Button>
          <Popconfirm title="确认删除?" onConfirm={async () => { await departmentAPI.delete(r.id); message.success('已删除'); fetchData(); }}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const posColumns = [
    { title: '岗位名称', dataIndex: 'name' },
    { title: '所属部门', dataIndex: 'department_name' },
    { title: '编制', dataIndex: 'headcount' },
    { title: '在岗', dataIndex: 'current_count' },
    {
      title: '状态', render: (_: any, r: any) => {
        const diff = r.headcount - r.current_count;
        return <span style={{ color: diff > 0 ? 'red' : 'green' }}>{diff > 0 ? `缺 ${diff} 人` : '满编'}</span>;
      },
    },
    {
      title: '操作', render: (_: any, r: any) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => { posForm.setFieldsValue(r); setPosModal(true); }}>编辑</Button>
        </Space>
      ),
    },
  ];

  const budgetColumns = [
    { title: '类别', dataIndex: 'category' },
    { title: '部门ID', dataIndex: 'department_id' },
    { title: '预算总额', dataIndex: 'budget_amount', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '已支出', dataIndex: 'spent_amount', render: (v: number) => `¥${v?.toLocaleString()}` },
    { title: '执行率', render: (_: any, r: any) => `${r.budget_amount ? Math.round(r.spent_amount / r.budget_amount * 100) : 0}%` },
  ];

  // 组织架构树图
  const buildTree = (depts: any[], parentId: number | null = null): any[] => {
    return depts.filter(d => d.parent_id === parentId).map(d => ({
      name: d.name,
      value: d.employee_count,
      children: buildTree(depts, d.id),
    }));
  };

  const treeOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'tree', data: [{ name: '组织架构', children: buildTree(departments) }],
      top: '5%', left: '10%', bottom: '5%', right: '20%',
      symbolSize: 10, orient: 'LR',
      label: { position: 'right', verticalAlign: 'middle', align: 'left', fontSize: 12 },
      leaves: { label: { position: 'right', verticalAlign: 'middle', align: 'left' } },
    }],
  };

  const tabItems = [
    {
      key: 'org', label: '组织架构',
      children: (
        <Row gutter={16}>
          <Col span={12}>
            <Card title="部门管理" extra={<Button icon={<PlusOutlined />} size="small" onClick={() => { setEditingDept(null); deptForm.resetFields(); setDeptModal(true); }}>新增</Button>}>
              <Table columns={deptColumns} dataSource={departments} rowKey="id" pagination={false} size="small" />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="组织架构图"><ReactECharts option={treeOption} style={{ height: 400 }} /></Card>
          </Col>
        </Row>
      ),
    },
    {
      key: 'position', label: '岗位编制',
      children: (
        <Card title="岗位编制管理" extra={<Button icon={<PlusOutlined />} size="small" onClick={() => { posForm.resetFields(); setPosModal(true); }}>新增岗位</Button>}>
          <Table columns={posColumns} dataSource={positions} rowKey="id" pagination={false} size="small" />
        </Card>
      ),
    },
    {
      key: 'budget', label: '人力预算',
      children: (
        <Card title="年度人力预算" extra={<Button icon={<PlusOutlined />} size="small" onClick={() => { budgetForm.resetFields(); setBudgetModal(true); }}>新增预算</Button>}>
          <Table columns={budgetColumns} dataSource={budgets} rowKey="id" pagination={false} size="small" />
        </Card>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>人力资源规划</h2>
      <Tabs items={tabItems} />

      {/* 部门Modal */}
      <Modal title={editingDept ? '编辑部门' : '新增部门'} open={deptModal}
        onOk={async () => {
          const vals = await deptForm.validateFields();
          if (editingDept) { await departmentAPI.update(editingDept.id, vals); }
          else { await departmentAPI.create(vals); }
          message.success('保存成功'); setDeptModal(false); fetchData();
        }} onCancel={() => setDeptModal(false)}>
        <Form form={deptForm} layout="vertical">
          <Form.Item name="name" label="部门名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="parent_id" label="上级部门ID"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea /></Form.Item>
          <Form.Item name="sort_order" label="排序"><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>

      {/* 岗位Modal */}
      <Modal title="岗位信息" open={posModal}
        onOk={async () => {
          const vals = await posForm.validateFields();
          if (posForm.getFieldValue('id')) {
            await positionAPI.update(posForm.getFieldValue('id'), vals);
          } else { await positionAPI.create(vals); }
          message.success('保存成功'); setPosModal(false); fetchData();
        }} onCancel={() => setPosModal(false)}>
        <Form form={posForm} layout="vertical">
          <Form.Item name="name" label="岗位名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="department_id" label="部门ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="headcount" label="编制人数"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="岗位职责"><Input.TextArea /></Form.Item>
          <Form.Item name="requirements" label="任职要求"><Input.TextArea /></Form.Item>
        </Form>
      </Modal>

      {/* 预算Modal */}
      <Modal title="新增预算" open={budgetModal}
        onOk={async () => {
          const vals = await budgetForm.validateFields();
          await contractAPI.createBudget(vals);
          message.success('保存成功'); setBudgetModal(false); fetchData();
        }} onCancel={() => setBudgetModal(false)}>
        <Form form={budgetForm} layout="vertical">
          <Form.Item name="year" label="年份"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="department_id" label="部门ID"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="category" label="类别"><Input /></Form.Item>
          <Form.Item name="budget_amount" label="预算金额"><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
