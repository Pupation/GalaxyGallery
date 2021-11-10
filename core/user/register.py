from fastapi import Request, Response, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from urllib.parse import quote_plus

from . import router
from models.user.user import *
from models.user.role import Role, URMap
from models.user.auth import current_user
from models.helper import GeneralException
from utils.provider import send_mail
from utils.connection.sql.db import get_sqldb

from models.forms import RegisterResponse, ErrorResponseForm, RegisterForm

from .utils import validate_password, validate_username

async def check_exists(db, username, email):
    sql = select(func.count(User.id)).where((User.username == username) | (User.email == email))
    print(str(sql))
    count = await db.scalar(sql)
    return count > 0

@router.post('/register/', 
    responses={
        200: {"model": RegisterResponse},
        409: {"model": ErrorResponseForm}
    })
async def register(request: Request, response: Response,bg: BackgroundTasks, form:RegisterForm , db:Session = Depends(get_sqldb)):
    try:
        if await check_exists(db, form.username, form.email):
            raise GeneralException('Username or email already exists.', 409)
        secret = User.gen_secret()
        passhash = User.get_passhash(secret, form.password)
    except GeneralException as ge:
        response.status_code = ge.retcode
        return {'error': ge.retcode, 'detail': ge.message}

    user = User(
            username=form.username, 
            passhash=passhash,
            email=form.email,
            editsecret=User.gen_secret(),
            secret=secret
        )
    bg.add_task(send_mail, user.email, 'registration email', f'click this link to confirm your account http://{request.headers["host"]}/api/confirm?code={quote_plus(user.editsecret)}')
    # send_mail(user.email, 'registration email', f'click this link to confirm your account {request.headers["host"]}/api/confirm/{user.editsecret}')
    await user.set_passkey(True)
    await user.add_role(db, 'unconfirmed')
    db.add(user)
    await db.commit()
    # db.refresh(user)
    # db.refresh(user)
    return {'ok': 1}

@router.get('/confirm')
async def confirm(
    code:str,
    response: Response,
    db: AsyncSession = Depends(get_sqldb)
):
    user: User
    try:
        sql = select(User).where((User.editsecret == code) & (User.status == UserStatus.pending))
        user, = (await db.execute(sql)).first()
        # user = db.query(User).filter((User.editsecret == code) & (User.status == UserStatus.pending) ).one()
    except:
        response.status_code = 404
        return {'error': 404, 'detail': 'User not found.'}
    try:
        user.status = UserStatus.confirmed
        user.editsecret = b''
        await user.remove_role(db, 'unconfirmed')
        await user.add_role(db, 'newbie')
        db.add(user)
        await db.commit()
        return {'ok': 1}
    except:
        response.status_code = 500
        return {'error': 500, 'detail': 'Internal error, failed to update database.'}

@router.get('/resend_email', responses = {
    200: {'model': ErrorResponseForm},
    403: {'model': ErrorResponseForm}
})
def resend_mail(backgroundTasks: BackgroundTasks,user: User = Depends(current_user)):
    if user.editsecret == '' or user.status == UserStatus.confirmed:
        raise HTTPException(403, 'You are not allowed to do this')
    else:
        backgroundTasks.add_task(send_mail, user.email, "Confirmation email", f'Your url is http://localhost:8000/confirm?code={quote_plus(user.editsecret)}')
        return {'error': 0, 'detail': 'success'}