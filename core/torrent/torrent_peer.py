from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from . import router

from models.user.user import User, get_user_by_id
from models.user.auth import user_with_permission, Permission
from models.torrent.user_peer_stat import UserPeerStat, UserPeerStatRecord, UserPeerStatResponse, UserPeerStatCountResponse, UserSeedStatus, get_count_peer_stat_count_by_tid 

from utils.connection.sql.db import get_sqldb

@router.get('/peer/count/{torrent_id}', response_model = UserPeerStatCountResponse)
async def get_peer_stat_count(torrent_id: int, _: User = Depends(user_with_permission(Permission.DOWNLOAD_TORRENT))):
    return get_count_peer_stat_count_by_tid(torrent_id)



@router.get('/peer/list/{torrent_id}', response_model=UserPeerStatResponse)
async def get_peer_stat_list(torrent_id: int, status: int, page: int = 0, _: User = Depends(user_with_permission(Permission.DOWNLOAD_TORRENT)), db: Session = Depends(get_sqldb)):
    ret = []
    print(db.query(UserPeerStat).filter(UserPeerStat.status == UserSeedStatus(status)).all())
    query = db.query(UserPeerStat).filter( (UserPeerStat.tid == torrent_id) &
                                          (UserPeerStat.status == UserSeedStatus(status)) &
                                          (UserPeerStat.last_action >= datetime.now() - timedelta(minutes=30)))
    total = query.count()
    for record in query.offset(page * 10).limit(10).all():
        record = dict(record.__dict__)
        record['status'] = record['status'].value
        user = get_user_by_id(record['uid'])
        if user.anonymous:
            record['username'] = 'Anonymous'
        else:
            record['username'] = user.username
        r = UserPeerStatRecord(**record)
        ret.append(r)
    return {"data": ret, 'total': total}
