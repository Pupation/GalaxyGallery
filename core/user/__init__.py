from fastapi import APIRouter


router = APIRouter(
    prefix='/api',
    tags=['users']
)

from .user import *
from .register import *