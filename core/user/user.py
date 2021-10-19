from . import router

from fastapi import Header
from fastapi.responses import HTMLResponse

@router.get('/login')
async def login():
    return HTMLResponse("<input name='username'/> <input name='password' type='password'/> <input type='submit'/>")

@router.post('/token/')
async def token(
    authentication:str = Header(None)
):
    print(authentication)
    return {
        'hello!'
    }