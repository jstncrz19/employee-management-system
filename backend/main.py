from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.employees import router as employee_router
from app.routers.attendance import router as attendance_router
from app.routers.leaves import router as leaves_router
from app.routers.dashboard import router as dashboard_router
from app.routers.audit import router as audit_router

app = FastAPI(
    title="Employee Leave & Attendance Management System API",
    description=(
        "Backend API for the Employee Leave & Attendance Management System. "
        "It covers JWT authentication with admin and employee roles, an "
        "employee directory, daily check-in/check-out tracking, leave requests "
        "with approval workflows and leave balance accounting, employee and "
        "admin dashboards, and an audit trail of significant actions.\n\n"
        "Interactive clients:\n"
        "- Swagger UI: `/docs`\n"
        "- ReDoc: `/redoc`\n\n"
        "Protected endpoints require a JWT bearer token obtained from "
        "`POST /auth/login` (OAuth2 password flow, `username` = email). "
        "Use the Authorize button in the interactive docs to send it. "
        "Unauthenticated requests return `401`; authenticated users calling "
        "endpoints outside their role return `403`."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(employee_router)
app.include_router(attendance_router)
app.include_router(leaves_router)
app.include_router(dashboard_router)
app.include_router(audit_router)

@app.get("/")
def root():
    return {"message": "Employee Management System API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
