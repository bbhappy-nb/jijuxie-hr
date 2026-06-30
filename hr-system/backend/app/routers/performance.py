"""绩效管理路由 — 完整版"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.performance import (
    PerformancePlan, PerformanceItem, PerformanceAssessment, PerformanceScore, AssessmentEvaluator,
)
from app.models.employee import Employee, Department, User
from app.auth import get_current_user
from app.schemas import (
    PerformancePlanCreate, PerformancePlanUpdate, AssessmentCreate, ScoreCreate,
    AssessmentEvaluatorCreate, BatchAssessmentCreate, SelfReviewSubmit, ScoreBatchCreate,
    PerformanceItemCreate, PerformanceItemUpdate, PaginatedResponse,
)

router = APIRouter(prefix="/api/performance", tags=["绩效管理"])


# ==================== 考核方案 CRUD ====================

@router.get("/plans", response_model=PaginatedResponse)
def list_plans(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None, status: Optional[str] = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    q = db.query(PerformancePlan)
    if year:
        q = q.filter(PerformancePlan.year == year)
    if status:
        q = q.filter(PerformancePlan.status == status)
    total = q.count()
    plans = q.order_by(PerformancePlan.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in plans:
        cnt = db.query(PerformanceAssessment).filter(PerformanceAssessment.plan_id == p.id).count()
        result.append({
            "id": p.id, "name": p.name, "period": p.period, "year": p.year,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "type": p.type, "description": p.description, "status": p.status,
            "grade_s_threshold": p.grade_s_threshold or 90,
            "grade_a_threshold": p.grade_a_threshold or 80,
            "grade_b_threshold": p.grade_b_threshold or 70,
            "grade_c_threshold": p.grade_c_threshold or 60,
            "bonus_coefficients": p.bonus_coefficients,
            "self_review_enabled": p.self_review_enabled if p.self_review_enabled is not None else 1,
            "assessment_count": cnt,
            "created_at": str(p.created_at) if p.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/plans")
def create_plan(data: PerformancePlanCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    p = PerformancePlan(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "message": "考核方案创建成功"}


@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, data: PerformancePlanUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="方案不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        if hasattr(p, key):
            setattr(p, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="方案不存在")
    db.query(PerformanceScore).filter(
        PerformanceScore.assessment.has(PerformanceAssessment.plan_id == plan_id)
    ).delete(synchronize_session=False)
    db.query(AssessmentEvaluator).filter(
        AssessmentEvaluator.assessment.has(PerformanceAssessment.plan_id == plan_id)
    ).delete(synchronize_session=False)
    db.query(PerformanceAssessment).filter(PerformanceAssessment.plan_id == plan_id).delete()
    db.query(PerformanceItem).filter(PerformanceItem.plan_id == plan_id).delete()
    db.delete(p)
    db.commit()
    return {"message": "已删除方案及关联数据"}


@router.put("/plans/{plan_id}/grading")
def update_plan_grading(plan_id: int, data: PerformancePlanUpdate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    """更新评级阈值和奖金系数"""
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="方案不存在")
    grading_fields = ["grade_s_threshold", "grade_a_threshold", "grade_b_threshold",
                      "grade_c_threshold", "bonus_coefficients", "self_review_enabled"]
    for key, val in data.model_dump(exclude_unset=True).items():
        if key in grading_fields:
            setattr(p, key, val)
    db.commit()
    return {"message": "评级配置已更新"}


# ==================== 考核指标 CRUD ====================

@router.get("/plans/{plan_id}/items")
def list_items(plan_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    items = db.query(PerformanceItem).filter(
        PerformanceItem.plan_id == plan_id
    ).order_by(PerformanceItem.sort_order).all()
    return [{
        "id": i.id, "plan_id": i.plan_id, "name": i.name,
        "description": i.description, "weight": i.weight,
        "target": i.target, "actual_value": i.actual_value,
        "scoring_method": i.scoring_method, "sort_order": i.sort_order,
    } for i in items]


@router.post("/plans/{plan_id}/items")
def create_item(plan_id: int, data: PerformanceItemCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    item = PerformanceItem(plan_id=plan_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "指标创建成功"}


@router.put("/items/{item_id}")
def update_item(item_id: int, data: PerformanceItemUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    item = db.query(PerformanceItem).filter(PerformanceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="指标不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        if hasattr(item, key):
            setattr(item, key, val)
    db.commit()
    return {"message": "指标已更新"}


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    item = db.query(PerformanceItem).filter(PerformanceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="指标不存在")
    db.query(PerformanceScore).filter(PerformanceScore.item_id == item_id).delete()
    db.delete(item)
    db.commit()
    return {"message": "已删除"}


# ==================== 考核评估 CRUD ====================

@router.get("/assessments", response_model=PaginatedResponse)
def list_assessments(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    plan_id: Optional[int] = None, employee_id: Optional[int] = None,
    status: Optional[str] = None, self_review_status: Optional[str] = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    q = db.query(PerformanceAssessment)
    if plan_id:
        q = q.filter(PerformanceAssessment.plan_id == plan_id)
    if employee_id:
        q = q.filter(PerformanceAssessment.employee_id == employee_id)
    if status:
        q = q.filter(PerformanceAssessment.status == status)
    if self_review_status:
        q = q.filter(PerformanceAssessment.self_review_status == self_review_status)
    total = q.count()
    assessments = q.order_by(PerformanceAssessment.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    result = []
    for a in assessments:
        emp = a.employee
        eva = a.evaluator
        plan = a.plan
        result.append({
            "id": a.id, "plan_id": a.plan_id, "plan_name": plan.name if plan else None,
            "employee_id": a.employee_id, "employee_name": emp.name if emp else None,
            "evaluator_id": a.evaluator_id, "evaluator_name": eva.name if eva else None,
            "total_score": a.total_score, "grade": a.grade,
            "self_review": a.self_review, "self_review_status": a.self_review_status,
            "evaluator_comment": a.evaluator_comment,
            "employee_confirmed": a.employee_confirmed,
            "status": a.status,
            "created_at": str(a.created_at) if a.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/assessments")
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    a = PerformanceAssessment(**data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "message": "考核记录创建成功"}


@router.post("/assessments/batch")
def batch_create_assessments(data: BatchAssessmentCreate, db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    """批量生成考核记录"""
    q = db.query(Employee).filter(Employee.status.in_(["在职", "试用期"]))
    if data.department_id:
        q = q.filter(Employee.department_id == data.department_id)
    if data.employee_ids:
        q = q.filter(Employee.id.in_(data.employee_ids))
    employees = q.all()

    count = 0
    for emp in employees:
        exists = db.query(PerformanceAssessment).filter(
            PerformanceAssessment.plan_id == data.plan_id,
            PerformanceAssessment.employee_id == emp.id,
        ).first()
        if exists:
            continue
        a = PerformanceAssessment(
            plan_id=data.plan_id, employee_id=emp.id,
            evaluator_id=data.evaluator_id,
        )
        db.add(a)
        count += 1

    db.commit()
    return {"message": f"已为 {count} 名员工创建考核记录", "count": count}


@router.put("/assessments/{ass_id}")
def update_assessment(ass_id: int, data: dict, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="考核记录不存在")
    for key, val in data.items():
        if hasattr(a, key):
            setattr(a, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/assessments/{ass_id}")
def delete_assessment(ass_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.query(PerformanceScore).filter(PerformanceScore.assessment_id == ass_id).delete()
    db.query(AssessmentEvaluator).filter(AssessmentEvaluator.assessment_id == ass_id).delete()
    db.delete(a)
    db.commit()
    return {"message": "已删除"}


@router.get("/assessments/{ass_id}/detail")
def get_assessment_detail(ass_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="记录不存在")
    plan = a.plan
    emp = a.employee
    scores = db.query(PerformanceScore).filter(PerformanceScore.assessment_id == ass_id).all()
    evaluators = db.query(AssessmentEvaluator).filter(
        AssessmentEvaluator.assessment_id == ass_id).all()

    return {
        "id": a.id,
        "plan": {
            "id": plan.id, "name": plan.name, "type": plan.type, "period": plan.period,
            "grade_s": plan.grade_s_threshold or 90,
            "grade_a": plan.grade_a_threshold or 80,
            "grade_b": plan.grade_b_threshold or 70,
            "grade_c": plan.grade_c_threshold or 60,
            "bonus_coefficients": plan.bonus_coefficients,
            "self_review_enabled": plan.self_review_enabled,
        } if plan else None,
        "employee": {"id": emp.id, "name": emp.name, "department": emp.department.name if emp.department else None} if emp else None,
        "evaluator": {"id": a.evaluator_id, "name": a.evaluator.name if a.evaluator else None},
        "total_score": a.total_score, "grade": a.grade,
        "self_review": a.self_review, "self_review_status": a.self_review_status,
        "evaluator_comment": a.evaluator_comment,
        "employee_confirmed": a.employee_confirmed,
        "status": a.status,
        "scores": [{
            "id": s.id, "item_id": s.item_id, "item_name": s.item.name if s.item else None,
            "score": s.score, "comment": s.comment,
            "weight": s.item.weight if s.item else 0,
        } for s in scores],
        "evaluators": [{
            "id": e.id, "evaluator_id": e.evaluator_id,
            "evaluator_name": e.evaluator.name if e.evaluator else None,
            "evaluator_type": e.evaluator_type, "weight": e.weight,
            "total_score": e.total_score, "grade": e.grade,
            "comment": e.comment, "status": e.status,
        } for e in evaluators],
    }


# ==================== 自评流程 ====================

@router.put("/assessments/{ass_id}/self-review")
def submit_self_review(ass_id: int, data: SelfReviewSubmit, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="记录不存在")
    a.self_review = data.self_review
    a.self_review_status = "已提交"
    db.commit()
    return {"message": "自评已提交"}


@router.put("/assessments/{ass_id}/confirm")
def employee_confirm(ass_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="记录不存在")
    a.employee_confirmed = 1
    a.confirmed_at = datetime.now()
    a.status = "已确认"
    db.commit()
    return {"message": "已确认"}


# ==================== 360 评估人 ====================

@router.post("/assessments/{ass_id}/evaluators")
def add_evaluator(ass_id: int, data: AssessmentEvaluatorCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    e = AssessmentEvaluator(assessment_id=ass_id, **data.model_dump(exclude={"assessment_id"}))
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "message": "评估人已添加"}


@router.delete("/assessments/evaluators/{eval_id}")
def delete_evaluator(eval_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    e = db.query(AssessmentEvaluator).filter(AssessmentEvaluator.id == eval_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(e)
    db.commit()
    return {"message": "已删除"}


@router.get("/assessments/{ass_id}/evaluators")
def list_evaluators(ass_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    evaluators = db.query(AssessmentEvaluator).filter(
        AssessmentEvaluator.assessment_id == ass_id).all()
    return [{
        "id": e.id, "evaluator_id": e.evaluator_id,
        "evaluator_name": e.evaluator.name if e.evaluator else None,
        "evaluator_type": e.evaluator_type, "weight": e.weight,
        "total_score": e.total_score, "grade": e.grade,
        "comment": e.comment, "status": e.status,
        "completed_at": str(e.completed_at) if e.completed_at else None,
    } for e in evaluators]


# ==================== 评分 ====================

def _apply_grading(assessment_id: int, db: Session):
    """重新计算评估总分和等级 (使用方案的自定义阈值)"""
    assessment = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.id == assessment_id).first()
    if not assessment:
        return

    # 检查是否有360评估人
    evaluators = db.query(AssessmentEvaluator).filter(
        AssessmentEvaluator.assessment_id == assessment_id,
        AssessmentEvaluator.status == "已完成",
    ).all()

    if evaluators:
        # 360: 加权平均
        total_weight = sum(e.weight or 100 for e in evaluators)
        if total_weight > 0:
            weighted_sum = sum((e.total_score or 0) * (e.weight or 100) for e in evaluators)
            assessment.total_score = round(weighted_sum / total_weight, 2)
    else:
        # 单评估人: 指标加权求和
        scores = db.query(PerformanceScore).filter(
            PerformanceScore.assessment_id == assessment_id).all()
        if scores:
            score_sum = 0
            for sc in scores:
                item = sc.item
                weight = item.weight if item else 0
                score_sum += (sc.score or 0) * weight / 100
            assessment.total_score = round(score_sum, 2)

    # 使用方案的自定义阈值定级
    plan = assessment.plan
    if plan:
        s_threshold = plan.grade_s_threshold or 90
        a_threshold = plan.grade_a_threshold or 80
        b_threshold = plan.grade_b_threshold or 70
        c_threshold = plan.grade_c_threshold or 60
    else:
        s_threshold, a_threshold, b_threshold, c_threshold = 90, 80, 70, 60

    if assessment.total_score >= s_threshold:
        assessment.grade = "S"
    elif assessment.total_score >= a_threshold:
        assessment.grade = "A"
    elif assessment.total_score >= b_threshold:
        assessment.grade = "B"
    elif assessment.total_score >= c_threshold:
        assessment.grade = "C"
    else:
        assessment.grade = "D"

    assessment.status = "已完成"
    db.commit()


@router.post("/scores")
def create_score(data: ScoreCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    s = PerformanceScore(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    _apply_grading(data.assessment_id, db)
    assessment = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.id == data.assessment_id).first()
    return {
        "id": s.id, "message": "评分成功",
        "total_score": assessment.total_score if assessment else 0,
        "grade": assessment.grade if assessment else None,
    }


@router.post("/scores/batch")
def batch_create_scores(data: ScoreBatchCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    for sc_data in data.scores:
        s = PerformanceScore(assessment_id=data.assessment_id, **sc_data.model_dump())
        db.add(s)
    db.commit()
    _apply_grading(data.assessment_id, db)
    assessment = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.id == data.assessment_id).first()
    return {
        "message": f"已提交 {len(data.scores)} 项评分",
        "total_score": assessment.total_score if assessment else 0,
        "grade": assessment.grade if assessment else None,
    }


@router.put("/evaluators/{evaluator_id}/score")
def update_evaluator_score(evaluator_id: int, total_score: float = 0, grade: str = None,
                           comment: str = None, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    """更新360评估人的打分"""
    e = db.query(AssessmentEvaluator).filter(AssessmentEvaluator.id == evaluator_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="记录不存在")
    e.total_score = total_score
    if grade:
        e.grade = grade
    if comment:
        e.comment = comment
    e.status = "已完成"
    e.completed_at = datetime.now()
    db.commit()
    _apply_grading(e.assessment_id, db)
    return {"message": "评分已更新"}


# ==================== 员工绩效轨迹 ====================

@router.get("/employee/{employee_id}/timeline")
def employee_performance_timeline(employee_id: int, year: Optional[int] = None,
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)):
    q = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.employee_id == employee_id
    )
    if year:
        q = q.join(PerformancePlan).filter(PerformancePlan.year == year)
    assessments = q.order_by(PerformanceAssessment.created_at.desc()).all()

    timeline = []
    for a in assessments:
        plan = a.plan
        scores = db.query(PerformanceScore).filter(
            PerformanceScore.assessment_id == a.id).all()
        timeline.append({
            "id": a.id, "plan_name": plan.name if plan else None,
            "period": plan.period if plan else None, "type": plan.type if plan else None,
            "total_score": a.total_score, "grade": a.grade, "status": a.status,
            "evaluator_comment": a.evaluator_comment,
            "created_at": str(a.created_at) if a.created_at else None,
            "scores": [{"item_name": s.item.name if s.item else None, "score": s.score} for s in scores],
        })

    # 最近一次评估的雷达图数据
    latest = assessments[0] if assessments else None
    radar = []
    if latest:
        latest_scores = db.query(PerformanceScore).filter(
            PerformanceScore.assessment_id == latest.id).all()
        radar = [{
            "item_name": s.item.name if s.item else "未知",
            "score": s.score, "weight": s.item.weight if s.item else 0,
        } for s in latest_scores]

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    return {
        "employee": {"id": emp.id, "name": emp.name, "department": emp.department.name if emp and emp.department else None} if emp else None,
        "total_assessments": len(timeline),
        "grades_summary": {
            "S": sum(1 for t in timeline if t["grade"] == "S"),
            "A": sum(1 for t in timeline if t["grade"] == "A"),
            "B": sum(1 for t in timeline if t["grade"] == "B"),
            "C": sum(1 for t in timeline if t["grade"] == "C"),
            "D": sum(1 for t in timeline if t["grade"] == "D"),
        },
        "radar": radar,
        "timeline": timeline,
    }


@router.get("/employee/{employee_id}/stats")
def employee_performance_stats(employee_id: int, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    """员工绩效统计数据"""
    assessments = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.employee_id == employee_id
    ).all()
    total = len(assessments)
    if total == 0:
        return {"message": "暂无绩效记录"}

    avg_score = sum(a.total_score or 0 for a in assessments) / total
    grades = [a.grade for a in assessments if a.grade]
    grade_map = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
    avg_grade_num = sum(grade_map.get(g, 0) for g in grades) / len(grades) if grades else 0

    # 趋势
    trend = []
    for a in sorted(assessments, key=lambda x: x.created_at or datetime.min):
        plan = a.plan
        trend.append({
            "label": f"{plan.year if plan else '?'}/{plan.period if plan else '?'}",
            "score": a.total_score,
        })

    return {
        "total_assessments": total,
        "average_score": round(avg_score, 2),
        "average_grade": round(avg_grade_num, 2),
        "trend": trend[-12:],
    }


# ==================== 统计 ====================

@router.get("/stats")
def performance_stats(year: Optional[int] = None, plan_id: Optional[int] = None,
                      db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """绩效分布统计"""
    q = db.query(PerformanceAssessment)
    if year:
        q = q.join(PerformancePlan).filter(PerformancePlan.year == year)
    if plan_id:
        q = q.filter(PerformanceAssessment.plan_id == plan_id)

    assessments = q.all()
    grade_dist = {}
    for a in assessments:
        g = a.grade or "未评级"
        grade_dist[g] = grade_dist.get(g, 0) + 1

    # 完成率
    completed = sum(1 for a in assessments if a.status in ("已完成", "已确认"))
    completion_rate = round(completed / max(len(assessments), 1) * 100, 1)

    return {
        "grade_distribution": [{"grade": k, "count": v} for k, v in sorted(grade_dist.items())],
        "total_assessments": len(assessments),
        "completed": completed,
        "completion_rate": completion_rate,
    }
