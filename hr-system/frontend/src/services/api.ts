/** API 服务层 */
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

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

export const authAPI = {
  login: (data: { username: string; password: string }) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getExtended: () => api.get('/dashboard/extended'),
};

export const employeeAPI = {
  list: (params?: Record<string, any>) => api.get('/employees', { params }),
  get: (id: number) => api.get(`/employees/${id}`),
  create: (data: any) => api.post('/employees', data),
  update: (id: number, data: any) => api.put(`/employees/${id}`, data),
  delete: (id: number) => api.delete(`/employees/${id}`),
  import: (file: File) => {
    const form = new FormData(); form.append('file', file);
    return api.post('/employees/import', form);
  },
};

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

export const recruitmentAPI = {
  listJobs: (params?: any) => api.get('/recruitment/jobs', { params }),
  createJob: (data: any) => api.post('/recruitment/jobs', data),
  updateJob: (id: number, data: any) => api.put(`/recruitment/jobs/${id}`, data),
  listCandidates: (params?: any) => api.get('/recruitment/candidates', { params }),
  createCandidate: (data: any) => api.post('/recruitment/candidates', data),
  updateCandidate: (id: number, data: any) => api.put(`/recruitment/candidates/${id}`, data),
  getStats: () => api.get('/recruitment/stats'),
};

export const trainingAPI = {
  listPlans: (params?: any) => api.get('/training/plans', { params }),
  createPlan: (data: any) => api.post('/training/plans', data),
  updatePlan: (id: number, data: any) => api.put(`/training/plans/${id}`, data),
  listRecords: (params?: any) => api.get('/training/records', { params }),
  createRecord: (data: any) => api.post('/training/records', data),
  updateRecord: (id: number, data: any) => api.put(`/training/records/${id}`, data),
};

export const performanceAPI = {
  listPlans: (params?: any) => api.get('/performance/plans', { params }),
  createPlan: (data: any) => api.post('/performance/plans', data),
  updatePlan: (id: number, data: any) => api.put(`/performance/plans/${id}`, data),
  deletePlan: (id: number) => api.delete(`/performance/plans/${id}`),
  updateGrading: (id: number, data: any) => api.put(`/performance/plans/${id}/grading`, data),
  listItems: (planId: number) => api.get(`/performance/plans/${planId}/items`),
  createItem: (planId: number, data: any) => api.post(`/performance/plans/${planId}/items`, data),
  updateItem: (id: number, data: any) => api.put(`/performance/items/${id}`, data),
  deleteItem: (id: number) => api.delete(`/performance/items/${id}`),
  listAssessments: (params?: any) => api.get('/performance/assessments', { params }),
  createAssessment: (data: any) => api.post('/performance/assessments', data),
  updateAssessment: (id: number, data: any) => api.put(`/performance/assessments/${id}`, data),
  deleteAssessment: (id: number) => api.delete(`/performance/assessments/${id}`),
  batchCreate: (data: any) => api.post('/performance/assessments/batch', data),
  getAssessmentDetail: (id: number) => api.get(`/performance/assessments/${id}/detail`),
  submitSelfReview: (id: number, data: { self_review: string }) =>
    api.put(`/performance/assessments/${id}/self-review`, data),
  confirmAssessment: (id: number) => api.put(`/performance/assessments/${id}/confirm`),
  addEvaluator: (assId: number, data: any) => api.post(`/performance/assessments/${assId}/evaluators`, data),
  deleteEvaluator: (id: number) => api.delete(`/performance/assessments/evaluators/${id}`),
  listEvaluators: (assId: number) => api.get(`/performance/assessments/${assId}/evaluators`),
  updateEvaluatorScore: (id: number, data: any) => api.put(`/performance/evaluators/${id}/score`, { params: data }),
  createScore: (data: any) => api.post('/performance/scores', data),
  batchScore: (data: any) => api.post('/performance/scores/batch', data),
  getEmployeeTimeline: (empId: number, year?: number) =>
    api.get(`/performance/employee/${empId}/timeline`, { params: year ? { year } : {} }),
  getEmployeeStats: (empId: number) => api.get(`/performance/employee/${empId}/stats`),
  getStats: (params?: any) => api.get('/performance/stats', { params }),
};

export const payrollAPI = {
  list: (params?: any) => api.get('/payroll/list', { params }),
  create: (data: any) => api.post('/payroll/create', data),
  update: (id: number, data: any) => api.put(`/payroll/${id}`, data),
  delete: (id: number) => api.delete(`/payroll/${id}`),
  confirm: (id: number) => api.put(`/payroll/${id}/confirm`),
  pay: (id: number) => api.put(`/payroll/${id}/pay`),
  batchGenerate: (year: number, month: number, deptId?: number) =>
    api.post(`/payroll/batch-generate/${year}/${month}`, null, { params: deptId ? { department_id: deptId } : {} }),
  batchConfirm: (year: number, month: number, deptId?: number) =>
    api.post('/payroll/batch-confirm', null, { params: { year, month, ...(deptId ? { department_id: deptId } : {}) } }),
  batchPay: (year: number, month: number, deptId?: number) =>
    api.post('/payroll/batch-pay', null, { params: { year, month, ...(deptId ? { department_id: deptId } : {}) } }),
  recalculate: (year: number, month: number) => api.post(`/payroll/recalculate/${year}/${month}`),
  getPayslip: (id: number) => api.get(`/payroll/${id}/payslip`),
  exportExcel: (year: number, month: number, deptId?: number) =>
    api.get('/payroll/export/excel', { params: { year, month, ...(deptId ? { department_id: deptId } : {}) }, responseType: 'blob' }),
  exportBank: (year: number, month: number, deptId?: number) =>
    api.get('/payroll/export/bank', { params: { year, month, ...(deptId ? { department_id: deptId } : {}) }, responseType: 'blob' }),
  getEmployeeHistory: (empId: number, year?: number) =>
    api.get(`/payroll/employee/${empId}/history`, { params: year ? { year } : {} }),
  getDepartmentCost: (year: number, month: number) =>
    api.get('/payroll/dashboard/department-cost', { params: { year, month } }),
  getTrends: (year: number) => api.get('/payroll/dashboard/trends', { params: { year } }),
  addItem: (payrollId: number, data: any) => api.post(`/payroll/${payrollId}/items`, data),
  updateItem: (itemId: number, data: any) => api.put(`/payroll/items/${itemId}`, data),
  deleteItem: (itemId: number) => api.delete(`/payroll/items/${itemId}`),
  listSpecialDeductions: (params?: any) => api.get('/payroll/special-deductions', { params }),
  createSpecialDeduction: (data: any) => api.post('/payroll/special-deductions', data),
  updateSpecialDeduction: (id: number, data: any) => api.put(`/payroll/special-deductions/${id}`, data),
  deleteSpecialDeduction: (id: number) => api.delete(`/payroll/special-deductions/${id}`),
  getSummary: (year: number, month: number) => api.get('/payroll/summary', { params: { year, month } }),
  listSocialInsurance: (city?: string) => api.get('/payroll/social-insurance', { params: city ? { city } : {} }),
  createSocialInsurance: (data: any) => api.post('/payroll/social-insurance', data),
  updateSocialInsurance: (id: number, data: any) => api.put(`/payroll/social-insurance/${id}`, data),
  deleteSocialInsurance: (id: number) => api.delete(`/payroll/social-insurance/${id}`),
  linkAssessment: (payrollId: number, assessmentId: number) =>
    api.post(`/payroll/${payrollId}/link-assessment`, { assessment_id: assessmentId }),
  listTemplates: () => api.get('/payroll/templates'),
  createTemplate: (data: any) => api.post('/payroll/templates', data),
  updateTemplate: (id: number, data: any) => api.put(`/payroll/templates/${id}`, data),
  deleteTemplate: (id: number) => api.delete(`/payroll/templates/${id}`),
  listTemplateItems: (templateId: number) => api.get(`/payroll/templates/${templateId}/items`),
  addTemplateItem: (templateId: number, data: any) => api.post(`/payroll/templates/${templateId}/items`, data),
  deleteTemplateItem: (itemId: number) => api.delete(`/payroll/templates/items/${itemId}`),
};

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
