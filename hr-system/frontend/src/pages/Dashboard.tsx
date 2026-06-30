import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Spin } from 'antd';
import {
  TeamOutlined, UserAddOutlined, UserDeleteOutlined,
  FileProtectOutlined, TrophyOutlined, DollarOutlined,
  PieChartOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { dashboardAPI } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [extended, setExtended] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([dashboardAPI.getStats(), dashboardAPI.getExtended()]).then(([s, e]) => {
      setStats(s.data);
      setExtended(e.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!stats) return <div>加载失败</div>;

  const deptOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
      data: stats.department_distribution || [],
      label: { show: true, formatter: '{b}: {c}' },
    }],
  };

  const payrollOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: (stats.monthly_payroll_trend || []).map((i: any) => i.month) },
    yAxis: { type: 'value' },
    series: [{
      type: 'line', smooth: true, data: (stats.monthly_payroll_trend || []).map((i: any) => i.amount),
      areaStyle: {}, itemStyle: { color: '#1677ff' },
    }],
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>工作台</h2>

      {/* 人事 KPI */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="员工总数" value={stats.total_employees} prefix={<TeamOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="在职员工" value={stats.active_employees} prefix={<TeamOutlined />} valueStyle={{ color: '#3f8600' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="本月入职" value={stats.month_onboarding} prefix={<UserAddOutlined />} valueStyle={{ color: '#1677ff' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="本月离职" value={stats.month_resignation} prefix={<UserDeleteOutlined />} valueStyle={{ color: '#cf1322' }} /></Card>
        </Col>
      </Row>

      {/* 薪酬绩效 KPI */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="合同到期" value={stats.contract_expiring} prefix={<FileProtectOutlined />} valueStyle={{ color: '#faad14' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="待考核" value={stats.pending_assessments} prefix={<TrophyOutlined />} valueStyle={{ color: '#ff7a45' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="待确认工资" value={extended?.pending_confirm || 0} prefix={<DollarOutlined />} valueStyle={{ color: '#faad14' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="待发薪" value={extended?.pending_pay || 0} prefix={<PieChartOutlined />} valueStyle={{ color: '#cf1322' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="考核完成率" value={extended?.completion_rate || 0} suffix="%" prefix={<CheckCircleOutlined />} valueStyle={{ color: '#3f8600' }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card><Statistic title="本月薪酬" value={extended?.total_net_salary || 0} prefix="¥" precision={0} /></Card>
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="部门人员分布"><ReactECharts option={deptOption} style={{ height: 350 }} /></Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="近12个月薪酬趋势"><ReactECharts option={payrollOption} style={{ height: 350 }} /></Card>
        </Col>
      </Row>
    </div>
  );
}
