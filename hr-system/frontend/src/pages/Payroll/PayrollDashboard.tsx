/** 薪酬分析大屏 */
import { useEffect, useState } from 'react';
import { Card, Row, Col, Table, Statistic, Spin, Select, DatePicker } from 'antd';
import { DollarOutlined, TeamOutlined, RiseOutlined, PieChartOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { payrollAPI } from '../../services/api';

export default function PayrollDashboard() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [summary, setSummary] = useState<any>(null);
  const [deptCost, setDeptCost] = useState<any[]>([]);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      payrollAPI.getSummary(year, month),
      payrollAPI.getDepartmentCost(year, month),
      payrollAPI.getTrends(year),
    ]).then(([sum, cost, trend]) => {
      setSummary(sum.data);
      setDeptCost(cost.data || []);
      setTrends(trend.data?.trends || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [year, month]);

  const deptPieOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      data: deptCost.map((d: any) => ({ name: d.department_name || '未分配', value: d.total_net })),
      label: { formatter: '{b}: {d}%' },
    }],
  };

  const trendOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['实发工资(当年)', '应发工资(当年)', '实发工资(去年同期)'] },
    xAxis: { type: 'category', data: trends.map((t: any) => t.label) },
    yAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${(v / 10000).toFixed(0)}万` } },
    series: [
      { name: '实发工资(当年)', type: 'bar', data: trends.map((t: any) => t.net_salary), itemStyle: { color: '#1677ff' } },
      { name: '应发工资(当年)', type: 'bar', data: trends.map((t: any) => t.total_income), itemStyle: { color: '#69b1ff' } },
      { name: '实发工资(去年同期)', type: 'line', data: trends.map((t: any) => t.prior_net), itemStyle: { color: '#ff7a45' } },
    ],
  };

  return (
    <Spin spinning={loading}>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card><Statistic title="发薪人数" value={summary?.employee_count || 0} prefix={<TeamOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="应发合计" value={summary?.total_income || 0} precision={2} prefix={<DollarOutlined />} suffix="元" /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="个税合计" value={summary?.total_tax || 0} precision={2} prefix={<RiseOutlined />} suffix="元" valueStyle={{ color: '#cf1322' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="实发合计" value={summary?.total_net_salary || 0} precision={2} prefix={<PieChartOutlined />} suffix="元" /></Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={2}><Select value={year} onChange={setYear} options={[...Array(5)].map((_, i) => ({ value: new Date().getFullYear() - i, label: `${new Date().getFullYear() - i}年` }))} /></Col>
        <Col span={2}><Select value={month} onChange={setMonth} options={[...Array(12)].map((_, i) => ({ value: i + 1, label: `${i + 1}月` }))} /></Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}><Card title="部门薪酬成本分布"><ReactECharts option={deptPieOption} style={{ height: 350 }} /></Card></Col>
        <Col span={12}><Card title="月度薪酬趋势"><ReactECharts option={trendOption} style={{ height: 350 }} /></Card></Col>
      </Row>

      <Card title="部门明细" style={{ marginTop: 16 }}>
        <Table
          dataSource={deptCost}
          rowKey="department_id"
          columns={[
            { title: '部门', dataIndex: 'department_name' },
            { title: '人数', dataIndex: 'headcount' },
            { title: '应发合计', dataIndex: 'total_income', render: (v: number) => `¥${v?.toFixed(2)}` },
            { title: '实发合计', dataIndex: 'total_net', render: (v: number) => `¥${v?.toFixed(2)}` },
          ]}
          pagination={false}
          size="small"
        />
      </Card>
    </Spin>
  );
}
