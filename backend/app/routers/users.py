from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description=(
        "Returns the authenticated account (id, email, role). "
        "Requires a valid JWT bearer token."
    ),
    responses={
        401: {"description": "Missing or invalid token"}
    }
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user