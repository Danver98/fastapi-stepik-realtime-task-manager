from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.services.task_service import TaskService
from app.utils.unitofwork import UnitOfWork, IUnitOfWork
from app.utils.websocket import ConnectionManager
from app.api import schemas
from app.core.security import get_current_user, get_current_user_websocket


async def get_task_service(uow: IUnitOfWork = Depends(UnitOfWork)) -> TaskService:
    return TaskService(uow)


tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_current_user)]
)

websocket_router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
    dependencies=[Depends(get_current_user_websocket)]
)

ws_manager = ConnectionManager()


@tasks_router.post("/create")
async def create_task(task: schemas.Task, service: TaskService = Depends(get_task_service)) -> schemas.Task:
    """Create task"""
    return await service.create(task)


@tasks_router.get("/read-all/{user_id}")
async def get_tasks(user_id: int, service: TaskService = Depends(get_task_service)) -> list[schemas.Task]:
    """Get all tasks"""
    return await service.get_all(user_id)


@tasks_router.get("/read/{id_}")
async def get_task(id_: int, service: TaskService = Depends(get_task_service)) -> schemas.Task:
    """Get task by id"""
    return await service.read(id_)


@tasks_router.put("/update")
async def update_task(task: schemas.Task, service: TaskService = Depends(get_task_service)) -> schemas.Task:
    """Update task"""
    old_task = await service.read(task.id)
    task = await service.update(task)
    # Probably old_task is expired
    if task.completed and not old_task.completed:
        # Notify all connected to /ws endpoint abous status changes
        await ws_manager.broadcast(f"Task #{task.id} called \"{task.name}\" is completed")
    return task


@tasks_router.delete("/delete/{id_}")
async def delete_task(id_: int, service: TaskService = Depends(get_task_service)):
    """Delete task"""
    return await service.delete(id_)


@websocket_router.websocket("/init/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int | None = 0):
    """WebSocket endpoint"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_personal_message(f"You wrote: {data}", websocket)
            await ws_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        await ws_manager.broadcast(f"Client #{client_id} left the chat")

