# core/models/project.py
from dataclasses import dataclass

@dataclass
class Project:
    id: int
    name: str
    created_at: str
