from fastapi import HTTPException, status
from app.api import schemas
from app.db import models
from app.api.endpoints.errors.models import CurrencyExchangeError
from app.utils.unitofwork import IUnitOfWork


class TaskService:
    """
        Service class for working with tasks
    """
    def __init__(self, uow: IUnitOfWork):

        self.uow = uow

    def _get_task_from_db_object(self, task: models.Task) -> schemas.Task:
        """ Get task from db object """
        return schemas.Task(
            id=task.id,
            name=task.name,
            description=task.description,
            user_id=task.user_id,
            completed=task.completed,
            created_at=task.created_at
        )

    async def create(self, task: schemas.Task) -> schemas.Task:
        """Create task"""
        db_task = task.model_dump(exclude_none=True)
        async with self.uow:
            db_task = await self.uow.task.create(db_task)
            task = self._get_task_from_db_object(db_task)
            await self.uow.commit()
            return task

    async def read(self, task_id: int) -> schemas.Task:
        """Get task by id"""
        async with self.uow:
            db_task = await self.uow.task.read(task_id)
            if db_task is None:
                raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
            task = self._get_task_from_db_object(db_task)
            return task

    async def update(self, task: schemas.Task) -> schemas.Task:
        """Update task"""
        db_task = task.model_dump(exclude_unset=True)
        async with self.uow:
            db_task = await self.uow.task.update(db_task)
            task = self._get_task_from_db_object(db_task)
            await self.uow.commit()
            return task

    async def get_all(self, user_id: int) -> list[schemas.Task]:
        """Get task by id"""
        async with self.uow:
            db_tasks = await self.uow.task.get_all(user_id)
            return [
                self._get_task_from_db_object(task)
                for task in db_tasks
            ]

    async def delete(self, task_id: int):
        """Delete task"""
        async with self.uow:
            await self.uow.task.delete(task_id)
            await self.uow.commit()
