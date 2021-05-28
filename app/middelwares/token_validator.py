import time
import typing
import jwt

from fastapi.params import Header
from jwt import PyJWTError
from pydantic import BaseModel

from starlette.requests import Request
from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.common import config, consts
from app.model import UserToken

from app.utils.date_utils import D


class AccessControl:
    def __init__(
            self,
            app: ASGIApp,
            except_path_list: typing.Sequence[str] = None,
            except_path_regex: str = None, ) -> None:
        if except_path_list is None:
            except_path_list = ["*"]
        self.app = app
        self.except_path_list = except_path_list
        self.except_path_regex = except_path_regex

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        print(self.except_path_regex)
        print(self.except_path_list)

        # 리퀘스트랑 헤더 가져오기
        request = Request(scope=scope)
        headers = Headers(scope=scope)

        # request.state.djsdjak = "dsda" -> 아무거나 입력 가능
        request.state.req_time = D.datetime()
        print(D.datetime())
        print(D.date())
        print(D.date_num())
        request.state.start = time.time()       # 로그 저장용
        request.state.inspect = None            # 500 에러 로깅용
        request.state.user = None               # 토큰 디코드 내용
        request.state.is_admin_access = None
        print(request.cookies)
        print(headers)
        res = await self.app(scope, receive, send)
        return res
