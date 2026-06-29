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


class PerformancePlanCreate(PerformancePlanBase):
    pass


class PerformancePlanResponse(PerformancePlanBase):
    id: int
    status: str
    assessment_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    plan_id: int
    employee_id: int
    evaluator_id: int


class AssessmentResponse(BaseModel):
    id: int
    plan_id: int
    employee_id: int
    employee_name: Optional[str] = None
    evaluator_name: Optional[str] = None
    total_score: float = 0
    grade: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScoreCreate(BaseModel):
    assessment_id: int
    item_id: int
    score: float = 0
    comment: Optional[str] = None


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


class PayrollCreate(PayrollBase):
    pass


class PayrollResponse(PayrollBase):
    id: int
    total_income: float
    total_deduction: float
    tax: float
    net_salary: float
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    status: str

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


class SocialInsuranceResponse(SocialInsuranceBase):
    id: int

    class Config:
        from_attributes = True


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
