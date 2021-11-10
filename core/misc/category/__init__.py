from fastapi import APIRouter


category_router = APIRouter(
    prefix='/api/category',
    tags=['category']
)

from .category import *