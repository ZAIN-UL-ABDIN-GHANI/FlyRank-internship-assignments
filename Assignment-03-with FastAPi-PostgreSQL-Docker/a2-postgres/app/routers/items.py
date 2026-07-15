from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_item_service
from app.models import Item, ItemCreate
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=Item, status_code=201)
async def create_item(payload: ItemCreate, service: ItemService = Depends(get_item_service)):
    return await service.create_item(payload)


@router.get("", response_model=List[Item])
async def list_items(service: ItemService = Depends(get_item_service)):
    return await service.list_items()


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int, service: ItemService = Depends(get_item_service)):
    item = await service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=Item)
async def update_item(item_id: int, payload: ItemCreate, service: ItemService = Depends(get_item_service)):
    item = await service.update_item(item_id, payload)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, service: ItemService = Depends(get_item_service)):
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
