# core/models/message.py
from dataclasses import dataclass

@dataclass
class Message:
    id: int
    chat_id: str
    role: str
    content: str
    ts: str
