from io import BytesIO
from . import router

from fastapi import Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import timedelta, datetime
import redis
import uuid
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

@router.get('/torrent_list')
async def torrent_list(request: Request,
                       page: int = 0,
                       keyword: str = None,
                       advanced: bool = False,
                       _: User = Depends(current_active_user)
                       ):
    return get_torrent_list(page)


@router.get('/torrent_detail/{torrent_id}')
async def torrent_detail(request: Request, torrent_id: int, _: User = Depends(current_active_user)):
    return get_torrent_detail(torrent_id)

@router.get("/download_torrent")
async def download_torrent(request: Request, torrent_id: int, user: User = Depends(current_active_user)):
    t_mongo = get_torrent_detail(torrent_id, 1)
    torrent = Torrent(t_mongo['torrent'])
    torrent.set_announce(f"{config.site.domain[0]}/announce?passkey={user.passkey}")
    return StreamingResponse(BytesIO(torrent.get_torrent()), headers = {
        "Content-Disposition": "attachment; filename=.torrent; filename*=UTF-8''" + quote_plus(t_mongo['filename'], encoding="utf-8"),
    },)