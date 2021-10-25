from fastapi import Depends
from sqlalchemy.orm import Session

from asyncio import sleep
from main import gg, config
from datetime import timedelta
from utils.connection.sql.db import get_sqldb
from models.user.user import User

async def accountingService(uid:int, tid:int, 
        uploaded:int, downloaded: int,
        time_delta: timedelta,
        seeder: bool):
    db: Session
    for db in get_sqldb():
        user = db.query(User).get({'id': uid})
        user.downloaded = User.downloaded + downloaded
        user.uploaded = User.uploaded + uploaded
        if seeder:
            user.seedtime = User.seedtime + int(time_delta.total_seconds())
        else:
            user.leechtime = User.leechtime + int(time_delta.total_seconds())
        db.commit()
        print(uploaded, downloaded, time_delta)
    # print("this is accounting service at background")