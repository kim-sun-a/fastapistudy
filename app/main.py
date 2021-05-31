from dataclasses import asdict
from typing import Optional

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX
from app.database.conn import db
from app.common.config import conf
from app.middelwares.token_validator import AccessControl
from app.middelwares.trusted_hosts import TrustedHostMiddleWare
from app.router import index, auth, user

API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)


def create_app():
    """
    앱 함수 실행
    :return:
    """
    c = conf()
    app = FastAPI()
    conf_dict = asdict(c)
    db.init_app(app, **conf_dict)

    # 데이터베이스 이니셜라이즈

    # 레디스 이니셜라이즈

    # 미들웨어 정의
    app.add_middleware(AccessControl, except_path_list=EXCEPT_PATH_LIST, except_path_regex=EXCEPT_PATH_REGEX)
    app.add_middleware(             # 이게 없으면 프론트 주소와 백엔드 주소가 다르면 접근 불가능
        CORSMiddleware,             # 특정 호스트로 접근할 수 있는 미들웨어
        allow_origins=conf().ALLOW_SITE,
        allow_credentials=True,
        allow_methods=["*"],                    # 하지만 개발 중이기에 모든 호스트에서 접근 가능
        allow_headers=["*"]
    )
    app.add_middleware(TrustedHostMiddleWare, allowed_hosts=conf().TRUSTED_HOSTS, except_path=["/health"])
    # 요청이 들어오면 제일 밑에 미들웨어부터 시작

    # 라우터 정의
    app.include_router(index.router)
    app.include_router(auth.router, tags=["Authentication"], prefix="/api")
    app.include_router(user.router, tags=["Users"], prefix="/api", dependencies=[Depends(API_KEY_HEADER)])

    return app


app = create_app()

# 실행되는 파일이 이 파일일 경우
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)