"""培训管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.training import TrainingPlan, TrainingRecord
from app.models.employee import Employee, User
from app.auth import get_current_user
from app.schemas import TrainingPlanCreate, TrainingRecordCreate, PaginatedResponse

router = APIRouter(prefix="/api/training", tags=["培训管理"])


@router.get("/plans", response_model=PaginatedResponse)
def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(TrainingPlan)
    if status:
        q = q.filter(TrainingPlan.status == status)
    total = q.count()
    items = q.order_by(TrainingPlan.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in items:
        cnt = db.query(TrainingRecord).filter(TrainingRecord.plan_id == p.id).count()
        result.append({
            "id": p.id, "title": p.title, "type": p.type, "trainer": p.trainer,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "location": p.location, "budget": p.budget, "actual_cost": p.actual_cost,
            "status": p.status, "participant_count": cnt,
            "max_participants": p.max_participants, "description": p.description,
            "created_at": str(p.created_at) if p.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/plans")
def create_plan(data: TrainingPlanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = TrainingPlan(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "message": "培训计划创建成功"}


@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="计划不存在")
    for key, val in data.items():
        if hasattr(p, key):
            setattr(p, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.get("/records", response_model=PaginatedResponse)
def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plan_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(TrainingRecord)
    if plan_id:
        q = q.filter(TrainingRecord.plan_id == plan_id)
    if employee_id:
        q = q.filter(TrainingRecord.employee_id == employee_id)
    total = q.count()
    items = q.order_by(TrainingRecord.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for r in items:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append({
            "id": r.id, "plan_id": r.plan_id, "employee_id": r.employee_id,
            "employee_name": emp.name if emp else None,
            "score": r.score, "hours": r.hours, "status": r.status,
            "feedback": r.feedback, "certificate": r.certificate,
            "created_at": str(r.created_at) if r.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/records")
def create_record(data: TrainingRecordCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = TrainingRecord(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "message": "培训记录创建成功"}


@router.put("/records/{rec_id}")
def update_record(rec_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(TrainingRecord).filter(TrainingRecord.id == rec_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, val in data.items():
        if hasattr(r, key):
            setattr(r, key, val)
    db.commit()
    return {"message": "更新成功"}
