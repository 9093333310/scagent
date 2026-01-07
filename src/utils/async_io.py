"""异步 I/O 工具"""
import aiofiles
from pathlib import Path

async def read_file_async(path: Path, encoding: str = 'utf-8') -> str:
    """异步读取文件"""
    async with aiofiles.open(path, 'r', encoding=encoding) as f:
        return await f.read()

async def write_file_async(path: Path, content: str, encoding: str = 'utf-8') -> None:
    """异步写入文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, 'w', encoding=encoding) as f:
        await f.write(content)
