from . import router

from fastapi import Request, HTTPException, Depends
from datetime import timedelta, datetime
import redis
import uuid
from sqlalchemy.orm import Session

from models.torrent.torrent import TorrentSQL, CreateTorrentForm, TorrentStatus, TorrentNoSQL
from models.user.user import User, Permission
from models.user.auth import current_active_user
from utils.cache import redis_connection_pool
from utils.provider.torrent import Torrent
from utils.connection.sql.db import get_sqldb
from utils.connection.nosql.db import client as nosql_db
from pydantic import BaseModel
from main import config
from typing import Optional

def is_valid_uuid4(_uuid):
    try:
        _ = uuid.UUID(_uuid, version=4)
        return True
    except:
        return False


@router.post('/create_torrent')
async def create_torrent(request: Request,form: CreateTorrentForm, user: User = Depends(current_active_user), db: Session = Depends(get_sqldb)):
    if not user.has_permission([Permission.UPLOAD, Permission.UPLOAD_TORRENT]):
        raise HTTPException(403, 'You do not have permission to upload file')

    cache: redis.StrictRedis = redis.StrictRedis(
        connection_pool=redis_connection_pool)
    if not is_valid_uuid4(form.file_id) or not cache.exists(form.file_id):
        raise HTTPException(410, 'File not found')
    if is_valid_uuid4(form.nfo_id) and not cache.exists(form.nfo_id):
        raise HTTPException(410, 'NFO File not found')

    torrent = Torrent(cache.get(form.file_id))
    info_hash = torrent.get_info_hash()
    cache.delete(form.file_id)
    if db.query(TorrentSQL).filter(TorrentSQL.info_hash == info_hash).count() > 0:
        raise HTTPException(409, 'Torrent already exists')
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
    )
    torrent_nosql = TorrentNoSQL(
        desc = form.desc,
        info_hash = torrent_sql.info_hash,
        torrent = torrent.get_torrent(),
        detail = {},
        filename = f'{config.site.short}{form.name}.torrent'
    )
    obj = nosql_db.torrents.insert_one(dict(torrent_nosql))
    print(obj.inserted_id)
    torrent_sql.record_id = obj.inserted_id
    db.add(torrent_sql)
    db.commit()
    db.refresh(torrent_sql)
    return {'ok': 1, 'id': torrent_sql.id}


@router.post('/upload_file')
async def upload_torrent(request: Request, user: User = Depends(current_active_user)):
    if not user.has_permission(Permission.UPLOAD):
        raise HTTPException(403, 'You do not have permission to upload file')
    cache = redis.StrictRedis(connection_pool=redis_connection_pool)
    file_id = str(uuid.uuid4())
    form = await request.form()
    # print(form['file'].read())
    # print(form['file'])
    try:
        filename = form.get('file').filename
    except:
        filename = 'N/A'
    file_content = await form.get('file').read()
    if filename.endswith('.torrent'):
        torrent = Torrent(file_content)
        cache.set(file_id, torrent.get_torrent(), timedelta(hours=12))
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
        cache.set(file_id, file_content, timedelta(hours=12))
        return {
            'id': file_id,
            'name': filename,
            'exp': datetime.utcnow() + timedelta(hours=12),
        }
