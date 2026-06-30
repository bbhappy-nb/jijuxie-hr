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
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>工作台</h2>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: 14 }}>欢迎回来，{new Date().getHours() < 12 ? '上午好' : new Date().getHours() < 18 ? '下午好' : '晚上好'}</p>
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {[
          { title: '员工总数', value: stats.total_employees, icon: <TeamOutlined />, color: '#2b5aed' },
          { title: '在职员工', value: stats.active_employees, icon: <TeamOutlined />, color: '#10b981' },
          { title: '本月入职', value: stats.month_onboarding, icon: <UserAddOutlined />, color: '#6366f1' },
          { title: '本月离职', value: stats.month_resignation, icon: <UserDeleteOutlined />, color: '#f43f5e' },
          { title: '合同到期', value: stats.contract_expiring, icon: <FileProtectOutlined />, color: '#f59e0b' },
          { title: '待考核', value: stats.pending_assessments, icon: <TrophyOutlined />, color: '#8b5cf6' },
          { title: '待确认工资', value: extended?.pending_confirm || 0, icon: <DollarOutlined />, color: '#f59e0b' },
          { title: '待发薪', value: extended?.pending_pay || 0, icon: <PieChartOutlined />, color: '#ef4444' },
          { title: '考核完成率', value: `${extended?.completion_rate || 0}%`, icon: <CheckCircleOutlined />, color: '#10b981' },
          { title: '本月实发薪酬', value: `¥${((extended?.total_net_salary || 0) / 10000).toFixed(1)}万`, icon: <DollarOutlined />, color: '#2b5aed' },
        ].map((stat, i) => (
          <Col xs={24} sm={12} md={8} lg={6} xl={4} key={i}>
            <Card
              style={{ borderRadius: 12, border: '1px solid #f1f5f9', transition: 'box-shadow 0.2s' }}
              bodyStyle={{ padding: '20px 24px' }}
              hoverable
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>{stat.title}</div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: '#1e293b' }}>{stat.value}</div>
                </div>
                <div style={{
                  width: 40, height: 40, borderRadius: 10, background: `${stat.color}10`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: stat.color, fontSize: 18,
                }}>{stat.icon}</div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="部门人员分布" style={{ borderRadius: 12 }}><ReactECharts option={deptOption} style={{ height: 350 }} /></Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="近12个月薪酬趋势" style={{ borderRadius: 12 }}><ReactECharts option={payrollOption} style={{ height: 350 }} /></Card>
        </Col>
      </Row>
    </div>
  );
}
