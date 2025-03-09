import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel

TG_STORAGE_DIR: Path = Path.home() / ".tg-storage"
TG_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH: Path = TG_STORAGE_DIR / "tg_storage.json"
SESSION_FILE: Path = TG_STORAGE_DIR / ".tg_storage"
GLOBAL_METAFILE: Path = TG_STORAGE_DIR / "tg_storage_global.json"


class Config(BaseModel):
    storage_chat_id: int
    metadata_message_id: int
    session_file: Path = SESSION_FILE
    global_metafile: Path = GLOBAL_METAFILE
    chat_verified: bool = False

    class Config:
        validate_assignment = True

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self.save()

    def to_dict(self, **kwargs):
        data = super().dict(**kwargs)
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        return data

    def save(self, path: Path = CONFIG_PATH) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> Self:
        try:
            if path.exists() and path.stat().st_size > 0:
                with open(path, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if key in ["session_file", "global_metafile"]:
                            data[key] = Path(value)
                    return cls(**data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {path}: {e}")

        return cls(
            storage_chat_id=0,
            metadata_message_id=0,
        )
