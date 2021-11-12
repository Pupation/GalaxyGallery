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

from .collection import collection_router

router.include_router(collection_router)