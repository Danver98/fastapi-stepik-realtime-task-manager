import datetime
from enum import Enum

from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints


class UserLogin(BaseModel):
    login: Annotated[str, StringConstraints()]
    password: Annotated[str, StringConstraints()]

class UserRegister(UserLogin):
    name: Annotated[str, StringConstraints()]
    surname: Annotated[str, StringConstraints()]

class Role(Enum):
    ADMIN = 1
    USER = 2

class User(BaseModel):
    id: int | None = None
    login: str | None = None
    name: str | None = None
    surname: str | None = None
    roles: tuple[Role] | None = None

class UserFromDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
