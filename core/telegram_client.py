from pathlib import Path

from pyrogram.client import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChannelPrivate
from pyrogram.types import Message
from rich.filesize import decimal
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.text import Text

from utils import run_coroutine

from .config_manager import Config


class CurrentTotalColumn(ProgressColumn):
    """Custom column to display current/total file size in human-readable form."""

    def render(self, task):
        current = decimal(task.completed)  # type: ignore
        total = decimal(task.total) if task.total else "?"  # type: ignore
        return Text(f"{current} / {total}", style="progress.data")


class TelegramManager:
    """Manages Telegram connection and permissions"""

    @staticmethod
    def create_session(api_id: int, api_hash: str, phone_number: str, config: Config):
        client = Client(
            name=str(config.session_file),
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
        )

        async def _create_session():
            async with client:
                ...

        run_coroutine(_create_session())

    def __init__(self, config: Config):
        self.client: Client = Client(name=str(config.session_file))
        self.config: Config = config

    async def validate_chat(self, chat_id: int) -> None:
        """Validate storage chat permissions"""
        try:
            async with self.client:
                me = await self.client.get_me()
                member = await self.client.get_chat_member(chat_id, me.id)
                if member.status not in [
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.OWNER,
                ]:
                    raise Exception("User needs to be an admin or owner of the chat")
        except ChannelPrivate as e:
            raise Exception("You don't have access to this chat") from e

    async def send_message(self, text: str) -> Message:
        """Send message to storage chat"""
        async with self.client:
            msg = await self.client.send_message(
                chat_id=self.config.storage_chat_id,
                text=text,
            )
            if not msg:
                raise ValueError("Failed to send message")
            return msg

    async def upload_file(self, file_path: Path) -> Message:
        """Upload file to storage chat with enhanced progress bar"""
        async with self.client:
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                CurrentTotalColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Uploading {file_path.name}", total=file_path.stat().st_size
                )

                async def progress_callback(current, total):
                    progress.update(task, completed=current)

                msg = await self.client.send_document(
                    chat_id=self.config.storage_chat_id,
                    document=str(file_path),
                    file_name=file_path.name,
                    progress=progress_callback,
                )
                if not msg:
                    raise ValueError("Failed to upload file")
                return msg

    async def download_file(self, message_id: int, output_path: Path) -> Path:
        """Download file from storage chat with enhanced progress bar"""
        async with self.client:
            message = await self.client.get_messages(
                self.config.storage_chat_id, message_ids=message_id
            )
            if isinstance(message, list):
                raise ValueError("Got list of messages instead of single message")

            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                CurrentTotalColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Downloading {output_path.name}", total=message.document.file_size
                )

                async def progress_callback(current, total):
                    progress.update(task, completed=current)

                downloaded = await message.download(
                    file_name=str(output_path), progress=progress_callback
                )
                return Path(downloaded)

    async def download_metadata(self, output_path: Path) -> Path:
        """Download metadata file from storage chat with enhanced progress bar"""
        async with self.client:
            if output_path.exists():
                message = await self.client.get_messages(
                    self.config.storage_chat_id,
                    message_ids=self.config.metadata_message_id,
                )
                if isinstance(message, list):
                    raise ValueError("Got list of messages instead of single message")

                file_size = message.document.file_size
                if output_path.stat().st_size == file_size:
                    return output_path

            message = await self.client.get_messages(
                self.config.storage_chat_id,
                message_ids=self.config.metadata_message_id,
            )
            if isinstance(message, list):
                raise ValueError("Got list of messages instead of single message")

            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                CurrentTotalColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    f"Downloading Metadata {output_path.name}",
                    total=message.document.file_size,
                )

                async def progress_callback(current, total):
                    progress.update(task, completed=current)

                downloaded = await message.download(
                    file_name=str(output_path), progress=progress_callback
                )
                return Path(downloaded)

    async def delete_file(self, message_id: int) -> None:
        """Delete file from storage chat"""
        async with self.client:
            await self.client.delete_messages(
                chat_id=self.config.storage_chat_id,
                message_ids=message_id,
            )
