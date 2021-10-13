from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, Any

from .helper import PyObjectId

import re

class TorrentClient:
    def __init__(self, **kwargs):
        self.record = _TorrentClient(**kwargs)
        self.peer_id_regex = re.compile(self.record.peer_id_pattern)
        self.agent_regex = re.compile(self.record.agent_pattern)
    
    def __eq__(self, agent: str) -> bool:
        agent = self.agent_regex.match(agent)
        if agent:
            return True
        else:
            return False

class _TorrentClient(BaseModel):
    # id: Optional[PyObjectId] = Field(alias='_id')
    _id: ObjectId
    family: str
    start_name: str
    peer_id_pattern: str
    peer_id_match_num: int
    peer_id_matchtype: str
    peer_id_start: str
    agent_pattern: str
    agent_match_num: int
    agent_matchtype: str
    agent_start: str
    exception: str
    allowhttps: str
    comment: str
    hits: int

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.peer_id_pattern[0] == '/' and self.peer_id_pattern[-1] == '/':
            self.peer_id_pattern = self.peer_id_pattern[1: -1]
        if self.agent_pattern[0] == '/' and self.agent_pattern[-1] == '/':
            self.agent_pattern = self.agent_pattern[1:-1]