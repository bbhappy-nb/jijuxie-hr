import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './components/MainLayout';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import EmployeeList from './pages/Employee/List';
import EmployeeDetail from './pages/Employee/Detail';
import HRPlanning from './pages/HRPlanning';
import RecruitmentJobs from './pages/Recruitment/Jobs';
import RecruitmentCandidates from './pages/Recruitment/Candidates';
import TrainingPlans from './pages/Training/Plans';
import TrainingRecords from './pages/Training/Records';
import PerformancePlans from './pages/Performance/Plans';
import PerformanceAssessments from './pages/Performance/Assessments';
import PayrollList from './pages/Payroll/List';
import PayrollSummary from './pages/Payroll/Summary';
import ContractList from './pages/Contract/List';
import ContractOnboarding from './pages/Contract/Onboarding';
import ContractResignation from './pages/Contract/Resignation';
import SystemSettings from './pages/System';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#1677ff', borderRadius: 6 } }}>
      <AntApp>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<PrivateRoute><MainLayout /></PrivateRoute>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="employees" element={<EmployeeList />} />
              <Route path="employees/:id" element={<EmployeeDetail />} />
              <Route path="hr-planning" element={<HRPlanning />} />
              <Route path="recruitment/jobs" element={<RecruitmentJobs />} />
              <Route path="recruitment/candidates" element={<RecruitmentCandidates />} />
              <Route path="training/plans" element={<TrainingPlans />} />
              <Route path="training/records" element={<TrainingRecords />} />
              <Route path="performance/plans" element={<PerformancePlans />} />
              <Route path="performance/assessments" element={<PerformanceAssessments />} />
              <Route path="payroll/list" element={<PayrollList />} />
              <Route path="payroll/summary" element={<PayrollSummary />} />
              <Route path="contracts/list" element={<ContractList />} />
              <Route path="contracts/onboarding" element={<ContractOnboarding />} />
              <Route path="contracts/resignation" element={<ContractResignation />} />
              <Route path="system" element={<SystemSettings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}
