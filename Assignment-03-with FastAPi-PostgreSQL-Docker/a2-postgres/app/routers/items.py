from typing import List

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from app.dependencies import get_item_service
from app.models import Task, TaskCreate, TaskUpdate
from app.services.item_service import ItemService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task, status_code=201)
async def create_item(payload: TaskCreate, service: ItemService = Depends(get_item_service)):
    return await service.create_item(payload)


@router.get("", response_model=List[Task])
async def list_items(service: ItemService = Depends(get_item_service)):
    return await service.list_items()


@router.get("/{task_id}", response_model=Task)
async def get_item(task_id: int, service: ItemService = Depends(get_item_service)):
    task = await service.get_item(task_id)
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task


@router.put("/{task_id}", response_model=Task)
async def update_item(task_id: int, payload: TaskUpdate, service: ItemService = Depends(get_item_service)):
    task = await service.update_item(task_id, payload)
    if task is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_item(task_id: int, service: ItemService = Depends(get_item_service)):
    deleted = await service.delete_item(task_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return Response(status_code=204)
