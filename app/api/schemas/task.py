from pydantic import BaseModel, ConfigDict
from datetime import datetime
from .user import User

class Task(BaseModel):
    """Task model"""
    id: int | None = None
    name: str | None = None
    description: str | None = None
    user_id: int | None = None
    user: User | None = None
    completed: bool | None = False
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
