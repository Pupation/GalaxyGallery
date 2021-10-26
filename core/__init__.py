# import all routes here

from .tracker import *
from .user import router as user_router
from .torrent import router as torrent_router
from .common import *

from .misc import chatbox_router, category_router