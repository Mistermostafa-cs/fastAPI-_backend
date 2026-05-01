# Smart School FastAPI Backend

This is a new backend copy for the same project database, implemented with FastAPI.
It runs side-by-side with the current ASP.NET MVC project and uses the same SQL Server schema.

## 1) Setup

```powershell
cd "c:\Graduation project\SSMS\Smart School Management System\fastapi_backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## 2) Run

```powershell
uvicorn app.main:app --reload
```

App docs:
- Swagger: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## 3) Auth flow

1. Call `POST /api/auth/login` with admin credentials.
2. Copy `access_token`.
3. Click Authorize in Swagger and paste `Bearer <token>`.
4. Test protected endpoints (`/api/users`, `/api/roles`, `/api/profiles/{user_id}`).

## 4) Implemented Endpoints

- `GET /health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `GET /api/users/me`
- `GET /api/users`
- `GET /api/users/{user_id}`
- `POST /api/users`
- `PUT /api/users/{user_id}`
- `PATCH /api/users/{user_id}/status`
- `GET /api/roles`
- `GET /api/profiles/{user_id}`
- `PUT /api/profiles/{user_id}`
- `GET /api/academics/academic-years`
- `POST /api/academics/academic-years`
- `GET /api/academics/classes`
- `POST /api/academics/classes`
- `GET /api/academics/subjects`
- `POST /api/academics/subjects`
- `GET /api/academics/class-subjects`
- `POST /api/academics/class-subjects`
- `GET /api/academics/enrollments`
- `POST /api/academics/enrollments`

## 5) Run tests

```powershell
pytest -q
```

## 6) Notes

- Authentication is JWT-based (Bearer token), not cookies.
- Auth/Users/Roles/Profiles use explicit SQLAlchemy models.
- Existing automap support is still available for modules not migrated yet.
- Seeded admin from MVC startup uses password `Admin@123`.
