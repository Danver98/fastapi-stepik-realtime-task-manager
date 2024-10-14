from abc import ABC, abstractmethod

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound


class AbstractRepository(ABC):
    @abstractmethod
    async def create(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    async def read(self, id_):
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id_):
        raise NotImplementedError
    

    @abstractmethod
    async def get_all(self, *args, **kwargs):
        raise NotImplementedError


class Repository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict):
        stmt = insert(self.model).values(**data).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def read(self, id_):
        stmt = select(self.model).where(self.model.id == id_)
        try:
            res = await self.session.execute(stmt)
            return res.scalar_one()
        except NoResultFound:
            return None

    async def update(self, data: dict):
        stmt = update(self.model).where(self.model.id == data['id']).values(**data).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def delete(self, id_):
        stmt = delete(self.model).where(self.model.id == id_).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def get_all(self,*args, **kwargs):
        result = await self.session.execute(select(self.model))
        return result.scalars().all()