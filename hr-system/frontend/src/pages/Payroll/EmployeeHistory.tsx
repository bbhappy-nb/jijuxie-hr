/** 员工薪酬历史 */
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Table, Tag, Descriptions, Spin } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { payrollAPI } from '../../services/api';

export default function EmployeeHistory() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!employeeId) return;
    payrollAPI.getEmployeeHistory(Number(employeeId)).then((res) => {
      setData(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [employeeId]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!data?.employee) return <div style={{ textAlign: 'center', padding: 100 }}>未找到员工薪酬记录</div>;

  const trendOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.trend?.map((t: any) => t.label) || [] },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}元' } },
    series: [
      { name: '应发', type: 'bar', data: data.trend?.map((t: any) => t.total_income) || [], itemStyle: { color: '#69b1ff' } },
      { name: '实发', type: 'line', data: data.trend?.map((t: any) => t.net_salary) || [], itemStyle: { color: '#1677ff' } },
    ],
  };

  const statusColors: Record<string, string> = { '草稿': 'default', '已确认': 'processing', '已发放': 'success' };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Descriptions title={`${data.employee?.name} (${data.employee?.employee_no}) 薪酬档案`} bordered size="small">
          <Descriptions.Item label="累计记录">{data.total_records} 条</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="薪酬趋势" style={{ marginTop: 16 }}>
        <ReactECharts option={trendOption} style={{ height: 300 }} />
      </Card>

      <Card title="薪酬明细" style={{ marginTop: 16 }}>
        <Table
          dataSource={data.history || []}
          rowKey="id"
          size="small"
          columns={[
            { title: '年月', render: (_, r: any) => `${r.year}/${r.month}` },
            { title: '基本工资', dataIndex: 'base_salary', render: (v: number) => `¥${v?.toFixed(2)}` },
            { title: '绩效奖金', dataIndex: 'performance_bonus', render: (v: number) => `¥${v?.toFixed(2)}` },
            { title: '应发合计', dataIndex: 'total_income', render: (v: number) => `¥${v?.toFixed(2)}` },
            { title: '个税', dataIndex: 'tax', render: (v: number) => `¥${v?.toFixed(2)}` },
            { title: '实发', dataIndex: 'net_salary', render: (v: number) => <strong>¥{v?.toFixed(2)}</strong> },
            { title: '状态', dataIndex: 'status', render: (s: string) => <Tag color={statusColors[s]}>{s}</Tag> },
            { title: '发放时间', dataIndex: 'paid_at' },
          ]}
        />
      </Card>
    </div>
  );
}
