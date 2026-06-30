import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, theme, Dropdown, Avatar } from 'antd';
import {
  DashboardOutlined, TeamOutlined, IdcardOutlined, SafetyOutlined,
  BookOutlined, TrophyOutlined, DollarOutlined, FileProtectOutlined,
  SettingOutlined, LogoutOutlined, UserOutlined,
  ApartmentOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuth } from '../stores/useAuth';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  { key: '/employees', icon: <TeamOutlined />, label: '员工档案' },
  { key: '/hr-planning', icon: <ApartmentOutlined />, label: '人力资源规划' },
  {
    key: 'recruitment', icon: <IdcardOutlined />, label: '招聘管理',
    children: [
      { key: '/recruitment/jobs', label: '招聘岗位' },
      { key: '/recruitment/candidates', label: '候选人管理' },
    ],
  },
  {
    key: 'training', icon: <BookOutlined />, label: '培训管理',
    children: [
      { key: '/training/plans', label: '培训计划' },
      { key: '/training/records', label: '培训记录' },
    ],
  },
  {
    key: 'performance', icon: <TrophyOutlined />, label: '绩效管理',
    children: [
      { key: '/performance/plans', label: '考核方案' },
      { key: '/performance/assessments', label: '考核记录' },
    ],
  },
  {
    key: 'payroll', icon: <DollarOutlined />, label: '薪酬管理',
    children: [
      { key: '/payroll/list', label: '工资表' },
      { key: '/payroll/summary', label: '社保配置' },
      { key: '/payroll/templates', label: '薪资模板' },
      { key: '/payroll/dashboard', label: '薪酬分析' },
    ],
  },
  {
    key: 'contracts', icon: <FileProtectOutlined />, label: '劳动关系',
    children: [
      { key: '/contracts/list', label: '劳动合同' },
      { key: '/contracts/onboarding', label: '入职管理' },
      { key: '/contracts/resignation', label: '离职管理' },
    ],
  },
  { key: '/system', icon: <SettingOutlined />, label: '系统设置', roles: ['admin'] },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

  // 根据角色过滤菜单
  const visibleMenuItems = menuItems.filter(item => {
    if ('roles' in item && Array.isArray(item.roles)) {
      return item.roles.includes(user?.role || '');
    }
    return true;
  });
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

  const handleMenuClick = ({ key }: { key: string }) => navigate(key);

  const getOpenKeys = () => {
    const path = location.pathname;
    for (const item of menuItems) {
      if ('children' in item && item.children) {
        for (const child of item.children) {
          if (path.startsWith(child.key)) return [item.key as string];
        }
      }
    }
    return [];
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed} theme="dark">
        <div style={{ height: 48, margin: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <SafetyOutlined style={{ fontSize: 24, color: '#1677ff' }} />
          {!collapsed && <span style={{ color: '#fff', marginLeft: 8, fontWeight: 600, whiteSpace: 'nowrap' }}>寄居蟹一代</span>}
        </div>
        <Menu
          theme="dark" mode="inline" selectedKeys={[location.pathname]}
          defaultOpenKeys={getOpenKeys()}
          items={visibleMenuItems} onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)} style={{ fontSize: 16 }} />
          <Dropdown menu={{ items: [{ key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout }] }}>
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.username || '用户'}</span>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: colorBgContainer, borderRadius: borderRadiusLG, minHeight: 280, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
