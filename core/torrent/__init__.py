from fastapi import APIRouter


router = APIRouter(
    prefix='/api/torrent',
    tags=['torrents']
)

from .torrent import *
from .create import *
from .torrent_peer import *
from .rank import *
from .manage import *
