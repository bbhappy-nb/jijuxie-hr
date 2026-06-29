"""绩效管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.performance import (
    PerformancePlan, PerformanceItem, PerformanceAssessment, PerformanceScore,
)
from app.models.employee import Employee, User
from app.auth import get_current_user
from app.schemas import (
    PerformancePlanCreate, AssessmentCreate, ScoreCreate,
    PaginatedResponse,
)

router = APIRouter(prefix="/api/performance", tags=["绩效管理"])


@router.get("/plans", response_model=PaginatedResponse)
def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PerformancePlan)
    if year:
        q = q.filter(PerformancePlan.year == year)
    total = q.count()
    items = q.order_by(PerformancePlan.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in items:
        cnt = db.query(PerformanceAssessment).filter(PerformanceAssessment.plan_id == p.id).count()
        result.append({
            "id": p.id, "name": p.name, "period": p.period, "year": p.year,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "type": p.type, "description": p.description, "status": p.status,
            "assessment_count": cnt,
            "created_at": str(p.created_at) if p.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/plans")
def create_plan(data: PerformancePlanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = PerformancePlan(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "message": "考核方案创建成功"}


@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="方案不存在")
    for key, val in data.items():
        if hasattr(p, key):
            setattr(p, key, val)
    db.commit()
    return {"message": "更新成功"}


# ========== 考核指标 ==========
@router.get("/plans/{plan_id}/items")
def list_items(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(PerformanceItem).filter(
        PerformanceItem.plan_id == plan_id
    ).order_by(PerformanceItem.sort_order).all()
    return [{"id": i.id, "plan_id": i.plan_id, "name": i.name,
             "description": i.description, "weight": i.weight,
             "target": i.target, "sort_order": i.sort_order} for i in items]


@router.post("/plans/{plan_id}/items")
def create_item(plan_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = PerformanceItem(plan_id=plan_id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "指标创建成功"}


# ========== 考核记录 ==========
@router.get("/assessments", response_model=PaginatedResponse)
def list_assessments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plan_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PerformanceAssessment)
    if plan_id:
        q = q.filter(PerformanceAssessment.plan_id == plan_id)
    if status:
        q = q.filter(PerformanceAssessment.status == status)
    total = q.count()
    items = q.order_by(PerformanceAssessment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for a in items:
        emp = db.query(Employee).filter(Employee.id == a.employee_id).first()
        eva = db.query(Employee).filter(Employee.id == a.evaluator_id).first()
        result.append({
            "id": a.id, "plan_id": a.plan_id, "employee_id": a.employee_id,
            "employee_name": emp.name if emp else None,
            "evaluator_id": a.evaluator_id,
            "evaluator_name": eva.name if eva else None,
            "total_score": a.total_score, "grade": a.grade,
            "self_review": a.self_review, "evaluator_comment": a.evaluator_comment,
            "status": a.status,
            "created_at": str(a.created_at) if a.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/assessments")
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = PerformanceAssessment(**data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "message": "考核记录创建成功"}


@router.put("/assessments/{ass_id}")
def update_assessment(ass_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="考核记录不存在")
    for key, val in data.items():
        if hasattr(a, key):
            setattr(a, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.post("/scores")
def create_score(data: ScoreCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = PerformanceScore(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    # 重新计算总分
    assessment = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == data.assessment_id).first()
    if assessment:
        total = db.query(PerformanceScore).filter(
            PerformanceScore.assessment_id == data.assessment_id
        ).all()
        # 简单加权求和
        score_sum = 0
        for sc in total:
            item = db.query(PerformanceItem).filter(PerformanceItem.id == sc.item_id).first()
            weight = item.weight if item else 0
            score_sum += sc.score * weight / 100
        assessment.total_score = round(score_sum, 2)
        # 定级
        if score_sum >= 90:
            assessment.grade = "S"
        elif score_sum >= 80:
            assessment.grade = "A"
        elif score_sum >= 70:
            assessment.grade = "B"
        elif score_sum >= 60:
            assessment.grade = "C"
        else:
            assessment.grade = "D"
        assessment.status = "已完成"
        db.commit()
    return {"id": s.id, "message": "评分成功"}


@router.get("/stats")
def performance_stats(year: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """绩效分布统计"""
    from sqlalchemy import func
    q = db.query(PerformanceAssessment.grade, func.count(PerformanceAssessment.id))
    if year:
        q = q.join(PerformancePlan).filter(PerformancePlan.year == year)
    grades = q.group_by(PerformanceAssessment.grade).all()
    return {
        "grade_distribution": [{"grade": g[0] or "未评级", "count": g[1]} for g in grades],
        "total_assessments": sum(g[1] for g in grades),
    }
