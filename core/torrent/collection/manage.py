from . import collection_router

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.user.user import User
from models.user.auth import current_active_user
from models.user.role import Permission
from models.torrent.collection import CollectionItems, CollectionSource, Collection
from models.forms import CollectionForm

from utils.connection.sql.db import get_sqldb

@collection_router.post('/')
async def create_collection(form: CollectionForm, user: User = Depends(current_active_user), db: AsyncSession= Depends(get_sqldb)):
    owner_id = user.id
    if form.source == CollectionSource.official or form.source == CollectionSource.group:
        if not user.has_permission(Permission.MANAGE_COLLECTION):
            raise HTTPException(403, "You do not have permission to create an official collection")
        owner_id = 1
    coll = Collection(owner_id=owner_id,**form.dict())
    db.add(coll)
    await db.commit()
    await db.refresh(coll)
    return coll



@collection_router.get('/{cid:int}')
async def get_collection(cid:int, user: User = Depends(current_active_user)):
    pass

@collection_router.put('/{cid:int}')
async def update_collection(cid:int, user: User = Depends(current_active_user)):
    pass

@collection_router.delete('/{cid:int}')
async def delete_collection(cid:int, user: User = Depends(current_active_user), db: AsyncSession= Depends(get_sqldb)):
    cid = int(cid)
    sql = select(Collection.owner_id, Collection.source).where(Collection.id == cid)
    ret = (await db.execute(sql)).one_or_none()
    if ret is None:
        raise HTTPException(404, 'Not found')
    owner_id, source = ret
    if cid != user.id and (owner_id != user.id or source == CollectionSource.official or source == CollectionSource.group):
        if not user.has_permission(Permission.MANAGE_COLLECTION):
            raise HTTPException(403, "You do not have permission to create an official collection")
    sql = CollectionItems.__table__.delete().where(CollectionItems.cid == cid) 
    await db.execute(sql)
    sql = Collection.__table__.delete().where(Collection.id == cid)
    await db.execute(sql)
    await db.commit()
    return {'ok': 1}