from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

from app.database.conn import db
from app.database.schema import Users
from inspect import currentframe as frame

router = APIRouter()


@router.get("/")
async def index(session: Session = Depends(db.session)):
    """
    ELB 상태 체크용 API
    :param session:
    :return:
    """

    user = Users(status='active', name='HelloWorld')
    session.add(user)
    session.commit()

    Users().create(session, auto_commit=True, name='서나')

    current_time = datetime.utcnow()
    return Response(f"Test API (UTC : {current_time.strftime('%Y.%m.%d %H:%M:%S')})")


@router.get("/test")
async def test(request: Request):
    """
    ELB 상태 체크용 API
    :param request:
    :return:
    """
    print("state.user: ", request.state.user)
    try:
        a = 1/0
    except Exception as e:
        request.state.inspect = frame()     # 핸들링되지 않는 에러
        raise e

    current_time = datetime.utcnow()
    return Response(f"Test API (UTC : {current_time.strftime('%Y.%m.%d %H:%M:%S')})")
