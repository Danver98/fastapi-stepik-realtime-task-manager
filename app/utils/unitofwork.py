from abc import ABC, abstractmethod

from app.db.database import async_session_maker
from app.repositories.base_repository import Repository
from app.repositories.task_repository import TasksRepository


class IUnitOfWork(ABC):
    """Interface for Unit of Work"""
    task: Repository

    @abstractmethod
    def __init__(self):
        ...

    @abstractmethod
    async def __aenter__(self):
        ...

    @abstractmethod
    async def __aexit__(self, *args):
        ...

    @abstractmethod
    async def commit(self):
        ...

    @abstractmethod
    async def rollback(self):
        ...


class UnitOfWork(IUnitOfWork):
    """Unit of Work implementation"""
    def __init__(self):
        self.session_factory = async_session_maker
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()

        self.task = TasksRepository(self.session)

    async def __aexit__(self, *args):
        await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()