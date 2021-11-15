from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy.future import select
from datetime import datetime, timedelta

from . import router

from models.user.user import User, get_user_by_id
from models.user.auth import user_with_permission, Permission
from models.torrent.user_peer_stat import UserPeerStat, UserPeerStatRecord, UserPeerStatResponse, UserPeerStatCountResponse, UserSeedStatus, get_count_peer_stat_count_by_tid

from utils.connection.sql.db import get_sqldb


@router.get('/peer/count/{torrent_id:int}', response_model=UserPeerStatCountResponse)
async def get_peer_stat_count(torrent_id: int, _: User = Depends(user_with_permission(Permission.DOWNLOAD_TORRENT))):
    return await get_count_peer_stat_count_by_tid(torrent_id)


@router.get('/peer/list/{torrent_id:int}', response_model=UserPeerStatResponse)
async def get_peer_stat_list(torrent_id: int, status: UserSeedStatus, page: int = 0, _: User = Depends(user_with_permission(Permission.DOWNLOAD_TORRENT)), db: AsyncSession = Depends(get_sqldb)):
    result = []
    sql = select(UserPeerStat, User.anonymous, User.username).join(User, onclause=User.id == UserPeerStat.uid).where(
        (UserPeerStat.tid == torrent_id) &
        (UserPeerStat.status == UserSeedStatus(status)) &
        (UserPeerStat.last_action >=
         datetime.now() - timedelta(minutes=30))
    )
    print(sql)

    total = (await db.execute(sql.with_only_columns(func.count()))).scalar()
    ret = await db.execute(sql.offset(page * 10).limit(10))
    for record, anonymous, username in ret.all():
        record = dict(record.__dict__)
        record['status'] = record['status'].value
        user = get_user_by_id(record['uid'])
        if anonymous:
            record['username'] = 'Anonymous'
        else:
            record['username'] = username
        r = UserPeerStatRecord(**record)
        result.append(r)
    return {"data": result, 'total': total}
