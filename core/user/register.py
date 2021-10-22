from fastapi import Request, Response, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from urllib.parse import quote_plus

from . import router
from models.user.user import *
from models.user.role import Role, URMap
from models.helper import GeneralException
from utils.provider import send_mail
from utils.connection.sql.db import get_sqldb

from .utils import validate_password, validate_username

def check_exists(db, username, email):
    user = db.query(User).filter((User.username == username) | (User.email == email)).count()
    return user > 0

@router.post('/register/')
async def register(request: Request, response: Response,bg: BackgroundTasks, db:Session = Depends(get_sqldb)):
    try:
        try:
            form = await request.json()
        except:
            raise GeneralException('Form not complete.', 400)
        try:
            username = form.get('username')
            password = form.get('password')
            email = form.get('email')
            school = form.get('school', 0)
            country = form.get('country', 0)
            invitation_code = form.get('invitation_code', '')
        except KeyError:
            raise GeneralException('Form not complete.', 400)
        if check_exists(db, username, email):
            raise GeneralException('Username or email already exists.', 409)
        if not validate_password(password):
            raise GeneralException('Password not valid.', 400)
        if not validate_username(username):
            raise GeneralException('Username not valid.', 400)
        secret = User.gen_secret()
        passhash = User.get_passhash(secret, password)
    except GeneralException as ge:
        response.status_code = ge.retcode
        return {'error': ge.retcode, 'detail': ge.message}

        
    

    user = User(
            username=username, 
            passhash=passhash,
            email=email,
            editsecret=User.gen_secret(),
            secret=secret
        )
    bg.add_task(send_mail, user.email, 'registration email', f'click this link to confirm your account http://{request.headers["host"]}/api/confirm?code={quote_plus(user.editsecret)}')
    # send_mail(user.email, 'registration email', f'click this link to confirm your account {request.headers["host"]}/api/confirm/{user.editsecret}')
    user.set_passkey(True)
    user.add_role(db, 'unconfirmed')
    db.add(user)
    db.commit()
    # db.refresh(user)
    # db.refresh(user)
    return {'ok': 1}

@router.get('/confirm')
async def confirm(
    code:str,
    response: Response,
    db: Session = Depends(get_sqldb)
):
    try:
        user = db.query(User).filter((User.editsecret == code) & (User.status == UserStatus.pending) ).one()
    except:
        response.status_code = 404
        return {'error': 404, 'detail': 'User not found.'}
    try:
        user.status = UserStatus.confirmed
        user.editsecret = b''
        user.remove_role(db, 'unconfirmed')
        user.add_role(db, 'newbie')
        db.add(user)
        db.commit()
        return {'ok': 1}
    except:
        response.status_code = 500
        return {'error': 500, 'detail': 'Internal error, failed to update database.'}
