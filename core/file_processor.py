import hashlib
import os
from io import BufferedWriter
from pathlib import Path
from typing import Final, Generator, Optional

BUFFER_SIZE: Final[int] = 10 * 1024  # 10KB
CHUNK_SIZE: Final[int] = 2000 * 1000 * 1000  # 2000MBi


def calculate_checksum(file_path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        while c := f.read(1024 * 1024):
            hash_md5.update(c)
    return hash_md5.hexdigest()


class FileSplitRebuild:
    def _split_file(self, input_file: Path) -> Generator[Path, None, None]:
        part_num: int = 1
        bytes_written: int = 0
        dest_file: Optional[BufferedWriter] = None
        part_path: Path = input_file.with_suffix(f".part{part_num:03d}")

        file_size = input_file.stat().st_size
        total_parts = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        print(f"File will be split into {total_parts} parts.")

        buffer_size = file_size if file_size < BUFFER_SIZE else BUFFER_SIZE

        with open(input_file, "rb") as src_file:
            while chunk := src_file.read(buffer_size):
                if dest_file is None:
                    dest_file = open(part_path, "wb")

                dest_file.write(chunk)
                bytes_written += len(chunk)

                if bytes_written >= CHUNK_SIZE:
                    dest_file.close()
                    yield part_path
                    part_num += 1
                    bytes_written = 0
                    dest_file = None
                    part_path = input_file.with_suffix(f".part{part_num:03d}")

        if dest_file is not None:
            dest_file.close()
            yield part_path

    def _recombine_files(self, metadata: dict, output_dir: Path) -> Path:
        output_path: Path = output_dir / metadata["original_name"]
        temp_path: Path = output_path.with_suffix(".tmp")

        with open(temp_path, "wb") as out_file:
            for chunk in metadata["chunks"]:
                chunk_name = chunk["name"]
                chunk_path = output_dir / chunk_name
                with open(chunk_path, "rb") as in_file:
                    while chunk := in_file.read(BUFFER_SIZE):
                        out_file.write(chunk)
                # os.remove(chunk_path)
        os.rename(temp_path, output_path)
        return output_path
