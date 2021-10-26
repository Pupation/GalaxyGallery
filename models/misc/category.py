from __future__ import annotations
from pydantic import BaseModel
from bson import ObjectId
from typing import Optional, List

class Category(BaseModel):
    _id: Optional[ObjectId]
    cid: int
    name: str
    subcategory: Optional[List[Category]]
    template_id: int

Category.update_forward_refs()

class CategoryResponse(BaseModel):
    code: int
    data: Optional[List[Category]]
    detail: Optional[str]

class UpdateCategoryForm(BaseModel):
    cid: int
    name: Optional[str]
    parent: Optional[int]
    template_id: Optional[int]
