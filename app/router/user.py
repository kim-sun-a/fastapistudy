from typing import List
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request
from fastapi.logger import logger

from app.common.consts import MAX_API_KEY
from app.database.conn import db
from app.database.schema import Users, ApiKeys, ApiWhiteLists
from app import model as m
from app.error import exceptions as ex
import string
import secrets

from app.model import MessageOk

router = APIRouter(prefix="/user")


@router.get("/me")
async def get_me(request: Request):
    """
    get my info
    :param request:
    :return:
    """
    user = request.state.user
    user_info = Users.get(id=user.id)
    # user_info = Users.filter(id__gt=user.id).order_by("email").all() -> list / first -> 1개 / count -> 개수
    # 가볍게 한번만 부르는 것은 세션을 굳이 부를 필요가 있나?
    # user_info = session.query(Users).filter(Users.id > user.id).order_by(Users.email.asc()).count() -> sqlalchemy
    # 위 코드와 아래 코드는 같은 것
    return user_info


@router.put('/me')
async def put_me(request: Request):
    ...


@router.delete('/me')
async def delete_me(request: Request):
    ...


@router.get('/apikeys', response_model=List[m.GetApiKeyList])
async def get_api_keys(request: Request):
    """
    api key  조회
    :param request:
    :return:
    """
    user = request.state.user
    api_keys = ApiKeys.filter(user_id=user.id).all()
    return api_keys


@router.post('/apikeys', response_model=m.GetApiKeys)
async def create_api_keys(request: Request, key_info: m.AddApiKey, session: Session = Depends(db.session)):
    """
    api key 생성
    :param request:
    :param key_info:
    :param session:
    :return:
    """
    user = request.state.user

    api_keys = ApiKeys.filter(session, user_id=user.id, status='active').count()
    if api_keys == MAX_API_KEY:
        raise ex.MaxKeyCountEx()

    alphabet = string.ascii_letters + string.digits
    s_key = ''.join(secrets.choice(alphabet) for i in range(40))        # 랜덤 키 만들기
    uid = None
    while not uid:
        uid_candidate = f"{str(uuid4())[:-12]}{str(uuid4())}"       # 유효아이디 뒤에 12자리 끊어서 연결
        uid_check = ApiKeys.get(access_key=uid_candidate)           # 만든 키가 유니크한지 검사하는 작업
        if not uid_check:
            uid = uid_candidate

    key_info = key_info.dict()

    new_key = ApiKeys.create(session, auto_commit=True, secret_key=s_key, user_id=user.id, access_key=uid, **key_info)
    return new_key


@router.put('/apikeys/{key_id}')
async def update_api_keys(request: Request, key_id: int, key_info: m.AddApiKey):
    """
    API key user memo update
    :param request:
    :param key_id:
    :param key_info:
    :return:
    """
    user = request.state.user
    key_data = ApiKeys.filter(id=key_id)
    if key_data and key_data.first().user_id == user.id:        # 키가 존재하고 키를 등록한 아이디와 로그인한 아이디가 같다면
        key_data.update(auto_commit=True, **key_info.dict())
    raise ex.NoKeyMatchEx()


@router.delete('/apikeys/{key_id}')
async def delete_api_keys(request: Request, key_id: int, access_key: str):
    user = request.state.user
    await check_api_owner(user.id, key_id)
    search_by_key = ApiKeys.filter(access_key=access_key)
    if not search_by_key.first():
        raise ex.NoKeyMatchEx()
    search_by_key.delete(auto_commit=True)
    return MessageOk()


@router.get('/apikeys/{key_id}/whitelists', response_model=List[m.GetAPIWhiteLists])
async def get_api_keys(request: Request, key_id:int):
    user = request.state.user
    await check_api_owner(user.id, key_id)
    whitelists = ApiWhiteLists.filter(api_key_id=key_id).all()
    return whitelists


@router.post('/apikeys/{key_id}/whitelists', response_model=m.GetAPIWhiteLists)
async def create_api_keys(request: Request, key_id: int, ip: m.CreateAPIWhiteLists, session: Session=Depends(db.session)):
    user = request.state.user
    await check_api_owner(user.id, key_id)
    ip_dup = ApiWhiteLists.get(api_key_id=key_id, ip_addr=ip.ip_addr)
    if ip_dup:
        return ip_dup
    ip_reg = ApiWhiteLists.create(session=session, auto_commit=True, api_key_id=key_id, ip_addr=ip.ip_addr)
    return ip_reg


@router.delete('/apikeys/{key_id}/whitelists/{list_id}')
async def delete_api_keys(request: Request, key_id:int, list_id:int):
    user = request.state.user
    await check_api_owner(user.id, key_id)
    ApiWhiteLists.filter(id=list_id, api_key_id=key_id).delete()

    return MessageOk()


async def check_api_owner(user_id, key_id):                 # 사용할 키의 user id 와 접속한 user id가 같은지 확인하는 작업
    api_keys = ApiKeys.get(id=key_id, user_id=user_id)
    if not api_keys:
        raise ex.NoKeyMatchEx()

