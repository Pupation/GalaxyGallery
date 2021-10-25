from fastapi import Depends
from sqlalchemy.orm import Session

from asyncio import sleep
from main import gg, config
from datetime import timedelta
from utils.connection.sql.db import get_sqldb
from models.user.user import User
from models.torrent.peer import Peer

async def accountingService(peer: Peer, next_allowance: timedelta):
    db: Session
    await peer.find_one
    
    if peer.peer.seeder:
        seeder = True
        contribute_ratio = 1
    elif peer.peer.paused: # partial seeding
        seeder = True
        contribute_ratio = 0.5 # FIXME: calculate contribute_ratio by left and torrent total size
    else:
        seeder = False

    downloaded, uploaded, time_delta = peer.commit(next_allowance=next_allowance, seeder=seeder)

    for db in get_sqldb():
        user = db.query(User).get({'id': peer.peer.userid})
        user.downloaded = User.downloaded + downloaded
        user.uploaded = User.uploaded + uploaded
        if seeder:
            user.seedtime = User.seedtime + int(time_delta.total_seconds()* contribute_ratio) 
        else:
            user.leechtime = User.leechtime + int(time_delta.total_seconds())
        db.commit()
    print(uploaded, downloaded, time_delta)
    # print("this is accounting service at background")