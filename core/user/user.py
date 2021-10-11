from main import gg

from fastapi.responses import HTMLResponse


@gg.get('/login')
async def login():
    return HTMLResponse("<input name='username'/> <input name='password' type='password'/> <input type='submit'/>")