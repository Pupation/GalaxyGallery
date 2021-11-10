
from fastapi import APIRouter


chatbox_router = APIRouter(
    prefix='/chatbox',
    tags=['chat']
)

from .chatbox import *
