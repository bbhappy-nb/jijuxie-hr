import { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, InputNumber, DatePicker, Checkbox, message, Tag, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { contractAPI } from '../../services/api';
import dayjs from 'dayjs';

const CHECKLIST_KEYS = ['id_card_copy', 'education_cert', 'photo', 'bank_card', 'health_check', 'resignation_cert', 'signed_contract'];

export default function ContractOnboarding() {
  const [data, setData] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchData = () => {
    contractAPI.listOnboarding().then(({ data }) => setData(Array.isArray(data) ? data : []));
  };

  useEffect(() => { fetchData(); }, []);

  const columns = [
    { title: '员工', dataIndex: 'employee_name' },
    { title: '入职日期', dataIndex: 'onboard_date' },
    {
      title: '身份证', dataIndex: 'id_card_copy',
      render: (v: number) => v ? <Tag color="green">已交</Tag> : <Tag color="red">未交</Tag>,
    },
    {
      title: '学历证书', dataIndex: 'education_cert',
      render: (v: number) => v ? <Tag color="green">已交</Tag> : <Tag color="red">未交</Tag>,
    },
    {
      title: '银行卡', dataIndex: 'bank_card',
      render: (v: number) => v ? <Tag color="green">已交</Tag> : <Tag color="red">未交</Tag>,
    },
    {
      title: '体检报告', dataIndex: 'health_check',
      render: (v: number) => v ? <Tag color="green">已交</Tag> : <Tag color="red">未交</Tag>,
    },
    {
      title: '合同签署', dataIndex: 'signed_contract',
      render: (v: number) => v ? <Tag color="green">已签</Tag> : <Tag color="red">未签</Tag>,
    },
    {
      title: '状态', dataIndex: 'status',
      render: (v: string) => <Tag color={v === '已完成' ? 'green' : 'orange'}>{v}</Tag>,
    },
    {
      title: '操作', render: (_: any, r: any) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => {
          setEditing(r);
          form.setFieldsValue({ ...r, onboard_date: r.onboard_date ? dayjs(r.onboard_date) : null });
          setModalOpen(true);
        }}>编辑</Button>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>入职管理</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModalOpen(true); }}>
          新员工入职
        </Button>
      </Space>
      <Table columns={columns} dataSource={data} rowKey="id" pagination={false} />

      <Modal title={editing ? '编辑入职记录' : '新员工入职'} open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          const payload = { ...vals, onboard_date: vals.onboard_date?.format('YYYY-MM-DD') };
          if (editing) { await contractAPI.updateOnboarding(editing.id, payload); }
          else { await contractAPI.createOnboarding(payload); }
          message.success('保存成功'); setModalOpen(false); fetchData();
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="employee_id" label="员工ID" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="onboard_date" label="入职日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Row gutter={16}>
            {CHECKLIST_KEYS.map(key => (
              <Col span={12} key={key}>
                <Form.Item name={key} valuePropName="checked">
                  <Checkbox>{{
                    id_card_copy: '身份证复印件', education_cert: '学历证书', photo: '照片',
                    bank_card: '银行卡', health_check: '体检报告', resignation_cert: '离职证明', signed_contract: '已签合同',
                  }[key]}</Checkbox>
                </Form.Item>
              </Col>
            ))}
          </Row>
          <Form.Item name="computer" label="电脑"><InputNumber style={{ width: '100%' }} placeholder="设备编号" /></Form.Item>
          <Form.Item name="office_supplies" label="办公用品"><InputNumber style={{ width: '100%' }} placeholder="领用清单" /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
