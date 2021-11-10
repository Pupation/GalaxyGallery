from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class CreateTorrentForm(BaseModel):
    name: str
    subname: str
    file_id: str
    desc: str
    category: int
    assistant_id: Optional[str]
    imdb_link: Optional[str]
    nfo_id: str

class UploadTorrentResponse(BaseModel):
    id: str
    name: str
    exp: datetime
    size: Optional[str]
    files: Optional[List[str]]
    info_hash: Optional[str]
    nfo: Optional[bool]

class TorrentListResponse(BaseModel):
    class TorrentBreifResponse(BaseModel):
        id: int
        name: str
        subname: str
        downloaded: int
        complete: int
        incomplete: int
        size: tuple
        rank_by: datetime
    data: List[TorrentBreifResponse]
    page: int
    total: int

class TorrentDetailResponse(BaseModel):
    info_hash: str
    desc: str
    detail: Optional[dict]
    filename: str
