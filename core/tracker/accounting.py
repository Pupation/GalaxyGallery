from fastapi import Depends
from sqlalchemy.orm import Session

from asyncio import sleep
from main import gg, config
from datetime import timedelta
from utils.connection.sql.db import get_sqldb
from models.user.user import User
from models.torrent.peer import Peer
from models.torrent.user_peer_stat import UserPeerStat, UserSeedStatus
from models.torrent.torrent import TorrentSQL

async def accountingService(peer: Peer, next_allowance: timedelta, left: bool):
    db: Session
    await peer.find_one

    downloaded, uploaded, time_delta = peer.commit(next_allowance=next_allowance, seeder= left == 0)

    for db in get_sqldb():
        user = db.query(User).get({'id': peer.peer.userid})
        try:   
            stat = db.query(UserPeerStat).filter_by(uid=peer.peer.userid, tid=peer.peer.torrent).one()
        except:
            stat = UserPeerStat(uid=peer.peer.userid, tid=peer.peer.torrent)
            stat.torrent_size = db.query(TorrentSQL).filter_by(id=stat.tid).one().size
            db.add(stat)
            db.commit()
            db.refresh(stat)

        user.downloaded = User.downloaded + downloaded
        stat.downloaded = UserPeerStat.downloaded + downloaded

        user.uploaded = User.uploaded + uploaded
        stat.uploaded = UserPeerStat.uploaded + uploaded

        if left == 0: # Seeding
            seeding = True
            contribute_ratio = 1
            stat.status = UserSeedStatus.SEEDING

        elif peer.peer.paused: # partial seeding
            seeding = True
            contribute_ratio = 1 - left / stat.torrent_size # FIXME: calculate contribute_ratio by left and torrent total size
            stat.status = UserSeedStatus.PARTICAL_SEEDING

        else: # Downloading
            seeding = False
            stat.status = UserSeedStatus.DOWNLOADING
        
        if seeding:
            seedtime = int(time_delta.total_seconds()* contribute_ratio) 
            stat.seedtime = UserPeerStat.seedtime + seedtime
            user.seedtime = User.seedtime + seedtime
        else:
            leechtime = int(time_delta.total_seconds())
            stat.leechtime = UserPeerStat.leechtime + leechtime
            user.leechtime = User.leechtime + leechtime

        db.commit()
    print(uploaded, downloaded, time_delta)
    # print("this is accounting service at background")