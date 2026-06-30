/** 工资条详情 — 可打印 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Table, Tag, Button, Space, Spin, Divider } from 'antd';
import { PrinterOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { payrollAPI } from '../../services/api';

export default function Payslip() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    payrollAPI.getPayslip(Number(id)).then((res) => {
      setData(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!data) return <div style={{ textAlign: 'center', padding: 100 }}>未找到工资条</div>;

  const statusColors: Record<string, string> = { '草稿': 'default', '已确认': 'processing', '已发放': 'success' };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 24 }} className="payslip-print">
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
        <Button type="primary" icon={<PrinterOutlined />} onClick={() => window.print()}>打印</Button>
      </Space>

      <Card bordered style={{ fontFamily: '"SimSun", "宋体", serif' }}>
        {/* 头部 */}
        <div style={{ textAlign: 'center', borderBottom: '2px solid #000', paddingBottom: 16, marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>工资条</h2>
          <p style={{ margin: '4px 0', color: '#666' }}>{data.year} 年 {data.month} 月</p>
        </div>

        {/* 员工信息 */}
        <Descriptions column={4} size="small" bordered style={{ marginBottom: 16 }}>
          <Descriptions.Item label="姓名">{data.employee?.name}</Descriptions.Item>
          <Descriptions.Item label="工号">{data.employee?.employee_no}</Descriptions.Item>
          <Descriptions.Item label="部门">{data.employee?.department}</Descriptions.Item>
          <Descriptions.Item label="岗位">{data.employee?.position}</Descriptions.Item>
        </Descriptions>

        {/* 收入项 */}
        <h4>收入项目</h4>
        <Table
          dataSource={data.income_items?.map((it: any, i: number) => ({ ...it, key: i })) || []}
          columns={[
            { title: '项目', dataIndex: 'name', key: 'name' },
            { title: '金额 (元)', dataIndex: 'amount', key: 'amount', render: (v: number) => v?.toFixed(2) },
          ]}
          pagination={false}
          size="small"
          summary={() => (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0}><strong>应发合计</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={1}><strong style={{ fontSize: 16, color: '#1677ff' }}>¥ {data.total_income?.toFixed(2)}</strong></Table.Summary.Cell>
            </Table.Summary.Row>
          )}
          style={{ marginBottom: 16 }}
        />

        {/* 扣款项 */}
        <h4>扣除项目</h4>
        <Table
          dataSource={data.deduction_items?.map((it: any, i: number) => ({ ...it, key: i })) || []}
          columns={[
            { title: '项目', dataIndex: 'name', key: 'name' },
            { title: '金额 (元)', dataIndex: 'amount', key: 'amount', render: (v: number) => v?.toFixed(2) },
          ]}
          pagination={false}
          size="small"
          summary={() => (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0}><strong>扣款合计</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={1}><strong>¥ {data.total_deduction?.toFixed(2)}</strong></Table.Summary.Cell>
            </Table.Summary.Row>
          )}
          style={{ marginBottom: 16 }}
        />

        {/* 实发 */}
        <Divider />
        <div style={{ textAlign: 'center', padding: '12px 0' }}>
          <span style={{ fontSize: 14 }}>实发工资：</span>
          <span style={{ fontSize: 28, fontWeight: 'bold', color: '#1677ff' }}>¥ {data.net_salary?.toFixed(2)}</span>
        </div>
        <Divider />

        {/* 状态和备注 */}
        <Space>
          <Tag color={statusColors[data.status] || 'default'}>{data.status}</Tag>
          {data.paid_at && <span style={{ color: '#999', fontSize: 12 }}>发放时间: {data.paid_at}</span>}
        </Space>

        {/* 绩效联动信息 */}
        {data.assessment && (
          <Card size="small" title="绩效奖金来源" style={{ marginTop: 16, background: '#f9f9f9' }}>
            <p>评估等级: <Tag>{data.assessment.grade}</Tag></p>
            <p>考核得分: {data.assessment.total_score} 分</p>
            <p>奖金系数: {data.assessment.coefficient} × 基本工资 = ¥{data.assessment.bonus_amount?.toFixed(2)}</p>
          </Card>
        )}
      </Card>

      <style>{`
        @media print {
          .ant-layout-sider, .ant-layout-header, .ant-btn { display: none !important; }
          .payslip-print { padding: 0 !important; max-width: 100% !important; }
          .ant-card { border: none !important; box-shadow: none !important; }
        }
      `}</style>
    </div>
  );
}
