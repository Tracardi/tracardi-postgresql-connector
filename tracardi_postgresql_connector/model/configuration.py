from pydantic import BaseModel
from tracardi.domain.entity import Entity


class Configuration(BaseModel):
    source: Entity
    query: str
    timeout: int = 20
