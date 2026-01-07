"""文件级缓存系统"""
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CacheEntry:
    """缓存条目"""
    file_path: str
    content_hash: str
    analysis_result: Dict[str, Any]
    timestamp: str
    version: str = "1.0"


class FileCache:
    """文件分析缓存"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "file_cache.json"
        self.cache: Dict[str, CacheEntry] = {}
        self._load()

    def _load(self):
        """加载缓存"""
        if self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text())
                self.cache = {k: CacheEntry(**v) for k, v in data.items()}
            except:
                self.cache = {}

    def _save(self):
        """保存缓存"""
        data = {k: asdict(v) for k, v in self.cache.items()}
        self.cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def get_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def get(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        key = str(file_path)
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if not file_path.exists():
            return None

        if self.get_hash(file_path) != entry.content_hash:
            del self.cache[key]
            return None

        return entry.analysis_result

    def set(self, file_path: Path, result: Dict[str, Any]):
        """设置缓存"""
        key = str(file_path)
        self.cache[key] = CacheEntry(
            file_path=key,
            content_hash=self.get_hash(file_path),
            analysis_result=result,
            timestamp=datetime.now().isoformat()
        )
        self._save()

    def invalidate(self, file_path: Path):
        """使缓存失效"""
        key = str(file_path)
        if key in self.cache:
            del self.cache[key]
            self._save()

    def clear(self):
        """清空缓存"""
        self.cache = {}
        self._save()
