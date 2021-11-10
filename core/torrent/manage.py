from . import router
from models.torrent.torrent import TorrentSQL, TorrentStatus, TorrentNoSQL, flush_page_cache
from utils.connection.sql.db import get_sqldb

from models.forms import UpdateTorrentForm

@router.put('/torrent_detail/{torrent_id}')
def update_torrent(form: UpdateTorrentForm):
    
    return 0