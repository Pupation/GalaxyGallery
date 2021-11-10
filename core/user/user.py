from datetime import timedelta

from pydantic.networks import EmailStr
EXPIRATION = [
    timedelta(minutes=15),
    timedelta(minutes=60),
    timedelta(days=1),
    timedelta(days=7),
    timedelta(days=30),
    timedelta(days=365)
]
from . import router

from fastapi import Depends, Request, Response, HTTPException
from fastapi.responses import HTMLResponse

from pydantic import BaseModel

from sqlalchemy.orm import Session
from typing import Optional

from utils.connection.sql.db import get_sqldb
from models.user.user import *
from models.user.auth import create_access_token, current_active_user, user_with_permission
from models.torrent.user_peer_stat import UserPeerStatCountResponse, get_count_peer_stat_count_by_uid

from .register import ErrorResponseForm

@router.get('/login')
async def login():
    return HTMLResponse("<input name='username'/> <input name='password' type='password'/> <input type='submit'/>")

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

@router.post('/token/', responses={
    200: {'model': LoginResponse},
    401: {'model': ErrorResponseForm},
    403: {'model': ErrorResponseForm},
    400: {'model': ErrorResponseForm},
})
async def token(
    request: Request,
    response: Response,
    form: LoginForm,
    db: Session = Depends(get_sqldb),
):
    try:
        user = await User.login(db, form.username, form.password)
        expires = form.expires
        if expires is not None:
            expires = EXPIRATION[expires]
    except GeneralException as ge:
        response.status_code = ge.retcode
        return {'error': ge.retcode, 'detail': ge.message}
    except:
        response.status_code = 400
        return {'error': 400,'detail': 'Bad request'}
    
    access_token = create_access_token(
        {
            "name": user.username,
            "uid": user.id
        },
        expires_delta = expires)
    ret = {"access_token": access_token, "token_type": "bearer", 
            "userid": user.id, "user": user.get_profile(True)}
    return ret

@router.get('/create_all') # FIXME: temora implementation for initialize the database
async def create_db():
    from models import create_all
    await create_all()


@router.get('/reset_passkey')
async def reset_passkey(user:User = Depends(current_active_user), db:AsyncSession = Depends(get_sqldb)):
    await user.set_passkey()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {'ok': 1}

@router.get('/profile/{userid}')
@router.get('/profile/')
async def get_profile(userid:Optional[int] = None, user:User = Depends(current_active_user)):
    if user.id == userid or userid == None:
        target_user = user
        bypass_privacy = True
    else:
        try:
            target_user = await get_user_by_id(userid)
        except:
            raise HTTPException(404, "User not found")
        bypass_privacy = False

    ret = target_user.get_profile(bypass_privacy)
    return ret

@router.get('/peer/count', response_model = UserPeerStatCountResponse)
async def get_peer_stat_count(user: User = Depends(user_with_permission(Permission.DOWNLOAD_TORRENT))):
    ret = await get_count_peer_stat_count_by_uid(user.id)
    return ret
