# core/models/chat.py
from dataclasses import dataclass

@dataclass
class Chat:
    id: str
    project_id: int
    title: str
    created_at: str
    last_used: str
