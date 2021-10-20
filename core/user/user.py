from datetime import timedelta
EXPIRATION = [
    timedelta(minutes=15),
    timedelta(minutes=60),
    timedelta(days=1),
    timedelta(days=7),
    timedelta(days=30),
    timedelta(days=365)
]
from . import router

from fastapi import Header, Depends, Request, Response
from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session

from utils.connection.sql.db import get_sqldb
from models.user.user import *
from models.user.auth import create_access_token, current_active_user

@router.get('/login')
async def login():
    return HTMLResponse("<input name='username'/> <input name='password' type='password'/> <input type='submit'/>")

@router.post('/token/')
async def token(
    request: Request,
    response: Response,
    db: Session = Depends(get_sqldb)
):
    try:
        form = await request.json()
        user = User.login(db, form['username'], form['password'])
        expires = form.get('expires', None)
        if expires is not None:
            expires = EXPIRATION[expires]
    except GeneralException as ge:
        response.status_code = ge.retcode
        return {'detail': ge.message}
    except:
        response.status_code = 400
        return {'detail': 'Bad request'}
    
    access_token = create_access_token(
        {
            "name": user.username,
            "uid": user.id
        },
        expires_delta = expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get('/create_all') # FIXME: temora implementation for initialize the database
async def create_db():
    from models import create_all
    create_all()

@router.get('/profile/{userid}')
def get_profile(userid, user:User = Depends(current_active_user)):
    return userid, 'hello', user.username