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

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse

from app.guards import get_current_user, require_role
from app.models import TokenData
from app.config import UPLOADS_DIR

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
    return {"categories": categories, "count": len(categories)}


@router.post("/upload", status_code=201)
async def upload_csv(
    file:     UploadFile = File(...,  description="CSV file to upload"),
    category: str        = Form(...,  description="Category name (e.g. leads, sales, employees)"),
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

    filepath  = _category_path(category)
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

    # 4. Append or create
    file_exists = os.path.exists(filepath)

    if file_exists:
        # --- APPEND MODE ---
        # Read existing headers to maintain column order
        with open(filepath, "r", newline="", encoding="utf-8") as f:
            existing_headers = csv.DictReader(f).fieldnames or []

        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=existing_headers, extrasaction="ignore")
            # Fill any missing columns from incoming rows with empty string
            normalized = [
                {col: row.get(col, "") for col in existing_headers}
                for row in incoming_rows
            ]
            writer.writerows(normalized)

        action = "appended"

    else:
        # --- CREATE MODE ---
        new_headers = list(incoming_rows[0].keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_headers)
            writer.writeheader()
            writer.writerows(incoming_rows)

        action = "created"

    return {
        "message":    f"Category '{category}' {action} successfully",
        "action":     action,
        "category":   _safe_category(category),
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

    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader  = csv.DictReader(f)
        data    = [row for _, row in zip(range(rows), reader)]
        columns = reader.fieldnames or []

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


@router.delete("/{category}", dependencies=[Depends(require_role("manager", "hr"))])
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
