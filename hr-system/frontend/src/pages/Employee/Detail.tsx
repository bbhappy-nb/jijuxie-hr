import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Spin, Tag, Space } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { employeeAPI } from '../../services/api';

export default function EmployeeDetail() {
  const { id } = useParams<{ id: string }>();
  const [emp, setEmp] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      employeeAPI.get(parseInt(id)).then(({ data }) => {
        setEmp(data);
        setLoading(false);
      }).catch(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!emp) return <div>员工不存在</div>;

  const statusColor = emp.status === '在职' ? 'green' : emp.status === '试用期' ? 'blue' : emp.status === '离职' ? 'red' : 'default';

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/employees')}>返回列表</Button>
        <h2 style={{ margin: 0 }}>员工详情 - {emp.name}</h2>
        <Tag color={statusColor}>{emp.status}</Tag>
      </Space>

      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="工号">{emp.employee_no}</Descriptions.Item>
          <Descriptions.Item label="姓名">{emp.name}</Descriptions.Item>
          <Descriptions.Item label="性别">{emp.gender}</Descriptions.Item>
          <Descriptions.Item label="手机号">{emp.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{emp.email || '-'}</Descriptions.Item>
          <Descriptions.Item label="身份证号">{emp.id_card || '-'}</Descriptions.Item>
          <Descriptions.Item label="出生日期">{emp.birthday || '-'}</Descriptions.Item>
          <Descriptions.Item label="学历">{emp.education || '-'}</Descriptions.Item>
          <Descriptions.Item label="专业">{emp.major || '-'}</Descriptions.Item>
          <Descriptions.Item label="毕业院校">{emp.school || '-'}</Descriptions.Item>
          <Descriptions.Item label="现住址">{emp.address || '-'}</Descriptions.Item>
          <Descriptions.Item label="紧急联系人">{emp.emergency_contact || '-'}</Descriptions.Item>
          <Descriptions.Item label="紧急联系电话">{emp.emergency_phone || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="工作信息" style={{ marginBottom: 16 }}>
        <Descriptions column={3} bordered size="small">
          <Descriptions.Item label="部门">{emp.department_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="岗位">{emp.position_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="员工状态"><Tag color={statusColor}>{emp.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="入职日期">{emp.hire_date || '-'}</Descriptions.Item>
          <Descriptions.Item label="转正日期">{emp.probation_end || '-'}</Descriptions.Item>
          <Descriptions.Item label="离职日期">{emp.resign_date || '-'}</Descriptions.Item>
          <Descriptions.Item label="基本工资">¥{(emp.base_salary || 0).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="银行卡号">{emp.bank_account || '-'}</Descriptions.Item>
          <Descriptions.Item label="开户行">{emp.bank_name || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
