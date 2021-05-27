from datetime import datetime, timedelta

import bcrypt
# pyjwt -> 제이슨 웹토큰을 파이썬에서 쓰는 것
import jwt
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session              # 타이핑을 하기 위해 가져온것
from starlette.responses import JSONResponse    # 스탈렛 안에 있는 json형태로 response

from app.common.consts import JWT_SECRET, JWT_ALGORITHM
from app.database.conn import db                # db 연결
from app.database.schema import Users
from app.model import SnsType, Token, UserToken, UserRegister

router = APIRouter(prefix="/auth")


# ASGI 제공
@router.post("/register/{sns_type}", status_code=201, response_model=Token)
async def register(sns_type: SnsType, reg_info: UserRegister, session: Session = Depends(db.session)):
    """
    `회원가입 API`\n
    :param sns_type:
    :param reg_info:
    :param session:
    :return:
    """
    if sns_type == SnsType.email:
        is_exist = await is_email_exist(reg_info.email)     # 같은 이메일이 있는지 확인
        if not reg_info.email or not reg_info.pw:               # reg_info = response 된 json 객체
            return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided"))
        if is_exist:
            return JSONResponse(status_code=400, content=dict(msg="Email_exist"))
        hash_pw = bcrypt.hashpw(reg_info.pw.encode("utf-8"), bcrypt.gensalt())         # bcrypt : 해시 함수 -> 패스워드 검증 gensalt -> 소금을 뿌린다...? 소금값에 따라 해쉬값이 달라짐
        new_user = Users.create(session, auto_commit=True, pw=hash_pw, email=reg_info.email)
        token = dict(Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing_agree'}),)}")
        return token
    return JSONResponse(status_code=400, content=dict(msg="NOT_SUPPORTED"))


async def is_email_exist(email: str):       # 이메일이 있는지 없는지 확인
    get_email = Users.get(email=email)
    if get_email:
        return True


def create_access_token(*, data: dict = None, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + timedelta(hours=expires_delta)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
