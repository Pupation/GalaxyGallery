from fastapi import Depends, HTTPException

from . import category_router

from models import GeneralResponse
from models.user.user import User
from models.user.auth import current_active_user, user_with_permission
from models.user.role import Permission
from models.misc.category import CategoryResponse, Category, UpdateCategoryForm
from utils.connection.nosql.db import client as nosql_client, _client


CATEGORIES = []

def update_categories():
    global CATEGORIES
    CATEGORIES = []
    def _bfs_search(root, cid):
        for c in root.subcategory:
            if c.cid == cid:
                return c
    print("Updating category cache")
    for category in _client.categories.find({}).sort('cid', 1):
        data = dict(category)
        if 'parent' in data and data['parent'] is not None and data['parent'] != -1:
            found = False
            for c in CATEGORIES:
                if c.cid == data['parent']:
                    _c = Category(**data)
                    _c.subcategory = []
                    c.subcategory.append(_c)
                    found = True
                    break
                else:
                    sub = _bfs_search(c, data['parent'])
                    if sub is not None:
                        _c = Category(**data)
                        _c.subcategory = []
                        sub.subcategory.append(_c)
                        found = True
                        break
            if not found:
                c = Category(**data)
                c.subcategory = []
                CATEGORIES.append(c)
            
        else:
            c = Category(**data)
            c.subcategory = []
            CATEGORIES.append(c)


@category_router.get('/', response_model=CategoryResponse)
async def get_categories(_: User = Depends(current_active_user)):
    return {
        'data': CATEGORIES,
        'code': 200
    }

@category_router.post('/category', response_model=GeneralResponse)
async def add_category(payload: UpdateCategoryForm, _: User = Depends(user_with_permission(Permission.MANAGE_TORRENT)) ):
    if nosql_client.categories.find_one({'cid': payload.cid}) is not None:
        raise HTTPException(409, 'Category id already exist.')
    try:
        if payload.template_id == None:
            template_id = 0
        nosql_client.categories.insert_one(dict(payload))
    except:
        raise HTTPException(400, "Error creating categories.")
    update_categories()
    return {'ok': 1}

@category_router.put('/category', response_model=GeneralResponse)
async def update_category(payload: UpdateCategoryForm, _: User = Depends(user_with_permission(Permission.MANAGE_TORRENT))):
    payload = dict(payload)
    query = dict()
    for key in payload.keys():
        if payload[key] is not None:
            query[f"{key}"] = payload[key]

    nosql_client.categories.find_one_and_update(
        {'cid': payload['cid']},
        {'$set': query}
    )
    update_categories()
    return {'ok': 1}

@category_router.delete('/category', response_model=GeneralResponse)
async def delete_category(payload: UpdateCategoryForm, _: User = Depends(user_with_permission(Permission.MANAGE_TORRENT))):
    nosql_client.categories.find_one_and_delete(
        {'cid': payload.cid}
    )
    return {'ok': 1}

update_categories()