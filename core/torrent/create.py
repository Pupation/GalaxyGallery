from . import router

from fastapi import Request, HTTPException, Depends, File, UploadFile
from datetime import timedelta, datetime
import aioredis as redis
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

from models.torrent.torrent import TorrentSQL, CreateTorrentForm, TorrentStatus, TorrentNoSQL, flush_page_cache
from models.user.user import User, Permission
from models.user.auth import current_active_user, user_with_permission
from utils.cache import redis_connection_pool
from utils.provider.torrent import Torrent
from utils.connection.sql.db import get_sqldb
from utils.connection.nosql.db import client as nosql_db
from pydantic import BaseModel
from main import config
from typing import Optional, List

def is_valid_uuid4(_uuid):
    try:
        _ = uuid.UUID(_uuid, version=4)
        return True
    except:
        return False


@router.post('/create_torrent')
async def create_torrent(request: Request,form: CreateTorrentForm, user: User = Depends(user_with_permission([Permission.UPLOAD, Permission.UPLOAD_TORRENT])), db: AsyncSession = Depends(get_sqldb)):
    cache: redis.StrictRedis = redis.StrictRedis(
        connection_pool=redis_connection_pool)
    if not is_valid_uuid4(form.file_id) or not await cache.exists(form.file_id):
        raise HTTPException(410, 'File not found')
    if is_valid_uuid4(form.nfo_id) and not await cache.exists(form.nfo_id):
        raise HTTPException(410, 'NFO File not found')

    torrent = Torrent(await cache.get(form.file_id))
    info_hash = torrent.get_info_hash()
    info_hash_plain = torrent.get_info_hash(True)

    sql = select(func.count()).where((TorrentSQL.info_hash_plain == info_hash_plain) | (TorrentSQL.info_hash == info_hash))
    if (await db.execute(sql)).first()[0] > 0:
        await cache.delete(form.file_id)
        raise HTTPException(409, 'Torrent already exists')

    form.name = form.name.replace('.torrent', '')
    torrent_sql = TorrentSQL(
        status=TorrentStatus.normal if user.has_permission(
            Permission.BYPASS_VOTE_TORRENT) else TorrentStatus.pending,
        info_hash = info_hash,
        anonymous = not not user.anonymous,
        owner_id = user.id,
        size = torrent.get_size(),
        numfiles = len(torrent.get_filelist()),
        name = form.name,
        subname = form.subname,
        category = form.category,
        rank_by = datetime.now(),
        info_hash_plain = info_hash_plain
    )
    torrent_nosql = TorrentNoSQL(
        desc = form.desc,
        info_hash = torrent_sql.info_hash,
        torrent = torrent.get_torrent(),
        detail = {},
        filename = f'{config.site.short}{form.name}.torrent'
    )
    obj = await nosql_db.torrents.insert_one(dict(torrent_nosql))
    torrent_sql.record_id = str(obj.inserted_id)
    db.add(torrent_sql)
    await db.commit()
    await db.refresh(torrent_sql)
    flush_page_cache()
    await cache.delete(form.file_id)
    return {'ok': 1, 'id': torrent_sql.id}

class UploadTorrentResponse(BaseModel):
    id: str
    name: str
    exp: datetime
    size: Optional[str]
    files: Optional[List[str]]
    info_hash: Optional[str]
    nfo: Optional[bool]

@router.post('/upload_file', responses={
    200: {'model': UploadTorrentResponse}
})
async def upload_torrent(request: Request, file: UploadFile = File(...), user: User = Depends(current_active_user)):
    file_content = file.read()
    if not user.has_permission(Permission.UPLOAD):
        raise HTTPException(403, 'You do not have permission to upload file')
    cache = redis.StrictRedis(connection_pool=redis_connection_pool)
    file_id = str(uuid.uuid4())
    # form = await request.form()
    # print(form['file'].read())
    # print(form['file'])
    try:
        filename = file.filename
    except:
        filename = 'N/A'
    try:
        if filename.endswith('.torrent'):
            torrent = Torrent(await file_content)
            await cache.set(file_id, torrent.get_torrent(), timedelta(hours=12))
            file_list = torrent.get_filelist()
            return {
                'id': file_id,
                'name': filename,
                'size': "%.2f %s" % torrent.get_size(True),
                'files': file_list,
                'exp': datetime.utcnow() + timedelta(hours=12),
                'info_hash': torrent.get_info_hash().hex(),
                'nfo': any([f.endswith('.nfo') for f in file_list])
            }
        else:
            await cache.set(file_id, await file_content, timedelta(hours=12))
            return {
                'id': file_id,
                'name': filename,
                'exp': datetime.utcnow() + timedelta(hours=12),
            }
    except:
        raise HTTPException(413, "Connection Aborted")