from datetime import datetime
from . import collection_router

from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.user.auth import current_active_user
from models.user.role import Permission
from models.user.user import User
from models.torrent.collection import CollectionSource, Collection, CollectionItems
from models.torrent.torrent import TorrentSQL, TorrentStatus

from utils.connection.sql.db import get_sqldb


@collection_router.get('/{cid:int}/add/{tid:int}')
async def add_to_collection(cid: int, tid: int, desc: str, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_sqldb)):
    if cid != user.id:
        sql = select(Collection).where(Collection.id == cid)
        coll: Collection = (await db.execute(sql)).unique().one_or_none()
        if coll is None:
            raise HTTPException(
                404, "Collection does not exist or not visible")
        coll, = coll

        if coll.source == CollectionSource.official or \
                coll.source == CollectionSource.group or \
                coll.owner_id != user.id:
            if not user.has_permission(Permission.MANAGE_COLLECTION):
                raise HTTPException(
                    403, "You do not have permission to edit this collection")
    sql = select(TorrentSQL).where((TorrentSQL.id == tid) &
                                   (TorrentSQL.status == TorrentStatus.normal))
    if (await db.execute(sql)).one_or_none() is None:
        raise HTTPException(404, "Torrent does not exist or not visible")
    sql = select(CollectionItems).where(
        (CollectionItems.tid == tid) & (CollectionItems.cid == cid))
    ci:CollectionItems = (await db.execute(sql)).one_or_none()
    if ci is None:
        ci = CollectionItems(tid=tid, cid=cid, desc=desc)
    else:
        ci, = ci
        ci.added_time = datetime.now()
        ci.desc = desc
    db.add(ci)
    try:
        await db.commit()
        return {'ok': 1}
    except:
        raise HTTPException(400, 'Unable to proceed')
