# RBAC Project

A **Role-Based Access Control (RBAC) API** built with FastAPI and MongoDB.  
Supports JWT authentication, user/role/permission management, and secure CSV data upload with per-role access control.

---

## Features

- 🔐 **JWT Authentication** — login and receive a signed token
- 👥 **Three roles** — `salesperson`, `manager`, `hr`
- 📤 **CSV Upload** — upload files into named categories; rows auto-tagged with `added_by = "username (role)"`
- 🧾 **Row CRUD** — manager can add/update/delete/read rows; salesperson can add/read
- 🗂️ **Category management** — append to existing category or create a new one automatically
- 🧩 **Preset categories** — `salon`, `supermarket`, `pharmacy`, `electronics`, `restaurant`, plus `others`
- 🛡️ **Route-level RBAC** — endpoints protected by role using FastAPI dependencies
- 📋 **Swagger UI** — fully interactive API docs at `/docs`

---

## Project Structure

```
rbac_project/
├── app/
│   ├── main.py          ← FastAPI entry point (port 8000)
│   ├── config.py        ← Settings loaded from .env
│   ├── db.py            ← MongoDB CRUD helpers
│   ├── auth.py          ← JWT creation + bcrypt password utils
│   ├── guards.py        ← require_role() / get_current_user() dependencies
│   ├── models.py        ← All Pydantic request/response models
│   └── routes/
│       ├── auth.py      ← POST /auth/login
│       ├── admin.py     ← CRUD for /users, /roles, /permissions
│       └── csv.py       ← CSV upload, preview, download, delete
├── uploads/             ← CSV files stored here by category
├── seed.py              ← Populates MongoDB with test data
├── requirements.txt
├── .env                 ← Environment variables (not committed)
├── .env.example         ← Template for .env
└── .gitignore
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| MongoDB | 6.0+ (running on `localhost:27017`) |

- **Install MongoDB:** https://www.mongodb.com/try/download/community  
- **Start MongoDB:** run `mongod` in a terminal, or use **MongoDB Compass**

---

## Setup & Run

### Step 1 — Clone and enter the project

```bash
cd rbac_project
```

### Step 2 — Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

Copy `.env.example` to `.env` (or edit the existing `.env`):

```bash
cp .env.example .env
```

Default values work out of the box for local development. For production, replace `SECRET_KEY` with a strong random value:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5 — Seed the database

Populates MongoDB with roles, permissions, and test users:

```bash
python seed.py
```

### Step 6 — Start the API

```bash
uvicorn app.main:app --port 8000 --reload
```

The API is now running:

| URL | Description |
|---|---|
| `http://localhost:8000` | Health check |
| `http://localhost:8000/docs` | **Swagger UI** (use this to test) |
| `http://localhost:8000/redoc` | ReDoc documentation |

---

## Test Users (after seeding)

| Username | Password | Role |
|---|---|---|
| `alice` | `alice123` | salesperson |
| `bob` | `bob123` | salesperson |
| `charlie` | `charlie123` | salesperson |
| `evan` | `evan123` | manager |
| `diana` | `diana123` | hr |

---

## API Overview

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Login → returns JWT token |

### Roles / Permissions (Manager)
| Method | Endpoint | Description |
|---|---|---|
| `GET/POST/PUT/DELETE` | `/roles/` | Manage roles |
| `GET/POST/PUT/DELETE` | `/permissions/` | Manage permissions |

### CSV Upload
| Method | Endpoint | Auth | Who |
|---|---|---|---|
| `GET` | `/csv/categories` | ✅ JWT | All roles |
| `POST` | `/csv/upload` | ✅ JWT | salesperson / manager |
| `GET` | `/csv/preview/{category}` | ✅ JWT | All roles |
| `GET` | `/csv/download/{category}` | ✅ JWT | All roles |
| `DELETE` | `/csv/{category}` | ✅ JWT | manager only |

### CSV Row CRUD
| Method | Endpoint | Auth | Who |
|---|---|---|---|
| `GET` | `/csv/rows/{category}` | ✅ JWT | All roles |
| `POST` | `/csv/rows/{category}` | ✅ JWT | salesperson / manager |
| `PUT` | `/csv/rows/{category}/{row_number}` | ✅ JWT | manager only |
| `DELETE` | `/csv/rows/{category}/{row_number}` | ✅ JWT | manager only |

### Users
| Method | Endpoint | Auth | Who |
|---|---|---|---|
| `GET` | `/users/` | ✅ JWT | hr / manager |
| `GET` | `/users/{id}` | ✅ JWT | hr / manager |
| `POST` | `/users/` | ✅ JWT | hr only |
| `PUT` | `/users/{id}` | ✅ JWT | manager only |
| `DELETE` | `/users/{id}` | ✅ JWT | manager only |

### Role Capabilities
| Role | Capabilities |
|---|---|
| salesperson | upload CSV, read CSV, add rows, list categories |
| manager | full CSV CRUD, manage users/roles/permissions |
| hr | create users, read users, read CSV/categories |

---

## CSV Upload Workflow

1. **Login** → `POST /auth/login` → copy the `access_token`
2. **Authorize** in Swagger UI → click 🔒 Authorize → paste `Bearer <token>`
3. **Upload** → `POST /csv/upload`
   - `file`: select your CSV file
   - `category`: pick `salon`, `supermarket`, `pharmacy`, `electronics`, `restaurant`, or `others`
   - `custom_category`: required when `category` is `others`
4. **Result:**
   - Category exists → rows **appended** to `uploads/<category>.csv`
   - Category new → **new file created**
   - Every row gets: `added_by = "alice (salesperson)"` + `uploaded_at`

---


## Troubleshooting

| Problem | Fix |
|---|---|
| `Connection refused` on MongoDB | Make sure MongoDB is running: `mongod` |
| `ModuleNotFoundError` | Run from the project root; re-run `pip install -r requirements.txt` |
| `401 Unauthorized` | Token expired — log in again and re-authorize in Swagger |
| `403 Forbidden` | Your role doesn't have access to that endpoint |
| CSV upload fails | Make sure the file is UTF-8 encoded `.csv` |
