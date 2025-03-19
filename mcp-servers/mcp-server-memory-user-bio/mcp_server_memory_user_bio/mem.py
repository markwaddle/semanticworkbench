import datetime
import pathlib

from pydantic import BaseModel, ValidationError

from .config import settings


class UserBioMemory(BaseModel):
    """
    A memory about the user.
    """

    date: datetime.date
    memory: str


class _SessionMemories(BaseModel):
    """
    The memories of a user session.
    """

    session_id: str
    memories: list[UserBioMemory]


def remember(session_id: str, user_timezone: datetime.tzinfo, memory: str) -> None:
    """
    Remember a memory about the user.
    """
    memories = _read_memories(session_id)
    bio_memory = UserBioMemory(
        date=datetime.datetime.now(user_timezone).date(),
        memory=memory,
    )
    memories.memories.append(bio_memory)
    _write_memories(memories)


def forget(session_id: str, memory: str) -> bool:
    """
    Forget a memory about the user.
    """
    memories = _read_memories(session_id)
    for bio_memory in memories.memories:
        if bio_memory.memory != memory:
            continue

        memories.memories.remove(bio_memory)
        _write_memories(memories)
        return True

    return False


def get_memories(session_id: str) -> list[UserBioMemory]:
    """
    Get all memories about the user.
    """
    memories = _read_memories(session_id)
    return sorted(memories.memories, key=lambda x: x.date)


def _read_memories(session_id: str) -> _SessionMemories:
    try:
        return _SessionMemories.model_validate_json(_filepath(session_id).read_text())
    except (FileNotFoundError, ValidationError):
        return _SessionMemories(session_id=session_id, memories=[])


def _write_memories(memories: _SessionMemories):
    _filepath(memories.session_id).write_text(memories.model_dump_json())


def _filepath(session_id: str) -> pathlib.Path:
    """
    Get the filepath for the session memories.
    """
    path = pathlib.Path(settings.storage_root) / f"memories-{session_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
