import re
import time
import typing
import jwt

from fastapi.params import Header
from jwt.exceptions import ExpiredSignatureError, DecodeError
from pydantic import BaseModel

from starlette.requests import Request
from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse, Response

from app.common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX
from app.error import exceptions as ex
from starlette.types import ASGIApp, Receive, Scope, Send

from app.common import config, consts
from app.common.config import conf
from app.error.exceptions import APIException
from app.model import UserToken

from app.utils.date_utils import D
from app.utils.logger import api_logger


async def access_control(request: Request, call_next):
    request.state.req_time = D.datetime()
    request.state.start = time.time()
    request.state.inspect = None
    request.state.user = None
    ip = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else request.client.host  # 사용자 아이피 확인
    request.state.ip = ip.split(",")[0] if "," in ip else ip
    headers = request.headers
    cookies = request.cookies
    url = request.url.path

    if await url_pattern_check(url, EXCEPT_PATH_REGEX) or url in EXCEPT_PATH_LIST:  # 미리 정의한 url에 url이 있다면 토큰 검사를 하지 않고 call_next
        response = await call_next(request)     # call_next => 다음 함수나 다음 미들웨어 호출해라
        if url != "/":   # 들어온 url이 root패스가 아니면 로그를 찍어라
            await api_logger(request=request, response=response)
        return response

    try:
        if url.startswith("/api"):
            # api인 경우 헤더로 토큰 검사
            if "authorization" in headers.keys():
                token_info = await token_decode(access_token=headers.get("Authorization"))
                request.state.user = UserToken(**token_info)
            else:
                # 토큰 없음
                if "Authorization" not in headers.keys():
                    raise ex.NotAuthorized()
        else:
            # 템플릿 렌더링 경우 쿠키에서 토큰 검사
            cookies["Authorization"] = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MTcsImVtYWlsIjoic3VuYUBuYXZlci5jb20iLCJuYW1lIjpudWxsLCJwaG9uZV9udW1iZXIiOm51bGwsInNuc190eXBlIjpudWxsfQ.3W6iKVzzz9jJojUVGJaMHZLYCKqVIsOcqejyXbqSOSE"

            if "Authorization" not in cookies.keys():
                raise ex.NotAuthorized()

            token_info = await token_decode(access_token=cookies.get("Authorization"))
            request.state.user = UserToken(**token_info)

        response = await call_next(request)         # 토큰 검사가 끝나면 call_next 함수 실행 (API)
        await api_logger(request=request, response=response)

    except Exception as e:
        error = await exception_handler(e)
        error_dict = dict(status=error.status_code, msg=error.msg, detail=error.detail, code=error.code)
        response = JSONResponse(status_code=error.status_code, content=error_dict)
        await api_logger(request=request, error=error)

    return response


async def url_pattern_check(path, pattern):
    result = re.match(pattern, path)
    if result:
        return True
    return False


async def token_decode(access_token):
    """
    :param access_token:
    :return:
    """
    try:
        access_token = access_token.replace("Bearer ", "")
        payload = jwt.decode(access_token, key=consts.JWT_SECRET, algorithms=[consts.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise ex.TokenExpiredEx()
    except DecodeError:
        raise ex.TokenDecodeEx()
    return payload


async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error
