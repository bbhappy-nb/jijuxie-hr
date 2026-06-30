/** 员工绩效轨迹 */
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Table, Tag, Spin, Row, Col, Descriptions } from 'antd';
import ReactECharts from 'echarts-for-react';
import { performanceAPI } from '../../services/api';

export default function EmployeeTimeline() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!employeeId) return;
    performanceAPI.getEmployeeTimeline(Number(employeeId)).then((res) => {
      setData(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [employeeId]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!data?.employee) return <div style={{ textAlign: 'center', padding: 100 }}>暂无绩效记录</div>;

  const gradeColors: Record<string, string> = { S: 'purple', A: 'green', B: 'blue', C: 'orange', D: 'red' };

  const radarOption = {
    tooltip: {},
    radar: {
      indicator: data.radar?.map((r: any) => ({ name: r.item_name, max: 100 })) || [],
    },
    series: [{
      type: 'radar',
      data: [{ value: data.radar?.map((r: any) => r.score) || [], name: '得分' }],
      areaStyle: { opacity: 0.2 },
    }],
  };

  const trendOption = {
    xAxis: { type: 'category', data: data.timeline?.map((t: any) => t.created_at?.slice(0, 10)).reverse() || [] },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [{
      type: 'line',
      data: data.timeline?.map((t: any) => t.total_score).reverse() || [],
      markLine: { data: [{ type: 'average', name: '平均' }] },
      itemStyle: { color: '#1677ff' },
    }],
  };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Descriptions title={`${data.employee?.name} — 绩效轨迹`} bordered size="small">
          <Descriptions.Item label="部门">{data.employee?.department}</Descriptions.Item>
          <Descriptions.Item label="累计评估">{data.total_assessments} 次</Descriptions.Item>
          <Descriptions.Item label="S">{data.grades_summary?.S || 0}次</Descriptions.Item>
          <Descriptions.Item label="A">{data.grades_summary?.A || 0}次</Descriptions.Item>
          <Descriptions.Item label="B">{data.grades_summary?.B || 0}次</Descriptions.Item>
          <Descriptions.Item label="C/D">{ (data.grades_summary?.C || 0) + (data.grades_summary?.D || 0) }次</Descriptions.Item>
        </Descriptions>
      </Card>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="最新评估雷达图"><ReactECharts option={radarOption} style={{ height: 350 }} /></Card>
        </Col>
        <Col span={12}>
          <Card title="得分趋势"><ReactECharts option={trendOption} style={{ height: 350 }} /></Card>
        </Col>
      </Row>

      <Card title="考核历史" style={{ marginTop: 16 }}>
        <Table
          dataSource={data.timeline || []}
          rowKey="id"
          size="small"
          columns={[
            { title: '考核方案', dataIndex: 'plan_name' },
            { title: '周期', dataIndex: 'period' },
            { title: '类型', dataIndex: 'type' },
            { title: '得分', dataIndex: 'total_score' },
            { title: '等级', dataIndex: 'grade', render: (g: string) => <Tag color={gradeColors[g]}>{g}</Tag> },
            { title: '状态', dataIndex: 'status', render: (s: string) => <Tag>{s}</Tag> },
            { title: '时间', dataIndex: 'created_at' },
          ]}
        />
      </Card>
    </div>
  );
}
