import { useEffect, useState } from 'react';
import { Card, Table, Button, Modal, Form, InputNumber, Input, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { payrollAPI } from '../../services/api';

export default function PayrollSummary() {
  const [siList, setSiList] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    payrollAPI.listSocialInsurance().then(({ data }) => setSiList(data));
  }, []);

  const siColumns = [
    { title: '城市', dataIndex: 'city' },
    { title: '年份', dataIndex: 'year' },
    { title: '养老基数', render: (_: any, r: any) => `${r.pension_base_min}-${r.pension_base_max}` },
    { title: '养老(个人)', dataIndex: 'pension_personal', render: (v: number) => `${v}%` },
    { title: '医疗(个人)', dataIndex: 'medical_personal', render: (v: number) => `${v}%` },
    { title: '失业(个人)', dataIndex: 'unemployment_personal', render: (v: number) => `${v}%` },
    { title: '公积金(个人)', dataIndex: 'housing_fund_personal', render: (v: number) => `${v}%` },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>薪酬汇总与社保设置</h2>

      <Card title="社保公积金配置" style={{ marginBottom: 16 }}
        extra={<Button icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalOpen(true); }}>新增城市配置</Button>}>
        <Table columns={siColumns} dataSource={siList} rowKey="id" pagination={false} size="small" />
      </Card>

      <Modal title="社保公积金配置" open={modalOpen}
        onOk={async () => {
          const vals = await form.validateFields();
          await payrollAPI.createSocialInsurance(vals);
          message.success('保存成功'); setModalOpen(false);
          payrollAPI.listSocialInsurance().then(({ data }) => setSiList(data));
        }} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="city" label="城市" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="year" label="年份"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="pension_base_min" label="养老基数下限"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="pension_base_max" label="养老基数上限"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="pension_personal" label="养老个人比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="pension_company" label="养老单位比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="medical_personal" label="医疗个人比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="medical_company" label="医疗单位比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="unemployment_personal" label="失业个人比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="housing_fund_personal" label="公积金个人比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="housing_fund_company" label="公积金单位比例(%)"><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
