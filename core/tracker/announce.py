from fastapi import Header, Request, HTTPException, BackgroundTasks
from datetime import timedelta
import asyncio
import re
from urllib.parse import unquote_to_bytes

from main import gg
from utils.response import BencResponse, ErrorResponse
from utils.checker import check_ip, check_ua_or_400, check_port_or_400, check_passkey
from models.helper import ErrorException, IP
from models.torrent import Peer, PeerList, get_peer_count
from models.torrent.torrent import get_torrent_id

from .accounting import accountingService


@gg.get('/announce')
async def announce(
    request: Request,
    backgroundTasks: BackgroundTasks,
    port: int, passkey: str, info_hash: bytes,
    peer_id: str, key: str, uploaded: int, downloaded: int, left: int,
    compact: int = 0, no_peer_id: int = 0,
    event: str = '',
    supportcrypto: bool = False, requirecrypto: bool = False,
    ipv6: str = None
):
    del info_hash  # fastapi did some silly converting here, thus we delete it and parse it by ourseleves
    # From BEP-21: In order to tell the tracker that a peer is a partial seed,
    # it MUST send an `event=paused` parameter in every announce while it is a partial seed.
    if event not in ['started', 'completed', 'stopped', 'paused', '']:
        return ErrorResponse('Unknown event.')
    ip = IP(request.client.host, ipv6)  # FIXME: get ip
    # FIXME: BEAWARE DoS! Blocked ip address still able to consume server computation resource
    info_hash = re.findall('info_hash=([^&]*)', str(request.url))[0]
    info_hash = unquote_to_bytes(info_hash)
    try:
        coroutine_checkip = check_ip(ip)                # redis cache
        coroutine_checkpasskey = check_passkey(passkey) # redis cache
        # torrent_client = check_ua_or_400(request)       # python local cache
        torrent_id = get_torrent_id(info_hash)          # redis cache
        check_port_or_400(port)
        blocked_ip, userid, torrent_client, torrent_id = await asyncio.gather(coroutine_checkip, coroutine_checkpasskey, check_ua_or_400(request), torrent_id)
        if blocked_ip:
            raise ErrorException('Blocked IP.', 400)
        if userid == -1:
            raise ErrorException('Passkey Invalid.', 401)
        elif userid == -2:
            raise ErrorException('Permission Denied.', 403)
            
        seeder = left == 0
        peer = Peer(info_hash=info_hash,                # MongoDB query
                    peer_id=peer_id,
                    port=port,
                    uploaded=uploaded,
                    downloaded=downloaded,
                    event=event,
                    agent=torrent_client.get("family"),
                    seeder=seeder,
                    passkey=passkey,
                    userid=userid,
                    torrent=torrent_id,
                    key=key,
                    **ip.todict()
                    )
        peer_count = get_peer_count(info_hash)                   # async function
        peers = PeerList(seeder=(seeder or (event == 'paused')), # MongoDB query, async function
                         info_hash=info_hash,
                         requester_ip=ip,
                         compact=(compact == 1)
                         )
        peers, peer_count = await asyncio.gather(peers(), peer_count)
        rep_dict = {
            "interval": 60,  # TODO: dynamic calculate interval by
            "min interval":  10,
            # "peers", "peers6"
            ** peers,
            # "complete", "incomplete", "downloaders"
            ** peer_count       # redis cache
        }
        if event == 'stopped':
            reannounce_deadline = timedelta(seconds=0)
        else:
            reannounce_deadline = timedelta(seconds=rep_dict['interval'] + 300)
        # backgroundTasks.add_task(
            # accountingService, peer, reannounce_deadline, left)
        # await accountingService(peer, reannounce_deadline, left)
        task = asyncio.create_task(accountingService(peer, reannounce_deadline, left)) # potential memory leak?
        # backgroundTasks.add_task(
        #     cleanup_future, task
        # )

        return BencResponse(rep_dict)
    except ErrorException as e:
        return ErrorResponse(e.__repr__(), e.ret_code)
    except HTTPException as e:
        if "blocked_ip" not in locals():
            blocked_ip = await coroutine_checkip
        if "userid" not in locals():
            userid = await coroutine_checkpasskey
        if blocked_ip:
            return ErrorResponse('Blocked IP.', 401)
        if userid is None:
            return ErrorResponse('Passkey Invalid.', 401)
        return ErrorResponse('Torrent Not found', 404)
    # except:
    #     return ErrorResponse('Bad request',400)

# async def cleanup_future(task):
#     print('start waiting')
#     # while not task.done():
#     #     print('task is still running')
#     #     asyncio.sleep(0.1)
#     # await task
#     print('task finished')