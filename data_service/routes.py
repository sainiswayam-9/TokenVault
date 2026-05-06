# data_service/routes.py
# Full CRUD for Sales, Reports, Employees — each enforcing RBAC

from fastapi import APIRouter, HTTPException, Request, Depends
from data_service.jwt_guard import require_role, get_current_user
from data_service.models import (
    TokenData,
    CreateSalesRecord, UpdateSalesRecord,
    CreateReport,      UpdateReport,
    CreateEmployee,    UpdateEmployee,
)
from data_service.database import (
    get_all_sales, get_sale_by_id, create_sale, update_sale, delete_sale,
    get_all_reports, get_report_by_id, create_report, update_report, delete_report,
    get_all_employees, get_employee_by_id, create_employee, update_employee, delete_employee,
)

# ── /data/me ─────────────────────────────────────────────────────
me_router = APIRouter(prefix="/data", tags=["Profile"])

@me_router.get("/me")
async def get_my_profile(current_user: TokenData = Depends(get_current_user)):
    """Any valid JWT — returns caller's identity and permissions."""
    role_permissions = {
        "salesperson": ["view_own_sales", "create_sale", "update_own_sale", "delete_own_sale"],
        "manager":     ["view_all_sales", "create_sale", "update_sale", "delete_sale",
                        "view_reports", "create_report", "update_report", "delete_report"],
        "hr":          ["view_employees", "create_employee", "update_employee", "delete_employee"],
    }
    return {
        "username": current_user.username,
        "role": current_user.role,
        "permissions": role_permissions.get(current_user.role, []),
    }


# ── SALES (/data/sales) ──────────────────────────────────────────
# salesperson: full CRUD on own records   manager: full CRUD on all
sales_router = APIRouter(prefix="/data/sales", tags=["Sales CRUD"])

@sales_router.get("/")
async def list_sales(
    request: Request,
    current_user: TokenData = Depends(require_role("salesperson", "manager")),
):
    """Salesperson sees own records; manager sees all."""
    owner = current_user.username if current_user.role == "salesperson" else None
    return await get_all_sales(request.app.db, salesperson=owner)


@sales_router.get("/{sale_id}")
async def get_sale(
    sale_id: str,
    request: Request,
    current_user: TokenData = Depends(require_role("salesperson", "manager")),
):
    record = await get_sale_by_id(request.app.db, sale_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sale record not found")
    # Salesperson can only see their own record
    if current_user.role == "salesperson" and record["salesperson"] != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied to this record")
    return record


@sales_router.post("/", status_code=201)
async def add_sale(
    request: Request,
    body: CreateSalesRecord,
    current_user: TokenData = Depends(require_role("salesperson", "manager")),
):
    """Create a new sale. Salesperson's username is auto-set as owner."""
    data = body.model_dump()
    if current_user.role == "salesperson":
        data["salesperson"] = current_user.username  # enforce ownership
    sale_id = await create_sale(request.app.db, data)
    return {"message": "Sale created", "id": sale_id}


@sales_router.put("/{sale_id}")
async def edit_sale(
    sale_id: str,
    request: Request,
    body: UpdateSalesRecord,
    current_user: TokenData = Depends(require_role("salesperson", "manager")),
):
    record = await get_sale_by_id(request.app.db, sale_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sale record not found")
    if current_user.role == "salesperson" and record["salesperson"] != current_user.username:
        raise HTTPException(status_code=403, detail="Cannot edit another salesperson's record")

    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    updated = await update_sale(request.app.db, sale_id, fields)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")
    return {"message": "Sale updated", "id": sale_id, "updated_fields": list(fields.keys())}


@sales_router.delete("/{sale_id}")
async def remove_sale(
    sale_id: str,
    request: Request,
    current_user: TokenData = Depends(require_role("salesperson", "manager")),
):
    record = await get_sale_by_id(request.app.db, sale_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sale record not found")
    if current_user.role == "salesperson" and record["salesperson"] != current_user.username:
        raise HTTPException(status_code=403, detail="Cannot delete another salesperson's record")

    deleted = await delete_sale(request.app.db, sale_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"message": "Sale deleted", "id": sale_id}


# ── REPORTS (/data/reports) ──────────────────────────────────────
# manager only
reports_router = APIRouter(prefix="/data/reports", tags=["Reports CRUD"])

@reports_router.get("/")
async def list_reports(
    request: Request,
    current_user: TokenData = Depends(require_role("manager")),
):
    return await get_all_reports(request.app.db)


@reports_router.get("/{report_id}")
async def get_report(
    report_id: str,
    request: Request,
    current_user: TokenData = Depends(require_role("manager")),
):
    record = await get_report_by_id(request.app.db, report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found")
    return record


@reports_router.post("/", status_code=201)
async def add_report(
    request: Request,
    body: CreateReport,
    current_user: TokenData = Depends(require_role("manager")),
):
    report_id = await create_report(request.app.db, body.model_dump())
    return {"message": "Report created", "id": report_id}


@reports_router.put("/{report_id}")
async def edit_report(
    report_id: str,
    request: Request,
    body: UpdateReport,
    current_user: TokenData = Depends(require_role("manager")),
):
    if not await get_report_by_id(request.app.db, report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = await update_report(request.app.db, report_id, fields)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")
    return {"message": "Report updated", "id": report_id, "updated_fields": list(fields.keys())}


@reports_router.delete("/{report_id}")
async def remove_report(
    report_id: str,
    request: Request,
    current_user: TokenData = Depends(require_role("manager")),
):
    if not await get_report_by_id(request.app.db, report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    deleted = await delete_report(request.app.db, report_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"message": "Report deleted", "id": report_id}


# ── EMPLOYEES (/data/employees) ──────────────────────────────────
# hr only
employees_router = APIRouter(prefix="/data/employees", tags=["Employees CRUD"])

@employees_router.get("/")
async def list_employees(
    request: Request,
    current_user: TokenData = Depends(require_role("hr")),
):
    return await get_all_employees(request.app.db)


@employees_router.get("/{emp_id}")
async def get_employee(
    emp_id: str,
    request: Request,
    current_user: TokenData = Depends(require_role("hr")),
):
    record = await get_employee_by_id(request.app.db, emp_id)
    if not record:
        raise HTTPException(status_code=404, detail="Employee not found")
    return record


@employees_router.post("/", status_code=201)
async def add_employee(
    request: Request,
    body: CreateEmployee,
    current_user: TokenData = Depends(require_role("hr")),
):
    emp_id = await create_employee(request.app.db, body.model_dump())
    return {"message": "Employee created", "id": emp_id}


@employees_router.put("/{emp_id}")
async def edit_employee(
    emp_id: str,
    request: Request,
    body: UpdateEmployee,
    current_user: TokenData = Depends(require_role("hr")),
):
    if not await get_employee_by_id(request.app.db, emp_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = await update_employee(request.app.db, emp_id, fields)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")
    return {"message": "Employee updated", "id": emp_id, "updated_fields": list(fields.keys())}


@employees_router.delete("/{emp_id}")
async def remove_employee(
    emp_id: str,
    request: Request,
    current_user: TokenData = Depends(require_role("hr")),
):
    if not await get_employee_by_id(request.app.db, emp_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    deleted = await delete_employee(request.app.db, emp_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Delete failed")
    return {"message": "Employee deleted", "id": emp_id}
