from pydantic import BaseModel

class TopicRequest(BaseModel):
    topic: str
    schedule: str

class Task(BaseModel):
    id: int
    topic: str
    status: str
