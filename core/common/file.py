import aioredis as redis
from typing import Optional
from fastapi.responses import StreamingResponse, PlainTextResponse
from urllib.parse import quote_plus

from main import gg

from utils.cache import redis_connection_pool
from io import BytesIO

@gg.get("/get_file")
async def get_file(location:int, code: str, filename:str = 'None'):
    if location == 1: # file in cache
        client = redis.StrictRedis(connection_pool=redis_connection_pool)
        content = await client.get(code)
        if content is None:
            return PlainTextResponse("Not found", 404)
        await client.delete(code)
        return StreamingResponse(BytesIO(content), 
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f"attachment; filename*=UTF-8''{quote_plus(filename)}"
            })
