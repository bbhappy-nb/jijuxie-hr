import { useEffect, useState } from 'react';
import { Table, Button, Input, Select, Space, Modal, Form, message, Popconfirm, Upload, Tag } from 'antd';
import { PlusOutlined, SearchOutlined, UploadOutlined, ExportOutlined, EditOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { employeeAPI, departmentAPI } from '../../services/api';
import type { ColumnsType } from 'antd/es/table';

export default function EmployeeList() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState('');
  const [deptId, setDeptId] = useState<number | undefined>();
  const [status, setStatus] = useState<string | undefined>();
  const [departments, setDepartments] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmp, setEditingEmp] = useState<any>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchData = () => {
    setLoading(true);
    employeeAPI.list({ page, page_size: 20, keyword: keyword || undefined, department_id: deptId, status })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [page, deptId, status]);
  useEffect(() => {
    departmentAPI.list().then(({ data }) => setDepartments(data)).catch(() => {});
  }, []);

  const handleSearch = () => { setPage(1); fetchData(); };

  const handleCreate = () => {
    setEditingEmp(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditingEmp(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    await employeeAPI.delete(id);
    message.success('删除成功');
    fetchData();
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingEmp) {
      await employeeAPI.update(editingEmp.id, values);
      message.success('更新成功');
    } else {
      await employeeAPI.create(values);
      message.success('创建成功');
    }
    setModalOpen(false);
    fetchData();
  };

  const handleImport = async (file: File) => {
    await employeeAPI.import(file);
    message.success('导入成功');
    fetchData();
    return false;
  };

  const columns: ColumnsType<any> = [
    { title: '工号', dataIndex: 'employee_no', width: 100 },
    { title: '姓名', dataIndex: 'name', width: 100, render: (text, r) => <a onClick={() => navigate(`/employees/${r.id}`)}>{text}</a> },
    { title: '性别', dataIndex: 'gender', width: 60 },
    { title: '手机号', dataIndex: 'phone', width: 130 },
    { title: '部门', dataIndex: 'department_name', width: 120 },
    { title: '岗位', dataIndex: 'position_name', width: 120 },
    { title: '学历', dataIndex: 'education', width: 100 },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: (s) => {
        const color = s === '在职' ? 'green' : s === '试用期' ? 'blue' : s === '离职' ? 'red' : 'default';
        return <Tag color={color}>{s}</Tag>;
      },
    },
    { title: '入职日期', dataIndex: 'hire_date', width: 110 },
    { title: '基本工资', dataIndex: 'base_salary', width: 100, render: (v) => v ? `¥${v.toLocaleString()}` : '-' },
    {
      title: '操作', width: 180, fixed: 'right',
      render: (_, r) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/employees/${r.id}`)}>查看</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)}>编辑</Button>
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>员工档案</h2>
      <Space wrap style={{ marginBottom: 16 }}>
        <Input placeholder="姓名/工号/手机号" prefix={<SearchOutlined />} value={keyword}
          onChange={(e) => setKeyword(e.target.value)} onPressEnter={handleSearch} style={{ width: 200 }} />
        <Select placeholder="部门" allowClear style={{ width: 150 }} value={deptId}
          onChange={(v) => { setDeptId(v); setPage(1); }}
          options={departments.map((d: any) => ({ label: d.name, value: d.id }))} />
        <Select placeholder="状态" allowClear style={{ width: 120 }} value={status}
          onChange={(v) => { setStatus(v); setPage(1); }}
          options={[{ label: '在职', value: '在职' }, { label: '试用期', value: '试用期' }, { label: '离职', value: '离职' }]} />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新增员工</Button>
        <Upload beforeUpload={handleImport} showUploadList={false} accept=".xlsx,.xls">
          <Button icon={<UploadOutlined />}>批量导入</Button>
        </Upload>
        <Button icon={<ExportOutlined />}>导出Excel</Button>
      </Space>

      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        scroll={{ x: 1400 }}
        pagination={{ current: page, pageSize: 20, total, showTotal: (t) => `共 ${t} 条`, onChange: (p) => setPage(p) }} />

      <Modal title={editingEmp ? '编辑员工' : '新增员工'} open={modalOpen}
        onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={640} destroyOnClose>
        <Form form={form} layout="vertical">
          <Form.Item name="employee_no" label="工号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="gender" label="性别"><Input /></Form.Item>
          <Form.Item name="phone" label="手机号"><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="department_id" label="部门ID"><Input type="number" /></Form.Item>
          <Form.Item name="position_id" label="岗位ID"><Input type="number" /></Form.Item>
          <Form.Item name="base_salary" label="基本工资"><Input type="number" /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
