from jose import JWTError, jwt
from main import config
from datetime import timedelta, datetime
from typing import Optional

from main import config
from .user import User, UserStatus, get_user_by_id

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token/")

def create_access_token(data:dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.site.default.expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.site.SECRET_KEY, algorithm=config.site.ALGORITHM)
    return encoded_jwt


async def current_user(token: User = Depends(oauth2_scheme)):
    try:
        bearer = jwt.decode(token, config.site.SECRET_KEY)
    except JWTError as e:
        raise HTTPException(401, 'Invalid Token')
    print(bearer)
    return get_user_by_id(bearer['uid'])

async def current_active_user(user: User = Depends(current_user)):
    if user.status != UserStatus.confirmed:
        raise HTTPException(402, 'User is not confirmed')
    return user