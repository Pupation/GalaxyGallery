from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta, datetime
from fastapi import Depends

from main import config
from utils.connection.sql.db import get_sqldb
from models.user.user import User
from models.torrent.peer import Peer
from models.torrent.user_peer_stat import UserPeerStat, UserSeedStatus, get_last_action
from models.torrent.torrent import TorrentSQL

async def accountingService(peer: Peer, next_allowance: timedelta, left: bool):
    db: AsyncSession
    await peer.find_one
    (downloaded, uploaded, time_delta), update_one = await peer.commit(next_allowance=next_allowance, seeder= left == 0)

    async for db in get_sqldb():
    # sql_update_user = update(User).where(User.id == db.peer.peer.userid)
        user = await db.get(User, {'id': peer.peer.userid})
        last_action = await get_last_action(peer.peer.torrent)

        if last_action - datetime.now() > timedelta(days=config.site.preference.reseed_threshold):
            # TODO: trigger evict cache and reseed bonus
            print("reseed bonus!")
            pass
        try:
            sql = select(UserPeerStat).where(UserPeerStat.uid==peer.peer.userid, UserPeerStat.tid==peer.peer.torrent)
            stat, = (await db.execute(sql)).first()
            # stat = db.query(UserPeerStat).filter_by(uid=peer.peer.userid, tid=peer.peer.torrent).one()
        except:
            stat = UserPeerStat(uid=peer.peer.userid, tid=peer.peer.torrent)
            sql = select(TorrentSQL.size).where(TorrentSQL.id == stat.tid)
            stat.torrent_size = await db.scalar(sql)
            db.add(stat)
            await db.commit()
            await db.refresh(stat)

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

        await db.commit()