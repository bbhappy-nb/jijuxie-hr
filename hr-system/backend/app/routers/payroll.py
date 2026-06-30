"""薪酬管理路由 — 完整版"""
from datetime import datetime
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.payroll import Payroll, SocialInsurance, SalaryTemplate, SalaryTemplateItem, PayrollItem, SpecialDeduction, PerformanceBonusLink
from app.models.employee import Employee, Department, User
from app.models.performance import PerformanceAssessment, PerformancePlan
from app.auth import get_current_user
from app.schemas import (PayrollCreate, PayrollUpdate, PayrollResponse, SocialInsuranceCreate,
                          SocialInsuranceUpdate, TemplateCreate, TemplateUpdate, SpecialDeductionCreate,
                          SpecialDeductionUpdate, PayrollItemCreate, PayrollItemUpdate, LinkAssessmentRequest,
                          PaginatedResponse)
from app.services.payroll_calc import calc_payroll, link_assessment_to_payroll

router = APIRouter(prefix="/api/payroll", tags=["薪酬管理"])


# ==================== 工资表 CRUD ====================

@router.get("/list", response_model=PaginatedResponse)
def list_payrolls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
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
    if employee_id:
        q = q.filter(Payroll.employee_id == employee_id)
    if status:
        q = q.filter(Payroll.status == status)
    if keyword:
        q = q.filter(Employee.name.contains(keyword))
    total = q.count()
    payrolls = q.order_by(Payroll.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in payrolls:
        emp = p.employee
        result.append({
            "id": p.id, "employee_id": p.employee_id,
            "employee_name": emp.name if emp else None,
            "department_name": emp.department.name if emp and emp.department else None,
            "department_id": emp.department_id if emp else None,
            "year": p.year, "month": p.month,
            "base_salary": p.base_salary, "performance_bonus": p.performance_bonus,
            "subsidy": p.subsidy, "overtime_pay": p.overtime_pay,
            "other_income": p.other_income,
            "social_insurance": p.social_insurance, "housing_fund": p.housing_fund,
            "tax": p.tax, "absence_deduction": p.absence_deduction,
            "other_deduction": p.other_deduction, "special_deduction": p.special_deduction,
            "total_income": p.total_income, "total_deduction": p.total_deduction,
            "net_salary": p.net_salary, "status": p.status,
            "template_id": p.template_id, "paid_at": str(p.paid_at) if p.paid_at else None,
            "remark": p.remark, "created_at": str(p.created_at) if p.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/create")
def create_payroll(data: PayrollCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """创建工资记录并自动计算"""
    payroll = Payroll(**data.model_dump(exclude={"template_id"}))
    if data.template_id:
        payroll.template_id = data.template_id
    db.add(payroll)
    db.flush()
    try:
        calc_payroll(payroll.employee_id, payroll.year, payroll.month, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    db.refresh(payroll)
    return {"id": payroll.id, "net_salary": payroll.net_salary, "message": "工资计算完成"}


@router.put("/{payroll_id}")
def update_payroll(payroll_id: int, data: PayrollUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="工资记录不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        if hasattr(p, key):
            setattr(p, key, val)
    if data.status == "已确认":
        p.status = "已确认"
    elif data.status == "已发放":
        p.status = "已发放"
        p.paid_at = datetime.now()
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"net_salary": p.net_salary, "message": "更新成功"}


@router.delete("/{payroll_id}")
def delete_payroll(payroll_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.query(PayrollItem).filter(PayrollItem.payroll_id == payroll_id).delete()
    db.query(PerformanceBonusLink).filter(PerformanceBonusLink.payroll_id == payroll_id).delete()
    db.delete(p)
    db.commit()
    return {"message": "已删除"}


@router.put("/{payroll_id}/confirm")
def confirm_payroll(payroll_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="记录不存在")
    p.status = "已确认"
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"message": "已确认"}


@router.put("/{payroll_id}/pay")
def pay_payroll(payroll_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="记录不存在")
    if p.status != "已确认":
        raise HTTPException(status_code=400, detail="只有已确认的工资才能发放")
    p.status = "已发放"
    p.paid_at = datetime.now()
    db.commit()
    return {"message": "已发放", "paid_at": str(p.paid_at)}


# ==================== 批量操作 ====================

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
            Payroll.year == year, Payroll.month == month,
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


@router.post("/batch-confirm")
def batch_confirm(year: int, month: int, department_id: Optional[int] = None,
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Payroll).join(Employee).filter(
        Payroll.year == year, Payroll.month == month, Payroll.status == "草稿"
    )
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    payrolls = q.all()
    for p in payrolls:
        p.status = "已确认"
        calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"message": f"已确认 {len(payrolls)} 条记录", "count": len(payrolls)}


@router.post("/batch-pay")
def batch_pay(year: int, month: int, department_id: Optional[int] = None,
              db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Payroll).join(Employee).filter(
        Payroll.year == year, Payroll.month == month, Payroll.status == "已确认"
    )
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    payrolls = q.all()
    now = datetime.now()
    for p in payrolls:
        p.status = "已发放"
        p.paid_at = now
    db.commit()
    return {"message": f"已发放 {len(payrolls)} 条记录", "count": len(payrolls)}


@router.post("/recalculate/{year}/{month}")
def recalculate(year: int, month: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """重算指定月份的工资 (从1月到指定月逐月重算，确保累计个税正确)"""
    payrolls = db.query(Payroll).filter(Payroll.year == year, Payroll.month <= month).order_by(Payroll.month).all()
    for p in payrolls:
        calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"message": f"已重算 {len(payrolls)} 条记录"}


# ==================== 工资条 ====================

@router.get("/{payroll_id}/payslip")
def get_payslip(payroll_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="记录不存在")
    emp = p.employee
    items = db.query(PayrollItem).filter(PayrollItem.payroll_id == payroll_id).order_by(PayrollItem.sort_order).all()

    # 绩效联动信息
    bonus_link = db.query(PerformanceBonusLink).filter(PerformanceBonusLink.payroll_id == payroll_id).first()
    assessment_info = None
    if bonus_link and bonus_link.assessment:
        a = bonus_link.assessment
        assessment_info = {
            "assessment_id": a.id, "grade": a.grade,
            "total_score": a.total_score, "coefficient": bonus_link.coefficient,
            "bonus_amount": bonus_link.bonus_amount,
        }

    return {
        "id": p.id,
        "employee": {
            "id": emp.id, "name": emp.name, "employee_no": emp.employee_no,
            "department": emp.department.name if emp.department else None,
            "position": emp.position.name if emp.position else None,
        },
        "year": p.year, "month": p.month,
        "income_items": [
            {"name": "基本工资", "amount": p.base_salary or 0},
            {"name": "绩效奖金", "amount": p.performance_bonus or 0},
            {"name": "补贴", "amount": p.subsidy or 0},
            {"name": "加班费", "amount": p.overtime_pay or 0},
            {"name": "其他收入", "amount": p.other_income or 0},
        ] + [{"name": it.name, "amount": it.amount or 0, "dynamic": True} for it in items if it.type == "income"],
        "deduction_items": [
            {"name": "社保(个人)", "amount": p.social_insurance or 0},
            {"name": "公积金(个人)", "amount": p.housing_fund or 0},
            {"name": "个人所得税", "amount": p.tax or 0},
            {"name": "缺勤扣款", "amount": p.absence_deduction or 0},
            {"name": "其他扣款", "amount": p.other_deduction or 0},
        ] + [{"name": it.name, "amount": it.amount or 0, "dynamic": True} for it in items if it.type == "deduction"],
        "total_income": p.total_income,
        "total_deduction": p.total_deduction,
        "net_salary": p.net_salary,
        "status": p.status,
        "paid_at": str(p.paid_at) if p.paid_at else None,
        "assessment": assessment_info,
    }


# ==================== 导出 ====================

@router.get("/export/excel")
def export_excel(year: int, month: int, department_id: Optional[int] = None,
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """导出 Excel 工资表"""
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="需要安装 openpyxl: pip install openpyxl")

    q = db.query(Payroll).join(Employee)
    q = q.filter(Payroll.year == year, Payroll.month == month)
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    payrolls = q.order_by(Employee.department_id, Employee.employee_no).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{year}年{month}月工资表"

    headers = ["工号", "姓名", "部门", "基本工资", "绩效奖金", "补贴", "加班费", "其他收入",
               "应发合计", "社保", "公积金", "个税", "缺勤扣款", "其他扣款",
               "专项扣除", "扣款合计", "实发工资", "状态"]
    ws.append(headers)

    for p in payrolls:
        emp = p.employee
        dept = emp.department.name if emp.department else ""
        ws.append([
            emp.employee_no, emp.name, dept,
            p.base_salary or 0, p.performance_bonus or 0, p.subsidy or 0,
            p.overtime_pay or 0, p.other_income or 0,
            p.total_income or 0, p.social_insurance or 0, p.housing_fund or 0,
            p.tax or 0, p.absence_deduction or 0, p.other_deduction or 0,
            p.special_deduction or 0, p.total_deduction or 0, p.net_salary or 0, p.status,
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename=payroll_{year}_{month}.xlsx"})


@router.get("/export/bank")
def export_bank(year: int, month: int, department_id: Optional[int] = None,
                db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """导出银行代发文件"""
    q = db.query(Payroll).join(Employee).filter(
        Payroll.year == year, Payroll.month == month, Payroll.status.in_(["已确认", "已发放"])
    )
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    payrolls = q.order_by(Employee.employee_no).all()

    lines = ["姓名,银行卡号,开户行,实发金额"]
    for p in payrolls:
        emp = p.employee
        lines.append(f"{emp.name},{emp.bank_account or ''},{emp.bank_name or ''},{p.net_salary or 0}")

    content = "\n".join(lines)
    return StreamingResponse(BytesIO(content.encode("utf-8-sig")), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename=bank_{year}_{month}.csv"})


# ==================== 员工薪酬历史 ====================

@router.get("/employee/{employee_id}/history")
def employee_salary_history(employee_id: int, year: Optional[int] = None,
                            db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Payroll).filter(Payroll.employee_id == employee_id)
    if year:
        q = q.filter(Payroll.year == year)
    payrolls = q.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    emp = db.query(Employee).filter(Employee.id == employee_id).first()

    history = []
    for p in payrolls:
        history.append({
            "id": p.id, "year": p.year, "month": p.month,
            "base_salary": p.base_salary, "performance_bonus": p.performance_bonus,
            "total_income": p.total_income, "total_deduction": p.total_deduction,
            "tax": p.tax, "net_salary": p.net_salary, "status": p.status,
            "paid_at": str(p.paid_at) if p.paid_at else None,
        })

    # 趋势数据
    trend = []
    for p in reversed(payrolls[:24]):
        trend.append({"label": f"{p.year}/{p.month:02d}", "net_salary": p.net_salary, "total_income": p.total_income})

    return {
        "employee": {"id": emp.id, "name": emp.name, "employee_no": emp.employee_no} if emp else None,
        "total_records": len(history),
        "history": history,
        "trend": trend,
    }


# ==================== 薪酬分析 ====================

@router.get("/dashboard/department-cost")
def department_cost(year: int, month: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    """部门薪酬成本分布"""
    results = db.query(
        Employee.department_id, Department.name,
        func.count(Payroll.id), func.sum(Payroll.total_income), func.sum(Payroll.net_salary)
    ).join(Employee).join(Department).filter(
        Payroll.year == year, Payroll.month == month
    ).group_by(Employee.department_id).all()

    return [{
        "department_id": r[0], "department_name": r[1],
        "headcount": r[2], "total_income": round(float(r[3] or 0), 2),
        "total_net": round(float(r[4] or 0), 2),
    } for r in results]


@router.get("/dashboard/trends")
def payroll_trends(year: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """月度薪酬趋势 (含去年同期对比)"""
    trends = []
    for month in range(1, 13):
        current = db.query(
            func.count(Payroll.id), func.sum(Payroll.net_salary), func.sum(Payroll.total_income),
            func.sum(Payroll.tax),
        ).filter(Payroll.year == year, Payroll.month == month).first()

        prior = db.query(
            func.sum(Payroll.net_salary),
        ).filter(Payroll.year == year - 1, Payroll.month == month).first()

        trends.append({
            "month": month,
            "label": f"{month}月",
            "headcount": current[0] or 0,
            "net_salary": round(float(current[1] or 0), 2),
            "total_income": round(float(current[2] or 0), 2),
            "total_tax": round(float(current[3] or 0), 2),
            "prior_net": round(float(prior[0] or 0), 2),
        })
    return {"year": year, "trends": trends}


# ==================== 动态薪资项 ====================

@router.post("/{payroll_id}/items")
def add_payroll_item(payroll_id: int, data: PayrollItemCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="记录不存在")
    item = PayrollItem(payroll_id=payroll_id, **data.model_dump())
    db.add(item)
    db.flush()
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"id": item.id, "message": "已添加"}


@router.put("/items/{item_id}")
def update_payroll_item(item_id: int, data: PayrollItemUpdate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    item = db.query(PayrollItem).filter(PayrollItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(item, key, val)
    p = item.payroll
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"message": "已更新"}


@router.delete("/items/{item_id}")
def delete_payroll_item(item_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    item = db.query(PayrollItem).filter(PayrollItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    payroll_id = item.payroll_id
    p = item.payroll
    db.delete(item)
    db.flush()
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    return {"message": "已删除"}


# ==================== 专项附加扣除 ====================

@router.get("/special-deductions")
def list_special_deductions(employee_id: Optional[int] = None, year: Optional[int] = None,
                            db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(SpecialDeduction)
    if employee_id:
        q = q.filter(SpecialDeduction.employee_id == employee_id)
    if year:
        q = q.filter(SpecialDeduction.year == year)
    items = q.all()
    return [{
        "id": d.id, "employee_id": d.employee_id,
        "employee_name": d.employee.name if d.employee else None,
        "year": d.year, "deduction_type": d.deduction_type,
        "amount": d.amount, "remark": d.remark,
    } for d in items]


@router.post("/special-deductions")
def create_special_deduction(data: SpecialDeductionCreate, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    d = SpecialDeduction(**data.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"id": d.id, "message": "创建成功"}


@router.put("/special-deductions/{deduction_id}")
def update_special_deduction(deduction_id: int, data: SpecialDeductionUpdate,
                             db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = db.query(SpecialDeduction).filter(SpecialDeduction.id == deduction_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(d, key, val)
    db.commit()
    return {"message": "已更新"}


@router.delete("/special-deductions/{deduction_id}")
def delete_special_deduction(deduction_id: int, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    d = db.query(SpecialDeduction).filter(SpecialDeduction.id == deduction_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(d)
    db.commit()
    return {"message": "已删除"}


# ==================== 社保公积金 ====================

@router.get("/social-insurance")
def list_social_insurance(city: Optional[str] = None, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    q = db.query(SocialInsurance)
    if city:
        q = q.filter(SocialInsurance.city == city)
    items = q.order_by(SocialInsurance.year.desc()).all()
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
def create_social_insurance(data: SocialInsuranceCreate, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    s = SocialInsurance(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "message": "创建成功"}


@router.put("/social-insurance/{si_id}")
def update_social_insurance(si_id: int, data: SocialInsuranceUpdate, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    s = db.query(SocialInsurance).filter(SocialInsurance.id == si_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(s, key, val)
    db.commit()
    return {"message": "已更新"}


@router.delete("/social-insurance/{si_id}")
def delete_social_insurance(si_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    s = db.query(SocialInsurance).filter(SocialInsurance.id == si_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(s)
    db.commit()
    return {"message": "已删除"}


# ==================== 绩效联动 ====================

@router.post("/{payroll_id}/link-assessment")
def link_assessment(payroll_id: int, data: LinkAssessmentRequest, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    try:
        result = link_assessment_to_payroll(payroll_id, data.assessment_id, db)
        db.commit()
        return {"message": "关联成功", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 薪资模板 ====================

@router.get("/templates")
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    templates = db.query(SalaryTemplate).order_by(SalaryTemplate.id.desc()).all()
    return [{
        "id": t.id, "name": t.name, "description": t.description,
        "item_count": len(t.items), "created_at": str(t.created_at) if t.created_at else None,
    } for t in templates]


@router.post("/templates")
def create_template(data: TemplateCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    t = SalaryTemplate(name=data.name, description=data.description)
    db.add(t)
    db.flush()
    if data.items:
        for i, item_data in enumerate(data.items):
            item = SalaryTemplateItem(
                template_id=t.id, name=item_data.name, type=item_data.type,
                is_taxable=item_data.is_taxable, sort_order=item_data.sort_order or i,
            )
            db.add(item)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "message": "模板创建成功"}


@router.put("/templates/{template_id}")
def update_template(template_id: int, data: TemplateUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    t = db.query(SalaryTemplate).filter(SalaryTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(t, key, val)
    db.commit()
    return {"message": "已更新"}


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    t = db.query(SalaryTemplate).filter(SalaryTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.query(SalaryTemplateItem).filter(SalaryTemplateItem.template_id == template_id).delete()
    db.delete(t)
    db.commit()
    return {"message": "已删除"}


@router.get("/templates/{template_id}/items")
def list_template_items(template_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    items = db.query(SalaryTemplateItem).filter(
        SalaryTemplateItem.template_id == template_id
    ).order_by(SalaryTemplateItem.sort_order).all()
    return [{
        "id": i.id, "template_id": i.template_id, "name": i.name,
        "type": i.type, "is_taxable": i.is_taxable, "sort_order": i.sort_order,
    } for i in items]


@router.post("/templates/{template_id}/items")
def add_template_item(template_id: int, data: PayrollItemCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    item = SalaryTemplateItem(template_id=template_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "已添加"}


@router.delete("/templates/items/{item_id}")
def delete_template_item(item_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    item = db.query(SalaryTemplateItem).filter(SalaryTemplateItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(item)
    db.commit()
    return {"message": "已删除"}


# ==================== 汇总统计 ====================

@router.get("/summary")
def payroll_summary(year: int, month: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    """月度薪酬汇总"""
    stats = db.query(
        func.count(Payroll.id), func.sum(Payroll.total_income), func.sum(Payroll.total_deduction),
        func.sum(Payroll.tax), func.sum(Payroll.social_insurance), func.sum(Payroll.housing_fund),
        func.sum(Payroll.net_salary),
    ).filter(Payroll.year == year, Payroll.month == month).first()

    # 状态分布
    status_stats = db.query(Payroll.status, func.count(Payroll.id)).filter(
        Payroll.year == year, Payroll.month == month
    ).group_by(Payroll.status).all()

    return {
        "year": year, "month": month,
        "employee_count": stats[0] or 0,
        "total_income": round(float(stats[1] or 0), 2),
        "total_deduction": round(float(stats[2] or 0), 2),
        "total_tax": round(float(stats[3] or 0), 2),
        "total_social_insurance": round(float(stats[4] or 0), 2),
        "total_housing_fund": round(float(stats[5] or 0), 2),
        "total_net_salary": round(float(stats[6] or 0), 2),
        "status_breakdown": {s: c for s, c in status_stats},
    }
