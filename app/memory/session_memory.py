from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class SessionMemory:
    messages: List[ChatMessage] = field(default_factory=list)

    def append(self, role: str, content: str) -> None:
        self.messages.append(ChatMessage(role=role, content=content))
    
    def get_conversation_history(self) -> List[tuple[str, str]]:
        """Get conversation history as a list of (role, content) tuples."""
        return [(msg.role, msg.content) for msg in self.messages]


class SessionMemoryStore:
    def __init__(self) -> None:
        self._store: Dict[str, SessionMemory] = {}

    def ensure_session(self, session_id: str) -> SessionMemory:
        if session_id not in self._store:
            self._store[session_id] = SessionMemory()
        return self._store[session_id]

    def get(self, session_id: str) -> SessionMemory:
        return self.ensure_session(session_id)


