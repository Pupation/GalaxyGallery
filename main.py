from fastapi import FastAPI

gg = FastAPI()

from models.config import Config

from fastapi.logger import logger
import logging

gunicorn_logger = logging.getLogger('uvicorn')
logger.handlers = gunicorn_logger.handlers

config = Config('config.yml')

from core import *