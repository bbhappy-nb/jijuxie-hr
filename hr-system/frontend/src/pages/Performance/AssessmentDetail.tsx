/** 绩效评估详情 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Table, Tag, Button, Spin, Space, Divider } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { performanceAPI } from '../../services/api';

export default function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    performanceAPI.getAssessmentDetail(Number(id)).then((res) => {
      setData(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!data) return <div style={{ textAlign: 'center', padding: 100 }}>未找到评估记录</div>;

  const gradeColors: Record<string, string> = { S: 'purple', A: 'green', B: 'blue', C: 'orange', D: 'red' };
  const statusColors: Record<string, string> = { '待考核': 'default', '已完成': 'processing', '已确认': 'success' };

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
      </Space>

      <Card>
        <Descriptions title={data.plan?.name} bordered size="small" column={2}>
          <Descriptions.Item label="被考核人">{data.employee?.name}</Descriptions.Item>
          <Descriptions.Item label="部门">{data.employee?.department}</Descriptions.Item>
          <Descriptions.Item label="考核周期">{data.plan?.period}</Descriptions.Item>
          <Descriptions.Item label="考核类型">{data.plan?.type}</Descriptions.Item>
          <Descriptions.Item label="总分">
            <span style={{ fontSize: 18, fontWeight: 'bold' }}>{data.total_score}</span>
          </Descriptions.Item>
          <Descriptions.Item label="等级">
            <Tag color={gradeColors[data.grade]} style={{ fontSize: 16, padding: '4px 12px' }}>{data.grade}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColors[data.status]}>{data.status}</Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 自评 */}
      {data.self_review && (
        <Card title="自评" style={{ marginTop: 16 }}>
          <p>{data.self_review}</p>
          <Tag>{data.self_review_status}</Tag>
        </Card>
      )}

      {/* 指标评分 */}
      <Card title="指标评分明细" style={{ marginTop: 16 }}>
        <Table
          dataSource={data.scores || []}
          rowKey="id"
          size="small"
          columns={[
            { title: '指标', dataIndex: 'item_name' },
            { title: '权重', dataIndex: 'weight', render: (v: number) => `${v}%` },
            { title: '得分', dataIndex: 'score' },
            { title: '评语', dataIndex: 'comment' },
          ]}
          pagination={false}
        />
      </Card>

      {/* 360评估人 */}
      {data.evaluators?.length > 0 && (
        <Card title="360度评估人" style={{ marginTop: 16 }}>
          <Table
            dataSource={data.evaluators}
            rowKey="id"
            size="small"
            columns={[
              { title: '评估人', dataIndex: 'evaluator_name' },
              { title: '类型', dataIndex: 'evaluator_type', render: (v: string) => <Tag>{v}</Tag> },
              { title: '权重', dataIndex: 'weight', render: (v: number) => `${v}%` },
              { title: '打分', dataIndex: 'total_score' },
              { title: '评级', dataIndex: 'grade', render: (g: string) => <Tag color={gradeColors[g]}>{g}</Tag> },
              { title: '评语', dataIndex: 'comment' },
              { title: '状态', dataIndex: 'status', render: (s: string) => <Tag color={statusColors[s]}>{s}</Tag> },
            ]}
            pagination={false}
          />
        </Card>
      )}

      {/* 考核评语 */}
      {data.evaluator_comment && (
        <Card title="考核评语" style={{ marginTop: 16 }}>
          <p>{data.evaluator_comment}</p>
        </Card>
      )}
    </div>
  );
}
