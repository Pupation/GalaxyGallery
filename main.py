from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware


gg = FastAPI()

from models.config import Config

import logging

gunicorn_logger = logging.getLogger('uvicorn.access')
logger.handlers = gunicorn_logger.handlers

config = Config('config.yml')

from core import *
gg.include_router(user_router)
gg.include_router(torrent_router)
gg.include_router(chatbox_router)

gg.add_middleware(
    CORSMiddleware,
    allow_origins=config.site.domain,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@gg.on_event('shutdown')
async def stop(self):
    print('---------try killing')
    # client = redis.StrictRedis(connection_pool=redis_connection_pool)
    # client.publish(NAME_MESSAGE_QUEUE, 'KILL')