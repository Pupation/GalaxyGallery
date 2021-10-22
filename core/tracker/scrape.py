from fastapi import Header, Request
from datetime import timedelta

from main import gg
from utils.response import BencResponse
from utils.checker.passkey_checker import check_passkey
from models.torrent import get_peer_count

@gg.get('/scrape')
async def scrape(
    request:Request,
    info_hash: bytes,
    passkey: str
):
    check_passkey_coroutine = check_passkey(passkey)
    rep_dict = {
        "files": get_peer_count(info_hash)
    }
    if (await check_passkey_coroutine) is not None:
        return BencResponse(rep_dict)
    else:
        return BencResponse({'message': 'Passkey invalid.'}, 403)
