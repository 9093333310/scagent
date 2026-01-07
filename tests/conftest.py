"""Pytest 配置"""
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_project():
    """创建临时项目目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        (project_path / "src").mkdir()
        (project_path / "src" / "test.py").write_text("def test(): pass")
        (project_path / ".shencha").mkdir()
        yield project_path


@pytest.fixture
def sample_code():
    """示例代码"""
    return '''
def vulnerable_function():
    user_input = input()
    eval(user_input)  # 安全问题

def slow_function(items):
    result = []
    for i in items:
        for j in items:
            result.append(i + j)  # O(n^2)
    return result
'''
