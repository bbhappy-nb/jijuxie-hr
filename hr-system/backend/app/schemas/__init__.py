"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# ========== 通用 ==========
class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


# ========== 认证 ==========
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


# ========== 员工 ==========
class EmployeeBase(BaseModel):
    employee_no: str
    name: str
    gender: Optional[str] = "男"
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    status: Optional[str] = "在职"
    hire_date: Optional[date] = None
    base_salary: Optional[float] = 0


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    status: Optional[str] = None
    base_salary: Optional[float] = None
    birthday: Optional[date] = None
    education: Optional[str] = None
    hire_date: Optional[date] = None
    probation_end: Optional[date] = None


class EmployeeResponse(EmployeeBase):
    id: int
    birthday: Optional[date] = None
    education: Optional[str] = None
    hire_date: Optional[date] = None
    probation_end: Optional[date] = None
    resign_date: Optional[date] = None
    department_name: Optional[str] = None
    position_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 部门 ==========
class DepartmentBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: int
    employee_count: int = 0
    children: List["DepartmentResponse"] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 岗位 ==========
class PositionBase(BaseModel):
    name: str
    department_id: int
    headcount: int = 1
    description: Optional[str] = None
    requirements: Optional[str] = None


class PositionCreate(PositionBase):
    pass


class PositionResponse(PositionBase):
    id: int
    current_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 招聘 ==========
class RecruitmentBase(BaseModel):
    title: str
    department_id: int
    headcount: int = 1
    salary_range: Optional[str] = None
    requirements: Optional[str] = None
    channel: Optional[str] = None
    priority: str = "普通"


class RecruitmentCreate(RecruitmentBase):
    pass


class RecruitmentResponse(RecruitmentBase):
    id: int
    status: str
    publish_date: Optional[date] = None
    candidate_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 候选人 ==========
class CandidateBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    recruitment_id: int
    education: Optional[str] = None
    years_of_work: Optional[int] = None
    expected_salary: Optional[str] = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    stage: Optional[str] = None
    interview_date: Optional[date] = None
    interviewer: Optional[str] = None
    interview_feedback: Optional[str] = None
    offer_salary: Optional[str] = None
    onboard_date: Optional[date] = None
    remark: Optional[str] = None


class CandidateResponse(CandidateBase):
    id: int
    stage: str
    interview_date: Optional[date] = None
    offer_date: Optional[date] = None
    recruitment_title: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 培训 ==========
class TrainingPlanBase(BaseModel):
    title: str
    type: Optional[str] = None
    trainer: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    budget: int = 0


class TrainingPlanCreate(TrainingPlanBase):
    pass


class TrainingPlanResponse(TrainingPlanBase):
    id: int
    status: str
    participant_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingRecordCreate(BaseModel):
    plan_id: int
    employee_id: int


class TrainingRecordResponse(BaseModel):
    id: int
    plan_id: int
    employee_id: int
    employee_name: Optional[str] = None
    score: Optional[int] = None
    hours: int = 0
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 绩效 ==========
class PerformancePlanBase(BaseModel):
    name: str
    period: str = "月度"
    year: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    type: str = "KPI"
    description: Optional[str] = None


class PerformancePlanCreate(PerformancePlanBase):
    pass


class PerformancePlanUpdate(BaseModel):
    name: Optional[str] = None
    period: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    grade_s_threshold: Optional[float] = None
    grade_a_threshold: Optional[float] = None
    grade_b_threshold: Optional[float] = None
    grade_c_threshold: Optional[float] = None
    bonus_coefficients: Optional[str] = None
    self_review_enabled: Optional[int] = None


class PerformancePlanResponse(BaseModel):
    id: int
    name: str
    period: str
    year: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    type: str
    description: Optional[str] = None
    status: str
    grade_s_threshold: float = 90
    grade_a_threshold: float = 80
    grade_b_threshold: float = 70
    grade_c_threshold: float = 60
    bonus_coefficients: Optional[str] = "S:1.5,A:1.2,B:1.0,C:0.8,D:0.5"
    self_review_enabled: int = 1
    assessment_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PerformanceItemBase(BaseModel):
    name: str
    weight: float = 0
    target: Optional[str] = None
    scoring_method: str = "direct"
    sort_order: int = 0


class PerformanceItemCreate(PerformanceItemBase):
    plan_id: int


class PerformanceItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = None
    target: Optional[str] = None
    actual_value: Optional[str] = None
    scoring_method: Optional[str] = None
    sort_order: Optional[int] = None


class PerformanceItemResponse(PerformanceItemBase):
    id: int
    plan_id: int
    description: Optional[str] = None
    actual_value: Optional[str] = None

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    plan_id: int
    employee_id: int
    evaluator_id: Optional[int] = None


class AssessmentResponse(BaseModel):
    id: int
    plan_id: int
    employee_id: int
    employee_name: Optional[str] = None
    plan_name: Optional[str] = None
    evaluator_id: Optional[int] = None
    evaluator_name: Optional[str] = None
    total_score: float = 0
    grade: Optional[str] = None
    self_review: Optional[str] = None
    self_review_status: Optional[str] = "未提交"
    employee_confirmed: int = 0
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentEvaluatorCreate(BaseModel):
    assessment_id: int
    evaluator_id: int
    evaluator_type: str = "上级"
    weight: float = 100


class AssessmentEvaluatorResponse(BaseModel):
    id: int
    assessment_id: int
    evaluator_id: int
    evaluator_name: Optional[str] = None
    evaluator_type: str
    weight: float
    total_score: float = 0
    grade: Optional[str] = None
    comment: Optional[str] = None
    status: str
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchAssessmentCreate(BaseModel):
    plan_id: int
    department_id: Optional[int] = None
    employee_ids: Optional[List[int]] = None
    evaluator_id: Optional[int] = None


class SelfReviewSubmit(BaseModel):
    self_review: str


class EmployeeConfirm(BaseModel):
    pass


class ScoreCreate(BaseModel):
    assessment_id: int
    item_id: int
    score: float = 0
    comment: Optional[str] = None


class ScoreBatchCreate(BaseModel):
    assessment_id: int
    scores: List[ScoreCreate]


# ========== 薪酬 ==========
class PayrollBase(BaseModel):
    employee_id: int
    year: int
    month: int
    base_salary: float = 0
    performance_bonus: float = 0
    subsidy: float = 0
    overtime_pay: float = 0
    other_income: float = 0
    social_insurance: float = 0
    housing_fund: float = 0
    absence_deduction: float = 0
    other_deduction: float = 0
    special_deduction: float = 0


class PayrollCreate(PayrollBase):
    template_id: Optional[int] = None


class PayrollUpdate(BaseModel):
    base_salary: Optional[float] = None
    performance_bonus: Optional[float] = None
    subsidy: Optional[float] = None
    overtime_pay: Optional[float] = None
    other_income: Optional[float] = None
    absence_deduction: Optional[float] = None
    other_deduction: Optional[float] = None
    special_deduction: Optional[float] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class PayrollResponse(PayrollBase):
    id: int
    total_income: float
    total_deduction: float
    tax: float
    net_salary: float
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    department_id: Optional[int] = None
    template_id: Optional[int] = None
    paid_at: Optional[datetime] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayrollItemCreate(BaseModel):
    name: str
    type: str
    amount: float = 0
    is_taxable: int = 1
    sort_order: int = 0


class PayrollItemUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    is_taxable: Optional[int] = None
    sort_order: Optional[int] = None


class PayrollItemResponse(BaseModel):
    id: int
    payroll_id: int
    name: str
    type: str
    amount: float
    is_taxable: int
    sort_order: int

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    items: Optional[List[PayrollItemCreate]] = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    item_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SocialInsuranceBase(BaseModel):
    city: str
    year: int
    pension_base_min: float = 0
    pension_base_max: float = 0
    pension_personal: float = 0
    pension_company: float = 0
    medical_base_min: float = 0
    medical_base_max: float = 0
    medical_personal: float = 0
    medical_company: float = 0
    unemployment_personal: float = 0
    unemployment_company: float = 0
    injury_company: float = 0
    maternity_company: float = 0
    housing_fund_min: float = 0
    housing_fund_max: float = 0
    housing_fund_personal: float = 0
    housing_fund_company: float = 0


class SocialInsuranceCreate(SocialInsuranceBase):
    pass


class SocialInsuranceUpdate(BaseModel):
    city: Optional[str] = None
    year: Optional[int] = None
    pension_base_min: Optional[float] = None
    pension_base_max: Optional[float] = None
    pension_personal: Optional[float] = None
    pension_company: Optional[float] = None
    medical_base_min: Optional[float] = None
    medical_base_max: Optional[float] = None
    medical_personal: Optional[float] = None
    medical_company: Optional[float] = None
    unemployment_personal: Optional[float] = None
    unemployment_company: Optional[float] = None
    injury_company: Optional[float] = None
    maternity_company: Optional[float] = None
    housing_fund_min: Optional[float] = None
    housing_fund_max: Optional[float] = None
    housing_fund_personal: Optional[float] = None
    housing_fund_company: Optional[float] = None


class SocialInsuranceResponse(SocialInsuranceBase):
    id: int

    class Config:
        from_attributes = True


class SpecialDeductionCreate(BaseModel):
    employee_id: int
    year: int
    deduction_type: str
    amount: float = 0
    remark: Optional[str] = None


class SpecialDeductionUpdate(BaseModel):
    deduction_type: Optional[str] = None
    amount: Optional[float] = None
    remark: Optional[str] = None


class SpecialDeductionResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    year: int
    deduction_type: str
    amount: float
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class LinkAssessmentRequest(BaseModel):
    assessment_id: int


# ========== 劳动合同 ==========
class ContractBase(BaseModel):
    employee_id: int
    contract_no: str
    type: str = "固定期限"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    probation_months: int = 0


class ContractCreate(ContractBase):
    pass


class ContractResponse(ContractBase):
    id: int
    status: str
    sign_date: Optional[date] = None
    employee_name: Optional[str] = None
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 入离职 ==========
class OnboardingCreate(BaseModel):
    employee_id: int
    onboard_date: Optional[date] = None


class OnboardingResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    onboard_date: Optional[date] = None
    id_card_copy: int = 0
    education_cert: int = 0
    photo: int = 0
    bank_card: int = 0
    health_check: int = 0
    signed_contract: int = 0
    status: str

    class Config:
        from_attributes = True


class ResignationCreate(BaseModel):
    employee_id: int
    apply_date: Optional[date] = None
    resign_date: Optional[date] = None
    type: str = "主动离职"
    reason: Optional[str] = None


class ResignationResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    apply_date: Optional[date] = None
    resign_date: Optional[date] = None
    type: str
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 仪表盘 ==========
class DashboardStats(BaseModel):
    total_employees: int = 0
    active_employees: int = 0
    month_onboarding: int = 0
    month_resignation: int = 0
    department_distribution: list = []
    monthly_payroll_trend: list = []
    contract_expiring: int = 0
    pending_assessments: int = 0
