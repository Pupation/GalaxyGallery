from fastapi import APIRouter


collection_router = APIRouter(
    prefix='/collection',
    tags=['collections']
)

from .manage import *
from .edit import *