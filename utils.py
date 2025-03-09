import asyncio
import json


def run_coroutine(coroutine) -> None:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(coroutine)


def size_in_humanize(size: int) -> str:
    if size < 1024:
        return f"{size} bytes"
    if size < 1024**2:
        return f"{size / 1024:.2f} KB"
    if size < 1024**3:
        return f"{size / (1024**2):.2f} MB"
    return f"{size / (1024**3):.2f} GB"


class Json:
    @staticmethod
    def dumps(data: dict | list, indent: int = 4) -> str:
        return json.dumps(data, indent=indent)

    @staticmethod
    def loads(data: str) -> dict | list:
        return json.loads(data)
