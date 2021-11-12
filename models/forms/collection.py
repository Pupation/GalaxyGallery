from pydantic import BaseModel, validator

from typing import Optional, List

from models.torrent.collection import CollectionSource, CategoryPublished

from core.misc.category import CATEGORIES

class CollectionForm(BaseModel):
    name: str
    subname: str
    source: CollectionSource
    published: CategoryPublished
    desc: str
    tags: List[str]
    category: int

    @validator('category')
    def category_exsit(cls, v):
        def _search(cid, category):
            for c in category.subcategory:
                if c.cid == cid or _search(cid, c):
                    return True
            return False
        for c in CATEGORIES:
            if c.cid == v or _search(v, c):
                return v
        raise ValueError('Category does not exist')