from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.employees import router as employee_router
from app.routers.attendance import router as attendance_router
from app.routers.leaves import router as leaves_router
from app.routers.dashboard import router as dashboard_router
from app.routers.audit import router as audit_router

app = FastAPI(
    title="Employee Management System API",
    description=(
        "REST API for employee management, attendance, "
        "leave management, and audit logging."
    ),
    version="1.0.0",
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
