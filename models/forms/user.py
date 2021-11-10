from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import re

from models.user.user import UserGender

class RegisterForm(BaseModel):
    username: str
    password: str
    email: EmailStr
    school: Optional[int]
    country: Optional[int]
    invitation_code: Optional[str]

    @validator('password')
    def passwords_complex(cls, v):
        if not re.match("^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z]).+$", v):
            raise ValueError('Password must meet requirements')
        return v
    
    @validator('username')
    def verify_username(cls, v):
        if '!' in v:
            raise ValueError('Username must not contain "!"')
        return v

class RegisterResponse(BaseModel):
    ok: int = 1

class LoginForm(BaseModel):
    username: str
    password: str
    expires: Optional[int]

class LoginResponse(BaseModel):
    class UserResponse(BaseModel):
        class RoleResponse(BaseModel):
            name: str
            color: str
        username: str
        role: Optional[RoleResponse]
        uploaded: Optional[str]
        downloaded: Optional[str]
        seedtime: Optional[int]
        leechtime: Optional[int]
        gender: Optional[UserGender]
        email: Optional[EmailStr]
    access_token: str
    token_type: str = 'bearer'
    userid: int
    user: UserResponse