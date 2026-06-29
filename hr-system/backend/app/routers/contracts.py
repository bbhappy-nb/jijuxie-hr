"""劳动关系管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.database import get_db
from app.models.contract import LaborContract, OnboardingRecord, ResignationRecord, HRBudget
from app.models.employee import Employee, User
from app.auth import get_current_user
from app.schemas import (
    ContractCreate, OnboardingCreate, ResignationCreate,
    PaginatedResponse,
)

router = APIRouter(prefix="/api/contracts", tags=["劳动关系"])


# ========== 劳动合同 ==========
@router.get("", response_model=PaginatedResponse)
def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(LaborContract)
    if status:
        q = q.filter(LaborContract.status == status)
    if employee_id:
        q = q.filter(LaborContract.employee_id == employee_id)
    total = q.count()
    items = q.order_by(LaborContract.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for c in items:
        emp = db.query(Employee).filter(Employee.id == c.employee_id).first()
        result.append({
            "id": c.id, "employee_id": c.employee_id,
            "employee_name": emp.name if emp else None,
            "contract_no": c.contract_no, "type": c.type,
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
            "probation_months": c.probation_months,
            "status": c.status, "sign_date": str(c.sign_date) if c.sign_date else None,
            "termination_date": str(c.termination_date) if c.termination_date else None,
            "termination_reason": c.termination_reason,
            "remark": c.remark,
            "created_at": str(c.created_at) if c.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("")
def create_contract(data: ContractCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = LaborContract(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "message": "合同创建成功"}


@router.put("/{contract_id}")
def update_contract(contract_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(LaborContract).filter(LaborContract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    for key, val in data.items():
        if hasattr(c, key):
            setattr(c, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.get("/expiring")
def expiring_contracts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """即将到期的合同（30天内）"""
    today = date.today()
    items = db.query(LaborContract).filter(
        LaborContract.status == "有效",
    ).all()
    result = []
    for c in items:
        if c.end_date:
            days_left = (c.end_date - today).days
            if 0 <= days_left <= 30:
                emp = db.query(Employee).filter(Employee.id == c.employee_id).first()
                result.append({
                    "id": c.id, "employee_name": emp.name if emp else None,
                    "contract_no": c.contract_no,
                    "end_date": str(c.end_date), "days_left": days_left,
                })
    return result


# ========== 入职记录 ==========
@router.get("/onboarding")
def list_onboarding(
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(OnboardingRecord)
    if employee_id:
        q = q.filter(OnboardingRecord.employee_id == employee_id)
    items = q.order_by(OnboardingRecord.id.desc()).all()
    result = []
    for o in items:
        emp = db.query(Employee).filter(Employee.id == o.employee_id).first()
        result.append({
            "id": o.id, "employee_id": o.employee_id,
            "employee_name": emp.name if emp else None,
            "onboard_date": str(o.onboard_date) if o.onboard_date else None,
            "id_card_copy": o.id_card_copy, "education_cert": o.education_cert,
            "photo": o.photo, "bank_card": o.bank_card,
            "health_check": o.health_check, "resignation_cert": o.resignation_cert,
            "signed_contract": o.signed_contract,
            "computer": o.computer, "phone_device": o.phone_device,
            "access_card": o.access_card, "office_supplies": o.office_supplies,
            "status": o.status,
        })
    return result


@router.post("/onboarding")
def create_onboarding(data: OnboardingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = OnboardingRecord(**data.model_dump())
    db.add(o)
    db.commit()
    db.refresh(o)
    return {"id": o.id, "message": "入职记录创建成功"}


@router.put("/onboarding/{rec_id}")
def update_onboarding(rec_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = db.query(OnboardingRecord).filter(OnboardingRecord.id == rec_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, val in data.items():
        if hasattr(o, key):
            setattr(o, key, val)
    db.commit()
    return {"message": "更新成功"}


# ========== 离职记录 ==========
@router.get("/resignation")
def list_resignation(
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(ResignationRecord)
    if employee_id:
        q = q.filter(ResignationRecord.employee_id == employee_id)
    items = q.order_by(ResignationRecord.id.desc()).all()
    result = []
    for r in items:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append({
            "id": r.id, "employee_id": r.employee_id,
            "employee_name": emp.name if emp else None,
            "apply_date": str(r.apply_date) if r.apply_date else None,
            "resign_date": str(r.resign_date) if r.resign_date else None,
            "type": r.type, "reason": r.reason,
            "exit_interview": r.exit_interview, "handover_person": r.handover_person,
            "handover_status": r.handover_status, "asset_returned": r.asset_returned,
            "status": r.status,
            "created_at": str(r.created_at) if r.created_at else None,
        })
    return result


@router.post("/resignation")
def create_resignation(data: ResignationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = ResignationRecord(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "message": "离职记录创建成功"}


@router.put("/resignation/{rec_id}")
def update_resignation(rec_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(ResignationRecord).filter(ResignationRecord.id == rec_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, val in data.items():
        if hasattr(r, key):
            setattr(r, key, val)
    db.commit()
    return {"message": "更新成功"}


# ========== 人力预算 ==========
@router.get("/budget")
def list_budget(year: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(HRBudget)
    if year:
        q = q.filter(HRBudget.year == year)
    items = q.all()
    result = []
    for b in items:
        result.append({
            "id": b.id, "year": b.year, "department_id": b.department_id,
            "budget_amount": b.budget_amount, "spent_amount": b.spent_amount,
            "category": b.category, "description": b.description,
        })
    return result


@router.post("/budget")
def create_budget(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    b = HRBudget(**data)
    db.add(b)
    db.commit()
    db.refresh(b)
    return {"id": b.id, "message": "预算创建成功"}
