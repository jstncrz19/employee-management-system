from fastapi import FastAPI

app = FastAPI(
    title="Employee Leave & Attendance Management System",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message": "Employee Management System API",
        "version": "0.1.0",
    }