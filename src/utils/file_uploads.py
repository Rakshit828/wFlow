import anyio
from anyio import Path
import os
from typing import AsyncIterator


class AsyncLocalStorageClient:
    def __init__(self, base_storage_dir: str = "/tmp/pipeline_storage"):
        self.base_dir = base_storage_dir

    async def _ensure_dir(self):
        """Ensures the directory exists without blocking execution paths."""
        path = Path(self.base_dir)
        if not await path.exists():
            await path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self, file_id: str, file_bytes: bytes, content_type: str = None
    ) -> str:
        """Writes binary bytes to the disk asynchronously."""
        await self._ensure_dir()
        file_path = os.path.join(self.base_dir, file_id)

        async with await anyio.open_file(file_path, "wb") as f:
            await f.write(file_bytes)
        return file_id

    async def download(self, file_id: str) -> bytes:
        """Reads file data from disk completely into a byte block."""
        file_path = os.path.join(self.base_dir, file_id)
        try:
            async with await anyio.open_file(file_path, "rb") as f:
                return await f.read()
        except FileNotFoundError:
            raise KeyError(f"File Reference '{file_id}' not found in internal storage.")

    async def download_stream(
        self, file_id: str, chunk_size: int = 1024 * 1024
    ) -> AsyncIterator[bytes]:
        """Streams the file off the local disk cleanly to preserve memory overhead."""
        file_path = os.path.join(self.base_dir, file_id)
        async with await anyio.open_file(file_path, "rb") as f:
            while chunk := await f.read(chunk_size):
                yield chunk

    async def delete(self, file_id: str):
        """Removes the file after pipeline lifecycle ends to preserve disk limits."""
        file_path = Path(os.path.join(self.base_dir, file_id))
        if await file_path.exists():
            await file_path.unlink()
