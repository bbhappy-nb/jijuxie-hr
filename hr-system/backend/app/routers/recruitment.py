"""招聘管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.recruitment import Recruitment, Candidate
from app.models.employee import User
from app.auth import get_current_user
from app.schemas import RecruitmentCreate, CandidateCreate, CandidateUpdate, PaginatedResponse

router = APIRouter(prefix="/api/recruitment", tags=["招聘管理"])


@router.get("/jobs", response_model=PaginatedResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Recruitment)
    if status:
        q = q.filter(Recruitment.status == status)
    total = q.count()
    items = q.order_by(Recruitment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for r in items:
        cnt = db.query(Candidate).filter(Candidate.recruitment_id == r.id).count()
        result.append({
            "id": r.id, "title": r.title, "department_id": r.department_id,
            "headcount": r.headcount, "salary_range": r.salary_range,
            "requirements": r.requirements, "channel": r.channel,
            "priority": r.priority, "status": r.status,
            "publish_date": str(r.publish_date) if r.publish_date else None,
            "candidate_count": cnt,
            "created_at": str(r.created_at) if r.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/jobs")
def create_job(data: RecruitmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = Recruitment(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "message": "招聘岗位创建成功"}


@router.put("/jobs/{job_id}")
def update_job(job_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = db.query(Recruitment).filter(Recruitment.id == job_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="岗位不存在")
    for key, val in data.items():
        if hasattr(r, key):
            setattr(r, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.get("/candidates", response_model=PaginatedResponse)
def list_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = None,
    recruitment_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Candidate)
    if stage:
        q = q.filter(Candidate.stage == stage)
    if recruitment_id:
        q = q.filter(Candidate.recruitment_id == recruitment_id)
    if keyword:
        from sqlalchemy import or_
        q = q.filter(or_(Candidate.name.contains(keyword), Candidate.phone.contains(keyword)))
    total = q.count()
    items = q.order_by(Candidate.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for c in items:
        job_title = c.recruitment.title if c.recruitment else None
        result.append({
            "id": c.id, "name": c.name, "phone": c.phone, "email": c.email,
            "education": c.education, "years_of_work": c.years_of_work,
            "current_company": c.current_company, "current_position": c.current_position,
            "expected_salary": c.expected_salary, "channel": c.channel,
            "recruitment_id": c.recruitment_id, "recruitment_title": job_title,
            "stage": c.stage, "interview_date": str(c.interview_date) if c.interview_date else None,
            "interviewer": c.interviewer, "interview_feedback": c.interview_feedback,
            "offer_date": str(c.offer_date) if c.offer_date else None,
            "offer_salary": c.offer_salary,
            "onboard_date": str(c.onboard_date) if c.onboard_date else None,
            "remark": c.remark, "is_onboarded": c.is_onboarded,
            "created_at": str(c.created_at) if c.created_at else None,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.post("/candidates")
def create_candidate(data: CandidateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = Candidate(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "message": "候选人添加成功"}


@router.put("/candidates/{cand_id}")
def update_candidate(cand_id: int, data: CandidateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Candidate).filter(Candidate.id == cand_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="候选人不存在")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(c, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.get("/stats")
def recruitment_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """招聘渠道分析"""
    from sqlalchemy import func
    channels = db.query(Candidate.channel, func.count(Candidate.id)).group_by(Candidate.channel).all()
    stages = db.query(Candidate.stage, func.count(Candidate.id)).group_by(Candidate.stage).all()
    return {
        "by_channel": [{"name": c[0] or "未知", "value": c[1]} for c in channels],
        "by_stage": [{"name": s[0], "value": s[1]} for s in stages],
        "total_candidates": db.query(func.count(Candidate.id)).scalar() or 0,
        "total_jobs": db.query(func.count(Recruitment.id)).filter(Recruitment.status == "招聘中").scalar() or 0,
    }
