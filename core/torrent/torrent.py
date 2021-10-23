from . import router

from fastapi import Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, RedirectResponse
from datetime import timedelta, datetime
import redis
import uuid
import pickle
from urllib.parse import quote_plus
from sqlalchemy.orm import Session

from models.torrent.torrent import TorrentSQL, CreateTorrentForm, TorrentStatus, TorrentNoSQL
from models.user.user import User, Permission
from models.user.auth import current_active_user
from utils.cache import redis_connection_pool, gg_cache
from utils.provider.torrent import Torrent
from utils.connection.sql.db import get_sqldb
from utils.connection.nosql.db import client as nosql_db
from main import config
from models.torrent import get_peer_count, get_torrent_list, get_torrent_detail

from pydantic import BaseModel
from typing import List, Optional

class TorrentListReturn(BaseModel):
    class TorrentBreifResponse(BaseModel):
        id: int
        name: str
        subname: str
        downloaded: int
        completed: int
        incomplete: int
        size: str
    data: List[TorrentBreifResponse]
    page: int
    total: int

@router.get('/torrent_list', response_model=TorrentListReturn)
async def torrent_list(request: Request,
                       page: int = 0,
                       keyword: str = None,
                       advanced: bool = False,
                       _: User = Depends(current_active_user)
                       ):
    return get_torrent_list(page)

class TorrentDetailResponse(BaseModel):
    info_hash: bytes
    desc: str
    detail: str
    filename: str

@router.get('/torrent_detail/{torrent_id}', response_model=TorrentDetailResponse)
async def torrent_detail(request: Request, torrent_id: int, _: User = Depends(current_active_user)):
    return get_torrent_detail(torrent_id)

@router.get("/download_torrent")
async def download_torrent(request: Request, torrent_id: int, user: User = Depends(current_active_user)):
    if not user.has_permission(Permission.DOWNLOAD_TORRENT):
        raise HTTPException(403, "You do not have permission to download torrent")
    t_mongo = get_torrent_detail(torrent_id, 1)
    torrent = Torrent(t_mongo['torrent'])
    torrent.set_announce(f"{config.site.domain[0]}/announce?passkey={user.passkey}")
    file_content = torrent.get_torrent()
    cache = redis.StrictRedis(connection_pool=redis_connection_pool)
    file_handler = str(uuid.uuid4())
    cache.set(file_handler, file_content, 30)
    return  f"http://{request.headers['Host']}/get_file?filename={t_mongo['filename']}&code={file_handler}&location=1"