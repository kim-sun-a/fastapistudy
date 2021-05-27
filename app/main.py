from dataclasses import asdict
from typing import Optional

import uvicorn
from fastapi import FastAPI
from app.database.conn import db
from app.common.config import conf
from app.router import index


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

    # 라우터 정의
    app.include_router(index.router)

    return app


app = create_app()

# 실행되는 파일이 이 파일일 경우
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)