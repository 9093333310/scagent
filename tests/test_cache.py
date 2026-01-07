"""缓存模块测试"""
import pytest
from pathlib import Path
from src.cache import FileCache


class TestFileCache:
    """文件缓存测试"""

    def test_cache_set_get(self, temp_project):
        """测试缓存读写"""
        cache = FileCache(temp_project / ".shencha" / "cache")
        test_file = temp_project / "src" / "test.py"

        result = {"issues": [], "score": 100}
        cache.set(test_file, result)

        cached = cache.get(test_file)
        assert cached == result

    def test_cache_invalidation_on_change(self, temp_project):
        """测试文件修改后缓存失效"""
        cache = FileCache(temp_project / ".shencha" / "cache")
        test_file = temp_project / "src" / "test.py"

        cache.set(test_file, {"old": True})

        # 修改文件
        test_file.write_text("def new(): pass")

        # 缓存应失效
        assert cache.get(test_file) is None

    def test_cache_clear(self, temp_project):
        """测试清空缓存"""
        cache = FileCache(temp_project / ".shencha" / "cache")
        test_file = temp_project / "src" / "test.py"

        cache.set(test_file, {"data": 1})
        cache.clear()

        assert cache.get(test_file) is None
