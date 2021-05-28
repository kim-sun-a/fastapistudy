from enum import Enum

from pydantic.main import BaseModel
from pydantic.networks import EmailStr


# pydantic이 validation(유효성 검사) 하는 모델
# json으로 들어오고 나가는 데이터를 basemodel로 객체화시켜 만드것것

# response model -> 응답 모델
class UserRegister(BaseModel):
    email: EmailStr = None
    pw: str = None


# incoming model
class SnsType(str, Enum):
    email: str = "email"
    facebook: str = "facebook"
    google: str = "google"
    kakao: str = "kakao"


# response model -> 들어올때
class Token(BaseModel):
    Authorization: str = None


# 토큰을 객체화
class UserToken(BaseModel):
    id: int
    pw: str = None
    email: str = None
    name: str = None
    phone_number: str = None
    sns_type: str = None

    class Config:
        orm_mode = True
