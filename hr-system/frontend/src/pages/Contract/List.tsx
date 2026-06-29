import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, DatePicker, message, Tag, Alert } from 'antd';
import { PlusOutlined, EditOutlined, WarningOutlined } from '@ant-design/icons';
import { contractAPI } from '../../services/api';
import dayjs from 'dayjs';

export default function ContractList() {
  const [data, setData] = useState<any[]>([]);
  const [expiring, setExpiring] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchData = () => {
    setLoading(true);
    contractAPI.list({ page, page_size: 20 })
      .then(({ data }) => { setData(data.items); setTotal(data.total); })
      .finally(() => setLoading(false));
    contractAPI.getExpiring().then(({ data }) => setExpiring(Array.isArray(data) ? data : []));
  };

  useEffect(() => { fetchData(); }, [page]);

  const columns = [
    { title: '员工', dataIndex: 'employee_name' },
    { title: '合同编号', dataIndex: 'contract_no' },
    {
      title: '类型', dataIndex: 'type',
      render: (v: string) => <Tag>{v}</Tag>,
    },
    { title: '开始日期', dataIndex: 'start_date' },
    { title: '结束日期', dataIndex: 'end_date' },
    { title: '试用期(月)', dataIndex: 'probation_months' },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => {
        const color = v === '有效' ? 'green' : v === '即将到期' ? 'orange' : v === '已到期' ? 'red' : 'default';
        return <Tag color={color}>{v}</Tag>;
      },
    },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => {
          setEditing(r);
          form.setFieldsValue({ ...r, start_date: r.start_date ? dayjs(r.start_date) : null, end_date: r.end_date ? dayjs(r.end_date) : null, sign_date: r.sign_date ? dayjs(r.sign_date) : null });
          setModalOpen(true);
        }}>编辑</Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>劳动合同管理</h2>
      {expiring.length > 0 && (
        <Alert type="warning" showIcon icon={<WarningOutlined />}
          message={`有 ${expiring.length} 份合同即将到期`}
          description={expiring.map(e => `${e.employee_name}: ${e.end_date} (剩余${e.days_left}天)`).join('; ')}
          style={{ marginBottom: 16 }} />
      )}
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          新增合同
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading}
        pagination={{ current: page, pageSize: 20, total, onChange: (p) => setPage(p) }} />

      <Modal title={editing ? '编辑合同' : '新增合同'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          const payload = {
            ...vals,
            start_date: vals.start_date?.format('YYYY-MM-DD'),
            end_date: vals.end_date?.format('YYYY-MM-DD'),
            sign_date: vals.sign_date?.format('YYYY-MM-DD'),
          };
          if (editing) { await contractAPI.update(editing.id, payload); }
          else { await contractAPI.create(payload); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="employee_id" label="员工ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="合同类型"><Select options={[
            { label: '固定期限', value: '固定期限' }, { label: '无固定期限', value: '无固定期限' },
            { label: '项目合同', value: '项目合同' }, { label: '实习协议', value: '实习协议' },
          ]} /></Form.Item>
          <Form.Item name="start_date" label="开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="probation_months" label="试用期(月)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          {editing && (
            <>
              <Form.Item name="status" label="状态"><Select options={[
                { label: '有效', value: '有效' }, { label: '即将到期', value: '即将到期' },
                { label: '已到期', value: '已到期' }, { label: '已解除', value: '已解除' },
              ]} /></Form.Item>
              <Form.Item name="termination_reason" label="解除原因"><Input.TextArea /></Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
}
