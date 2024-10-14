from sqlalchemy import select
from app.db.models import Task
from app.repositories.base_repository import Repository


class TasksRepository(Repository):
    """
        Task repository
    """
    model = Task

    async def get_all(self, user_id) -> list[Task]:
        """Get user tasks"""
        tasks = await self.session.execute(select(Task).where(Task.user_id == user_id))
        return tasks.scalars().all()
