"""安全模块测试"""
import pytest
from pathlib import Path
from src.security import SecurityValidator


class TestSecurityValidator:
    """安全验证器测试"""

    def test_path_traversal_blocked(self):
        """测试路径遍历攻击防护"""
        base = Path("/project")
        with pytest.raises(ValueError, match="路径遍历"):
            SecurityValidator.validate_path(base, "../../../etc/passwd")

    def test_valid_path_allowed(self, temp_project):
        """测试正常路径"""
        result = SecurityValidator.validate_path(temp_project, "src/test.py")
        assert str(result).startswith(str(temp_project))

    def test_command_validation_allowed(self):
        """测试允许的命令"""
        assert SecurityValidator.validate_command("pnpm", ["type-check"])
        assert SecurityValidator.validate_command("git", ["status"])

    def test_command_validation_blocked(self):
        """测试禁止的命令"""
        with pytest.raises(ValueError, match="不允许的命令"):
            SecurityValidator.validate_command("rm", ["-rf"])

    def test_app_name_validation(self):
        """测试应用名称验证"""
        assert SecurityValidator.validate_app_name("my-app")
        assert SecurityValidator.validate_app_name("app_123")

        with pytest.raises(ValueError):
            SecurityValidator.validate_app_name("app; rm -rf /")

    def test_sanitize_log_line(self):
        """测试日志清理"""
        line = "API_KEY=sk-1234567890abcdef Bearer token123"
        result = SecurityValidator.sanitize_log_line(line)
        assert "sk-1234567890abcdef" not in result
        assert "***" in result
