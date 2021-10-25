
from fastapi import APIRouter


chatbox_router = APIRouter(
    prefix='/chatbox'
)

from .chatbox import *
