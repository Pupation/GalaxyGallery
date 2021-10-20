from fastapi import APIRouter


router = APIRouter(
    prefix='/api'
)

from .user import *
from .register import *