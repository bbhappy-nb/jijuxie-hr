"""员工管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime
import openpyxl
from io import BytesIO

from app.database import get_db
from app.models.employee import Employee, Department, Position, User
from app.auth import get_current_user, hash_password
from app.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    DepartmentCreate, DepartmentResponse,
    PositionCreate, PositionResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/api", tags=["员工管理"])


# ========== 员工 CRUD ==========
@router.get("/employees", response_model=PaginatedResponse)
def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """员工列表（分页+搜索+筛选）"""
    q = db.query(Employee)
    if keyword:
        q = q.filter(or_(
            Employee.name.contains(keyword),
            Employee.employee_no.contains(keyword),
            Employee.phone.contains(keyword),
        ))
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if status:
        q = q.filter(Employee.status == status)

    total = q.count()
    items = q.order_by(Employee.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for emp in items:
        result.append({
            "id": emp.id,
            "employee_no": emp.employee_no,
            "name": emp.name,
            "gender": emp.gender,
            "phone": emp.phone,
            "email": emp.email,
            "education": emp.education,
            "department_id": emp.department_id,
            "department_name": emp.department.name if emp.department else None,
            "position_id": emp.position_id,
            "position_name": emp.position.name if emp.position else None,
            "status": emp.status,
            "hire_date": str(emp.hire_date) if emp.hire_date else None,
            "probation_end": str(emp.probation_end) if emp.probation_end else None,
            "resign_date": str(emp.resign_date) if emp.resign_date else None,
            "base_salary": emp.base_salary,
            "birthday": str(emp.birthday) if emp.birthday else None,
            "created_at": str(emp.created_at) if emp.created_at else None,
        })

    return {"total": total, "page": page, "page_size": page_size, "items": result}


@router.get("/employees/{emp_id}")
def get_employee(emp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """员工详情"""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    return {
        "id": emp.id,
        "employee_no": emp.employee_no,
        "name": emp.name,
        "gender": emp.gender,
        "phone": emp.phone,
        "email": emp.email,
        "id_card": emp.id_card,
        "education": emp.education,
        "major": emp.major,
        "school": emp.school,
        "address": emp.address,
        "emergency_contact": emp.emergency_contact,
        "emergency_phone": emp.emergency_phone,
        "department_id": emp.department_id,
        "department_name": emp.department.name if emp.department else None,
        "position_id": emp.position_id,
        "position_name": emp.position.name if emp.position else None,
        "status": emp.status,
        "hire_date": str(emp.hire_date) if emp.hire_date else None,
        "resign_date": str(emp.resign_date) if emp.resign_date else None,
        "probation_end": str(emp.probation_end) if emp.probation_end else None,
        "base_salary": emp.base_salary,
        "bank_account": emp.bank_account,
        "bank_name": emp.bank_name,
        "birthday": str(emp.birthday) if emp.birthday else None,
        "created_at": str(emp.created_at) if emp.created_at else None,
        "updated_at": str(emp.updated_at) if emp.updated_at else None,
    }


@router.post("/employees")
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """新增员工"""
    exists = db.query(Employee).filter(Employee.employee_no == data.employee_no).first()
    if exists:
        raise HTTPException(status_code=400, detail="工号已存在")
    emp = Employee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {"id": emp.id, "message": "员工创建成功"}


@router.put("/employees/{emp_id}")
def update_employee(emp_id: int, data: EmployeeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新员工信息"""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    for key, val in update_data.items():
        setattr(emp, key, val)
    emp.updated_at = datetime.now()
    db.commit()
    return {"message": "更新成功"}


@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除员工"""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    db.delete(emp)
    db.commit()
    return {"message": "删除成功"}


@router.post("/employees/import")
async def import_employees(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """批量导入员工（Excel）"""
    contents = await file.read()
    wb = openpyxl.load_workbook(BytesIO(contents))
    ws = wb.active
    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        emp = Employee(
            employee_no=str(row[0]) if row[0] else "",
            name=str(row[1]) if row[1] else "",
            gender=str(row[2]) if len(row) > 2 and row[2] else "男",
            phone=str(row[3]) if len(row) > 3 and row[3] else None,
            email=str(row[4]) if len(row) > 4 and row[4] else None,
            department_id=int(row[5]) if len(row) > 5 and row[5] else None,
            base_salary=float(row[6]) if len(row) > 6 and row[6] else 0,
        )
        db.add(emp)
        count += 1
    db.commit()
    return {"message": f"成功导入 {count} 名员工", "count": count}


# ========== 部门 CRUD ==========
@router.get("/departments")
def list_departments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """部门列表（树形）"""
    depts = db.query(Department).order_by(Department.sort_order).all()

    def build_tree(parent_id=None):
        result = []
        for d in depts:
            if d.parent_id == parent_id:
                emp_count = db.query(Employee).filter(Employee.department_id == d.id, Employee.status != "离职").count()
                result.append({
                    "id": d.id,
                    "name": d.name,
                    "parent_id": d.parent_id,
                    "manager_id": d.manager_id,
                    "description": d.description,
                    "sort_order": d.sort_order,
                    "employee_count": emp_count,
                    "children": build_tree(d.id),
                })
        return result
    return build_tree(None)


@router.post("/departments")
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建部门"""
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"id": dept.id, "message": "部门创建成功"}


@router.put("/departments/{dept_id}")
def update_department(dept_id: int, data: DepartmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新部门"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    for key, val in data.model_dump().items():
        setattr(dept, key, val)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    emp_count = db.query(Employee).filter(Employee.department_id == dept_id).count()
    if emp_count > 0:
        raise HTTPException(status_code=400, detail=f"该部门下还有 {emp_count} 名员工，请先转移")
    db.delete(dept)
    db.commit()
    return {"message": "删除成功"}


# ========== 岗位 CRUD ==========
@router.get("/positions")
def list_positions(department_id: Optional[int] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """岗位列表"""
    q = db.query(Position)
    if department_id:
        q = q.filter(Position.department_id == department_id)
    positions = q.all()
    result = []
    for p in positions:
        current_count = db.query(Employee).filter(Employee.position_id == p.id, Employee.status != "离职").count()
        result.append({
            "id": p.id,
            "name": p.name,
            "department_id": p.department_id,
            "department_name": p.department.name if p.department else None,
            "headcount": p.headcount,
            "description": p.description,
            "requirements": p.requirements,
            "current_count": current_count,
        })
    return result


@router.post("/positions")
def create_position(data: PositionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pos = Position(**data.model_dump())
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return {"id": pos.id, "message": "岗位创建成功"}


@router.put("/positions/{pos_id}")
def update_position(pos_id: int, data: PositionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pos = db.query(Position).filter(Position.id == pos_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")
    for key, val in data.model_dump().items():
        setattr(pos, key, val)
    db.commit()
    return {"message": "更新成功"}
