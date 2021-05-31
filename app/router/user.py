from fastapi import APIRouter
from starlette.requests import Request

from app.database.schema import Users
from app.error.exceptions import NotFoundUserEx
from app.model import UserMe

router = APIRouter()


@router.get("/me", response_model=UserMe)
async def get_user(request: Request):
    """
    get my info
    :param request:
    :return:
    """
    user = request.state.user
    user_info = Users.get(id=user.id)
    raise NotFoundUserEx(user_info.email)
    return user_info
