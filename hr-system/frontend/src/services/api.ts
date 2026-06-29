/** API 服务层 */
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

// 请求拦截器 - 添加 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ========== 认证 ==========
export const authAPI = {
  login: (data: { username: string; password: string }) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// ========== 仪表盘 ==========
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
};

// ========== 员工 ==========
export const employeeAPI = {
  list: (params?: Record<string, any>) => api.get('/employees', { params }),
  get: (id: number) => api.get(`/employees/${id}`),
  create: (data: any) => api.post('/employees', data),
  update: (id: number, data: any) => api.put(`/employees/${id}`, data),
  delete: (id: number) => api.delete(`/employees/${id}`),
  import: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/employees/import', form);
  },
};

// ========== 部门 & 岗位 ==========
export const departmentAPI = {
  list: () => api.get('/departments'),
  create: (data: any) => api.post('/departments', data),
  update: (id: number, data: any) => api.put(`/departments/${id}`, data),
  delete: (id: number) => api.delete(`/departments/${id}`),
};

export const positionAPI = {
  list: (deptId?: number) => api.get('/positions', { params: deptId ? { department_id: deptId } : {} }),
  create: (data: any) => api.post('/positions', data),
  update: (id: number, data: any) => api.put(`/positions/${id}`, data),
};

// ========== 招聘 ==========
export const recruitmentAPI = {
  listJobs: (params?: any) => api.get('/recruitment/jobs', { params }),
  createJob: (data: any) => api.post('/recruitment/jobs', data),
  updateJob: (id: number, data: any) => api.put(`/recruitment/jobs/${id}`, data),
  listCandidates: (params?: any) => api.get('/recruitment/candidates', { params }),
  createCandidate: (data: any) => api.post('/recruitment/candidates', data),
  updateCandidate: (id: number, data: any) => api.put(`/recruitment/candidates/${id}`, data),
  getStats: () => api.get('/recruitment/stats'),
};

// ========== 培训 ==========
export const trainingAPI = {
  listPlans: (params?: any) => api.get('/training/plans', { params }),
  createPlan: (data: any) => api.post('/training/plans', data),
  updatePlan: (id: number, data: any) => api.put(`/training/plans/${id}`, data),
  listRecords: (params?: any) => api.get('/training/records', { params }),
  createRecord: (data: any) => api.post('/training/records', data),
  updateRecord: (id: number, data: any) => api.put(`/training/records/${id}`, data),
};

// ========== 绩效 ==========
export const performanceAPI = {
  listPlans: (params?: any) => api.get('/performance/plans', { params }),
  createPlan: (data: any) => api.post('/performance/plans', data),
  updatePlan: (id: number, data: any) => api.put(`/performance/plans/${id}`, data),
  listItems: (planId: number) => api.get(`/performance/plans/${planId}/items`),
  createItem: (planId: number, data: any) => api.post(`/performance/plans/${planId}/items`, data),
  listAssessments: (params?: any) => api.get('/performance/assessments', { params }),
  createAssessment: (data: any) => api.post('/performance/assessments', data),
  updateAssessment: (id: number, data: any) => api.put(`/performance/assessments/${id}`, data),
  createScore: (data: any) => api.post('/performance/scores', data),
  getStats: (year?: number) => api.get('/performance/stats', { params: year ? { year } : {} }),
};

// ========== 薪酬 ==========
export const payrollAPI = {
  list: (params?: any) => api.get('/payroll/list', { params }),
  create: (data: any) => api.post('/payroll/create', data),
  update: (id: number, data: any) => api.put(`/payroll/${id}`, data),
  confirm: (id: number) => api.put(`/payroll/${id}/confirm`),
  batchGenerate: (year: number, month: number, deptId?: number) =>
    api.post(`/payroll/batch-generate/${year}/${month}`, null, { params: deptId ? { department_id: deptId } : {} }),
  getSummary: (year: number, month: number) => api.get('/payroll/summary', { params: { year, month } }),
  listSocialInsurance: (city?: string) => api.get('/payroll/social-insurance', { params: city ? { city } : {} }),
  createSocialInsurance: (data: any) => api.post('/payroll/social-insurance', data),
};

// ========== 劳动关系 ==========
export const contractAPI = {
  list: (params?: any) => api.get('/contracts', { params }),
  create: (data: any) => api.post('/contracts', data),
  update: (id: number, data: any) => api.put(`/contracts/${id}`, data),
  getExpiring: () => api.get('/contracts/expiring'),
  listOnboarding: (empId?: number) => api.get('/contracts/onboarding', { params: empId ? { employee_id: empId } : {} }),
  createOnboarding: (data: any) => api.post('/contracts/onboarding', data),
  updateOnboarding: (id: number, data: any) => api.put(`/contracts/onboarding/${id}`, data),
  listResignation: (empId?: number) => api.get('/contracts/resignation', { params: empId ? { employee_id: empId } : {} }),
  createResignation: (data: any) => api.post('/contracts/resignation', data),
  updateResignation: (id: number, data: any) => api.put(`/contracts/resignation/${id}`, data),
  listBudget: (year?: number) => api.get('/contracts/budget', { params: year ? { year } : {} }),
  createBudget: (data: any) => api.post('/contracts/budget', data),
};

export default api;
