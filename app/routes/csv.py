# app/routes/csv.py
# CSV upload, preview, download — with RBAC authorization
#
# Upload flow:
#   1. Validate JWT → get username + role
#   2. Sanitize category name → maps to uploads/<category>.csv
#   3. Inject 'added_by' column: "alice (salesperson)" on every row
#   4. Category file exists → APPEND rows (skip re-writing header)
#   5. Category file missing → CREATE new file with header + rows

import os
import io
import csv
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Body
from fastapi.responses import FileResponse

from app.guards import get_current_user, require_role
from app.models import TokenData, CsvRowDataRequest
from app.config import UPLOADS_DIR, CSV_PRESET_CATEGORIES

router = APIRouter(prefix="/csv", tags=["CSV Upload"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_category(category: str) -> str:
    """Sanitize category name — alphanumeric, hyphens, underscores only."""
    safe = "".join(c for c in category if c.isalnum() or c in "-_").lower()
    if not safe:
        raise HTTPException(status_code=400, detail="Invalid category name — use letters, numbers, hyphens or underscores")
    return safe


def _category_path(category: str) -> str:
    """Return the absolute path for uploads/<category>.csv."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    return os.path.join(UPLOADS_DIR, f"{_safe_category(category)}.csv")


def _read_csv(filepath: str) -> tuple[list[str], list[dict]]:
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    return headers, rows


def _write_csv(filepath: str, headers: list[str], rows: list[dict]) -> None:
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _ensure_headers(headers: list[str], required: list[str]) -> tuple[list[str], list[str]]:
    missing = [h for h in required if h not in headers]
    return headers + missing, missing


def _resolve_category(category: str, custom_category: str | None) -> str:
    if category.lower() == "others":
        if not custom_category:
            raise HTTPException(status_code=400, detail="custom_category is required when category is 'others'")
        return custom_category
    return category


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/categories")
async def list_categories(current_user: TokenData = Depends(get_current_user)):
    """
    List all available CSV categories.
    Any authenticated user (salesperson / manager / hr) can view.
    """
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    categories = [
        f.replace(".csv", "")
        for f in sorted(os.listdir(UPLOADS_DIR))
        if f.endswith(".csv")
    ]
    preset = list(CSV_PRESET_CATEGORIES)
    all_categories = sorted(set(preset + categories))
    return {
        "preset": preset,
        "existing": categories,
        "all": all_categories,
        "count": len(all_categories),
    }


@router.post("/upload", status_code=201, dependencies=[Depends(require_role("salesperson", "manager"))])
async def upload_csv(
    file:     UploadFile = File(...,  description="CSV file to upload"),
    category: str        = Form(...,  description="Category name (e.g. leads, sales, employees)"),
    custom_category: str | None = Form(None, description="Custom name when category is 'others'"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Upload a CSV file to a named category.

    - **Any authenticated role** can upload (salesperson / manager / hr).
    - An `added_by` column is automatically added to every row: `username (role)`.
    - An `uploaded_at` column (UTC timestamp) is also injected.
    - If the category already exists → rows are **appended**.
    - If the category is new → a **new file is created**.
    """
    # 1. Validate file type
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    resolved_category = _resolve_category(category, custom_category)
    filepath  = _category_path(resolved_category)
    added_by  = f"{current_user.username} ({current_user.role})"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 2. Read and parse the uploaded file
    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")  # handles BOM from Excel-exported CSVs
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported — save as UTF-8 CSV")

    reader       = csv.DictReader(io.StringIO(text))
    incoming_rows = list(reader)

    if not incoming_rows:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains only a header row")

    # 3. Inject audit columns on every row
    for row in incoming_rows:
        row["added_by"]    = added_by
        row["uploaded_at"] = timestamp

    # 4. Append or create (rewrite to ensure audit columns exist)
    file_exists = os.path.exists(filepath)
    required_headers = ["added_by", "uploaded_at"]

    if file_exists:
        existing_headers, existing_rows = _read_csv(filepath)
        new_headers, missing = _ensure_headers(existing_headers, required_headers)
        if missing:
            for row in existing_rows:
                for col in missing:
                    row.setdefault(col, "")

        normalized = [
            {col: row.get(col, "") for col in new_headers}
            for row in incoming_rows
        ]
        all_rows = existing_rows + normalized
        _write_csv(filepath, new_headers, all_rows)
        action = "appended"
    else:
        new_headers, _ = _ensure_headers(list(incoming_rows[0].keys()), required_headers)
        normalized = [
            {col: row.get(col, "") for col in new_headers}
            for row in incoming_rows
        ]
        _write_csv(filepath, new_headers, normalized)
        action = "created"

    return {
        "message":    f"Category '{category}' {action} successfully",
        "action":     action,
        "category":   _safe_category(resolved_category),
        "rows_added": len(incoming_rows),
        "added_by":   added_by,
        "file":       filepath,
    }


@router.get("/preview/{category}")
async def preview_csv(
    category: str,
    rows:     int = 20,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Preview the first N rows of a category CSV as JSON.
    Default: 20 rows. Use `?rows=50` to change.
    """
    filepath = _category_path(category)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    headers, all_rows = _read_csv(filepath)
    data = all_rows[:rows]
    columns = headers

    return {
        "category":     _safe_category(category),
        "columns":      columns,
        "preview_rows": len(data),
        "data":         data,
    }


@router.get("/download/{category}")
async def download_csv(
    category: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Download the full CSV for a category as a file attachment.
    Any authenticated user can download.
    """
    filepath = _category_path(category)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    return FileResponse(
        path=filepath,
        media_type="text/csv",
        filename=f"{_safe_category(category)}.csv",
    )


@router.delete("/{category}", dependencies=[Depends(require_role("manager"))])
async def delete_category(
    category: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete a category CSV file entirely.
    Restricted to **manager** and **hr** only.
    """
    filepath = _category_path(category)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    os.remove(filepath)
    return {
        "message":    f"Category '{category}' deleted",
        "deleted_by": f"{current_user.username} ({current_user.role})",
    }


@router.get("/rows/{category}")
async def list_rows(
    category: str,
    offset: int = 0,
    limit: int = 50,
    current_user: TokenData = Depends(get_current_user),
):
    """Read CSV rows with pagination."""
    filepath = _category_path(category)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    headers, rows = _read_csv(filepath)
    if offset < 0 or limit < 1:
        raise HTTPException(status_code=400, detail="offset must be >= 0 and limit must be >= 1")

    sliced = rows[offset:offset + limit]
    return {
        "category": _safe_category(category),
        "columns": headers,
        "offset": offset,
        "limit": limit,
        "returned": len(sliced),
        "total": len(rows),
        "data": sliced,
    }


@router.post("/rows/{category}", status_code=201)
async def add_row(
    category: str,
    body: CsvRowDataRequest = Body(...),
    current_user: TokenData = Depends(require_role("salesperson", "manager")),
):
    """Add a single row to a category CSV (salesperson / manager)."""
    filepath = _category_path(category)
    added_by = f"{current_user.username} ({current_user.role})"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    required_headers = ["added_by", "uploaded_at"]

    if os.path.exists(filepath):
        headers, rows = _read_csv(filepath)
        headers, missing = _ensure_headers(headers, required_headers)
        if missing:
            for row in rows:
                for col in missing:
                    row.setdefault(col, "")
    else:
        headers, _ = _ensure_headers(list(body.data.keys()), required_headers)
        rows = []

    new_row = {col: body.data.get(col, "") for col in headers}
    new_row["added_by"] = added_by
    new_row["uploaded_at"] = timestamp
    rows.append(new_row)

    _write_csv(filepath, headers, rows)

    return {
        "message": f"Row added to '{_safe_category(category)}'",
        "row_number": len(rows),
        "added_by": added_by,
    }


@router.put("/rows/{category}/{row_number}")
async def update_row(
    category: str,
    row_number: int,
    body: CsvRowDataRequest = Body(...),
    current_user: TokenData = Depends(require_role("manager")),
):
    """Update a row by row number (manager only)."""
    filepath = _category_path(category)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    headers, rows = _read_csv(filepath)
    if row_number < 1 or row_number > len(rows):
        raise HTTPException(status_code=404, detail="Row number not found")

    restricted = {"added_by", "uploaded_at", "updated_by", "updated_at"}
    allowed_keys = [k for k in body.data.keys() if k in headers and k not in restricted]
    ignored = [k for k in body.data.keys() if k not in headers or k in restricted]

    row = rows[row_number - 1]
    for key in allowed_keys:
        row[key] = body.data[key]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    headers, missing = _ensure_headers(headers, ["updated_by", "updated_at"])
    if missing:
        for r in rows:
            for col in missing:
                r.setdefault(col, "")

    row["updated_by"] = f"{current_user.username} ({current_user.role})"
    row["updated_at"] = timestamp

    _write_csv(filepath, headers, rows)

    return {
        "message": f"Row {row_number} updated",
        "row_number": row_number,
        "updated_by": row["updated_by"],
        "ignored_fields": ignored,
    }


@router.delete("/rows/{category}/{row_number}")
async def delete_row(
    category: str,
    row_number: int,
    current_user: TokenData = Depends(require_role("manager")),
):
    """Delete a row by row number (manager only)."""
    filepath = _category_path(category)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    headers, rows = _read_csv(filepath)
    if row_number < 1 or row_number > len(rows):
        raise HTTPException(status_code=404, detail="Row number not found")

    deleted = rows.pop(row_number - 1)
    _write_csv(filepath, headers, rows)

    return {
        "message": f"Row {row_number} deleted",
        "deleted_by": f"{current_user.username} ({current_user.role})",
        "deleted_row": deleted,
    }
