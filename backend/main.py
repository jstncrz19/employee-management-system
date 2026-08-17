from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.employees import router as employee_router
from app.routers.attendance import router as attendance_router

app = FastAPI(
    title="Employee Management System API"
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(employee_router)
app.include_router(attendance_router)

@app.get("/")
def root():
    return {"message": "Employee Management System API"}

