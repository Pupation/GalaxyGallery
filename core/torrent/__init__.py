from fastapi import APIRouter


router = APIRouter(
    prefix='/api/torrent'
)

from .torrent import *
from .create import *