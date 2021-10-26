from fastapi import APIRouter


category_router = APIRouter(
    prefix='/api/category'
)

from .category import *