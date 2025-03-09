"""File metadata management"""

import json
import mimetypes
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Self

from core.file_processor import calculate_checksum


@dataclass
class ChunkInfo:
    message_id: int
    name: str
    size: int
    index: int

    @classmethod
    def new(cls, message_id: int, file: Path, index: int):
        return cls(
            message_id=message_id,
            name=file.name,
            size=file.stat().st_size,
            index=index,
        )

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "name": self.name,
            "size": self.size,
            "index": self.index,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(**data)


@dataclass
class FileMetadata:
    original_name: str
    file_type: str
    extension: str
    checksum: str
    file_size: int
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunks: List[ChunkInfo] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def new(cls, file: Path) -> Self:
        file_type, _ = mimetypes.guess_type(file)
        file_type = file_type if file_type else "Unknown"
        return cls(
            original_name=file.name,
            file_type=file_type,
            extension=file.suffix,
            file_size=file.stat().st_size,
            checksum=calculate_checksum(file),
            created_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "original_name": self.original_name,
            "file_id": self.file_id,
            "file_type": self.file_type,
            "extension": self.extension,
            "checksum": self.checksum,
            "chunks": [c.to_dict() for c in self.chunks],
            "created_at": self.created_at,
            "file_size": self.file_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        chunks = [ChunkInfo.from_dict(chunk) for chunk in data["chunks"]]
        del data["chunks"]
        return cls(chunks=chunks, **data)

    @classmethod
    def get_metadatas(cls, file: Path) -> list[Self]:
        with file.open("r") as f:
            data = json.load(f)
        return [cls.from_dict(d) for d in data]

    @classmethod
    def push_metadatas(cls, metadatas: list[Self], path: Path):
        with path.open("w") as f:
            # if not metadatas:
            #     f.write("[]")
            json.dump([m.to_dict() for m in metadatas], f, indent=4)
