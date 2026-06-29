"""薪酬管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.payroll import Payroll, SocialInsurance, SalaryTemplate
from app.models.employee import Employee, User
from app.auth import get_current_user
from app.schemas import PayrollCreate, SocialInsuranceCreate, PaginatedResponse
from app.services.payroll_calc import calc_payroll

router = APIRouter(prefix="/api/payroll", tags=["薪酬管理"])


@router.get("/list", response_model=PaginatedResponse)
def list_payrolls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Payroll).join(Employee)
    if year:
        q = q.filter(Payroll.year == year)
    if month:
        q = q.filter(Payroll.month == month)
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if keyword:
        q = q.filter(Employee.name.contains(keyword))
    total = q.count()
    items = q.order_by(Payroll.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in items:
        emp = db.query(Employee).filter(Employee.id == p.employee_id).first()
        result.append({
            "id": p.id, "employee_id": p.employee_id,
            "employee_name": emp.name if emp else None,
            "department_name": emp.department.name if emp and emp.department else None,
            "year": p.year, "month": p.month,
            "base_salary": p.base_salary, "performance_bonus": p.performance_bonus,
            "subsidy": p.subsidy, "overtime_pay": p.overtime_pay,
            "other_income": p.other_income,
            "social_insurance": p.social_insurance, "housing_fund": p.housing_fund,
            "tax": p.tax, "absence_deduction": p.absence_deduction,
            "other_deduction": p.other_deduction,
            "total_income": p.total_income, "total_deduction": p.total_deduction,
            "net_salary": p.net_salary, "status": p.status,
            "remark": p.remark,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/create")
def create_payroll(data: PayrollCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建工资记录并自动计算"""
    payroll = Payroll(**data.model_dump())
    db.add(payroll)
    db.flush()

    # 自动计算
    try:
        calc_payroll(payroll.employee_id, payroll.year, payroll.month, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(payroll)
    return {"id": payroll.id, "net_salary": payroll.net_salary, "message": "工资计算完成"}


@router.post("/batch-generate/{year}/{month}")
def batch_generate(year: int, month: int, department_id: Optional[int] = None,
                   db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """批量生成月度工资"""
    q = db.query(Employee).filter(Employee.status.in_(["在职", "试用期"]))
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    employees = q.all()

    count = 0
    for emp in employees:
        exists = db.query(Payroll).filter(
            Payroll.employee_id == emp.id,
            Payroll.year == year,
            Payroll.month == month,
        ).first()
        if exists:
            continue
        payroll = Payroll(employee_id=emp.id, year=year, month=month, base_salary=emp.base_salary)
        db.add(payroll)
        db.flush()
        calc_payroll(emp.id, year, month, db)
        count += 1

    db.commit()
    return {"message": f"已为 {count} 名员工生成工资", "count": count}


@router.put("/{payroll_id}")
def update_payroll(payroll_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="工资记录不存在")
    for key, val in data.items():
        if hasattr(p, key):
            setattr(p, key, val)
    # 重新计算
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"net_salary": p.net_salary, "message": "更新成功"}


@router.put("/{payroll_id}/confirm")
def confirm_payroll(payroll_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="记录不存在")
    p.status = "已确认"
    db.commit()
    return {"message": "已确认"}


# ========== 社保公积金 ==========
@router.get("/social-insurance")
def list_social_insurance(city: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(SocialInsurance)
    if city:
        q = q.filter(SocialInsurance.city == city)
    items = q.all()
    return [{
        "id": s.id, "city": s.city, "year": s.year,
        "pension_base_min": s.pension_base_min, "pension_base_max": s.pension_base_max,
        "pension_personal": s.pension_personal, "pension_company": s.pension_company,
        "medical_base_min": s.medical_base_min, "medical_base_max": s.medical_base_max,
        "medical_personal": s.medical_personal, "medical_company": s.medical_company,
        "unemployment_personal": s.unemployment_personal, "unemployment_company": s.unemployment_company,
        "injury_company": s.injury_company, "maternity_company": s.maternity_company,
        "housing_fund_min": s.housing_fund_min, "housing_fund_max": s.housing_fund_max,
        "housing_fund_personal": s.housing_fund_personal, "housing_fund_company": s.housing_fund_company,
    } for s in items]


@router.post("/social-insurance")
def create_social_insurance(data: SocialInsuranceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = SocialInsurance(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "message": "创建成功"}


# ========== 汇总统计 ==========
@router.get("/summary")
def payroll_summary(year: int, month: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """月度薪酬汇总"""
    from sqlalchemy import func
    stats = db.query(
        func.count(Payroll.id),
        func.sum(Payroll.total_income),
        func.sum(Payroll.total_deduction),
        func.sum(Payroll.tax),
        func.sum(Payroll.social_insurance),
        func.sum(Payroll.housing_fund),
        func.sum(Payroll.net_salary),
    ).filter(Payroll.year == year, Payroll.month == month).first()
    return {
        "year": year, "month": month,
        "employee_count": stats[0] or 0,
        "total_income": round(float(stats[1] or 0), 2),
        "total_deduction": round(float(stats[2] or 0), 2),
        "total_tax": round(float(stats[3] or 0), 2),
        "total_social_insurance": round(float(stats[4] or 0), 2),
        "total_housing_fund": round(float(stats[5] or 0), 2),
        "total_net_salary": round(float(stats[6] or 0), 2),
    }
