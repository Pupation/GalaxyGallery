from models.torrent.peer import get_peer_count
from . import router

from fastapi import Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, RedirectResponse
from datetime import timedelta, datetime
import redis
import uuid

from models.forms.torrent import CreateTorrentForm
from models.user.user import User, Permission
from models.user.auth import current_active_user
from utils.cache import redis_connection_pool
from utils.provider.torrent import Torrent
from utils.connection.sql.db import get_sqldb
from utils.connection.nosql.db import client as nosql_db
from main import config
from models.torrent import get_torrent_list, get_torrent_detail
from .rank import query_keyword

from models.forms.torrent import TorrentListResponse, TorrentDetailResponse
from typing import List, Literal


@router.get('/torrent_list', response_model=TorrentListResponse)
async def torrent_list(request: Request,
                       page: int = 0,
                       keyword: str = None,
                       semi_search: bool = False,
                       advanced: bool = False,
                       version: Literal['v1', 'v2'] = 'v1',
                       _: User = Depends(current_active_user)
                       ):
    if not semi_search and page == 0 and keyword != '' and keyword is not None:
        await query_keyword(keyword)
    if version in ['v1', 'v2']:
        ret = await get_torrent_list(page, keyword, version)
    else:
        raise HTTPException(400, 'Invalid Version: %s' % version)
    return ret


@router.get('/torrent_detail/{torrent_id}', response_model=TorrentDetailResponse)
async def torrent_detail(request: Request, torrent_id: int, _: User = Depends(current_active_user)):
    ret = await get_torrent_detail(torrent_id, 0)
    ret['info_hash'] = ret['info_hash'].hex()
    return ret

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