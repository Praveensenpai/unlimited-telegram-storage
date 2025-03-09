from pathlib import Path
from typing import Optional

import typer
from pyrogram.errors import ChannelPrivate, ChatAdminRequired

from core import ChunkInfo, Config, FileMetadata, FileSplitRebuild, TelegramManager
from core.file_processor import calculate_checksum
from utils import Json, run_coroutine, size_in_humanize
from pretty_print import print_info, print_error, print_success, print_warning


app = typer.Typer()
config = Config.load()
telegram_manager = TelegramManager(config)


def check_pre_requirements() -> bool:
    if not config.global_metafile.exists():
        print_error(
            "No global metafile found. Please run the 'sync' command to update the metadata."
        )
        return False
    if not config.chat_verified:
        print_error(
            "Chat verification failed! You must be admin or owner of the channel."
        )
        return False
    return True


@app.command()
def init() -> None:
    """Initialize configuration"""
    api_id = typer.prompt("Enter API ID", type=int)
    api_hash = typer.prompt("Enter API Hash", type=str)
    phone_number = typer.prompt("Enter Phone Number (+1234567890)", type=str)
    print_info("Creating session...")
    telegram_manager.create_session(api_id, api_hash, phone_number, config)
    print_success("✅ Session created successfully!")


@app.command()
def setup_storage_chat() -> None:
    """Setup storage chat"""
    storage_chat_id = typer.prompt("Enter Storage Chat ID", type=str)
    storage_chat_id = int(storage_chat_id)
    print_info("Setting up storage chat")

    async def _setup_storage_chat():
        try:
            await telegram_manager.validate_chat(storage_chat_id)
            config.storage_chat_id = storage_chat_id
            config.chat_verified = True
            print_success("✅ Chat verification successful!")
            return
        except ChatAdminRequired:
            print_error("Bot needs admin privileges with post permission!")
        except ChannelPrivate:
            print_error("User not in channel! Join first then retry")
        config.chat_verified = False

    run_coroutine(_setup_storage_chat())
    print_success("✅ Storage chat setup complete!")


@app.command()
def sync() -> None:
    """Sync metadata between Telegram and local storage"""

    async def _sync_metadata():
        local_metadata: list[FileMetadata] = []
        telegram_metadata: list[FileMetadata] = []

        if config.global_metafile.exists():
            local_metadata = FileMetadata.get_metadatas(config.global_metafile)
        else:
            print_warning("No metadata file found in configuration (Local)")

        try:
            if not config.metadata_message_id:
                print_warning("No metadata message found in configuration (Telegram)")
            else:
                temp_metadata_path = Path.cwd() / "temp_metadata.json"
                await telegram_manager.download_metadata(temp_metadata_path)
                telegram_metadata = FileMetadata.get_metadatas(temp_metadata_path)
                temp_metadata_path.unlink()
        except Exception as e:
            print_error(f"Error downloading metadata from Telegram: {e}")
            return

        if not config.global_metafile.exists():
            print_warning("No metadata found in Telegram or locally")
            print_info("Creating a new metadata file")
            config.global_metafile.write_text(Json.dumps(local_metadata, indent=4))
            global_metadata_message = await telegram_manager.upload_file(
                config.global_metafile
            )
            config.metadata_message_id = global_metadata_message.id
            return

        if len(telegram_metadata) > len(local_metadata):
            FileMetadata.push_metadatas(telegram_metadata, Config.global_metafile)
            print_success("✅ Local metadata updated from Telegram")
        elif len(local_metadata) > len(telegram_metadata):
            config.global_metafile.write_text(Json.dumps(local_metadata, indent=4))
            global_metadata_message = await telegram_manager.upload_file(
                config.global_metafile
            )
            config.metadata_message_id = global_metadata_message.id
            print_success("✅ Telegram metadata updated from local")
        else:
            print_success("✅ Metadata is already in sync")

    run_coroutine(_sync_metadata())


@app.command()
def list_files() -> None:
    """List all uploaded files"""
    if not config.global_metafile.exists():
        print_warning("No files uploaded yet.")
        return

    global_metadatas = FileMetadata.get_metadatas(config.global_metafile)

    total_storage = 0
    for idx, meta in enumerate(global_metadatas, 1):
        file_size_str = size_in_humanize(meta.file_size)
        print_info(
            f"{idx:<3} | {meta.original_name:<50} | {file_size_str:<10} | ID: {meta.file_id} | {meta.file_type:<10}"
        )
        total_storage += meta.file_size

    size_str = size_in_humanize(total_storage)
    print_info(f"Total storage used: {size_str}")


@app.command()
def upload(file_path: Path) -> None:
    """Upload a file to Telegram storage"""

    async def _upload():
        if not check_pre_requirements():
            return
        file_checksum = calculate_checksum(file_path)

        global_metadatas = FileMetadata.get_metadatas(config.global_metafile)

        for data in global_metadatas:
            if data.checksum == file_checksum:
                print_warning(
                    f"File '{file_path.name}' already exists with name: {data.original_name} and ID: {data.file_id}"
                )
                return

        metadata = FileMetadata.new(file_path)
        print_info(f"Filename: {metadata.original_name}")
        print_info(f"File Type Detected: {metadata.file_type}")
        print_info(f"File Format: {metadata.extension}")
        print_info(f"File Size: {size_in_humanize(metadata.file_size)}")
        print_info(f"File Checksum: {metadata.checksum}")
        splitter = FileSplitRebuild()
        chunks = list(splitter._split_file(file_path))

        print_info(f"Uploading {file_path.name} ({len(chunks)} chunks)")
        for idx, chunk in enumerate(chunks, start=1):
            message = await telegram_manager.upload_file(chunk)
            metadata.chunks.append(
                ChunkInfo.new(message_id=message.id, file=chunk, index=idx)
            )
            chunk.unlink()
        global_metadatas.append(metadata)
        FileMetadata.push_metadatas(global_metadatas, config.global_metafile)
        global_metadata_message = await telegram_manager.upload_file(
            config.global_metafile
        )
        config.metadata_message_id = global_metadata_message.id
        print_success(f"✅ Upload complete! File ID: {metadata.file_id}")

    run_coroutine(_upload())


@app.command()
def download(file_id: str, output_dir: Path = Path.cwd()) -> None:
    """Download a file from Telegram storage"""

    async def _download():
        if not check_pre_requirements():
            return

        global_metadatas = FileMetadata.get_metadatas(config.global_metafile)

        metadata = next((m for m in global_metadatas if m.file_id == file_id), None)
        if not metadata:
            print_error(f"File with ID {file_id} not found in metadata.")
            return

        output_path = output_dir / metadata.original_name
        output_dir.mkdir(parents=True, exist_ok=True)

        print_info(f"Filename: {metadata.original_name}")
        print_info(f"File Type Detected: {metadata.file_type}")
        print_info(f"File Format: {metadata.extension}")
        print_info(f"File Size: {size_in_humanize(metadata.file_size)}")
        print_info(f"File Checksum: {metadata.checksum}")

        print_info(
            f"Downloading {metadata.original_name} ({len(metadata.chunks)} chunks)..."
        )

        chunk_files = []
        for chunk in metadata.chunks:
            chunk_path = output_dir / chunk.name
            chunk_path = await telegram_manager.download_file(
                chunk.message_id, chunk_path
            )
            chunk_files.append(chunk_path)

        print_info(f"Rebuilding {metadata.original_name} from chunks...")
        FileSplitRebuild()._recombine_files(metadata.to_dict(), output_dir)
        for chunk_path in chunk_files:
            chunk_path.unlink()

        print_success(f"✅ Download complete: {output_path}")

    run_coroutine(_download())


@app.command()
def delete(file_id: str) -> None:
    """Delete a file from Telegram storage and local metadata"""

    async def _delete():
        if not check_pre_requirements():
            return

        global_metadatas = FileMetadata.get_metadatas(config.global_metafile)

        metadata_to_delete: Optional[FileMetadata] = None
        for data in global_metadatas:
            if data.file_id == file_id:
                metadata_to_delete = data
                break

        if metadata_to_delete is None:
            print_error(f"File with ID {file_id} not found")
            return

        confirmation = input(
            f"Are you sure you want to delete file with ID {file_id} with filename '{metadata_to_delete.original_name}'? (y/n): "
        )
        if confirmation.lower() != "y":
            print_warning("Deletion cancelled!")
            return

        for chunk_info in metadata_to_delete.chunks:
            await telegram_manager.delete_file(chunk_info.message_id)
            print_info(f"Deleted chunk {chunk_info.name} from Telegram")

        FileMetadata.push_metadatas(
            [data for data in global_metadatas if data.file_id != file_id],
            config.global_metafile,
        )

        global_metadata_message = await telegram_manager.upload_file(
            config.global_metafile
        )
        config.metadata_message_id = global_metadata_message.id

        print_success(
            f"✅ File with ID {file_id} deleted from Telegram and local metadata"
        )

    run_coroutine(_delete())


@app.command()
def delete_all() -> None:
    """Delete all files specified in the metadata file from Telegram and local metadata"""

    async def _delete_all():
        if not check_pre_requirements():
            return

        global_metadata = FileMetadata.get_metadatas(config.global_metafile)

        if not global_metadata:
            print_warning("No files found!")
            return

        print_warning("Files to be deleted:")
        for idx, m in enumerate(global_metadata, start=1):
            file_size_str = size_in_humanize(m.file_size)
            print_warning(
                f"{idx:<3} | {m.original_name:<50} | {file_size_str:<10} | ID: {m.file_id} | {m.file_type:<10}"
            )

        confirmation = input("Are you sure you want to delete all files? (y/n): ")
        if confirmation.lower() != "y":
            print_warning("Deletion cancelled")
            return

        for metadata in global_metadata:
            for chunk_info in metadata.chunks:
                await telegram_manager.delete_file(chunk_info.message_id)
                print_info(f"Deleted chunk {chunk_info.name} from Telegram")

        # config.global_metafile.write_text(Json.dumps([], indent=4))
        FileMetadata.push_metadatas([], config.global_metafile)

        global_metadata_message = await telegram_manager.upload_file(
            config.global_metafile
        )
        config.metadata_message_id = global_metadata_message.id

        print_success("✅ All files deleted from Telegram and local metadata")

    run_coroutine(_delete_all())


if __name__ == "__main__":
    app()
