"""安全工具模块 - 输入验证和路径安全"""
import os
import re
from pathlib import Path
from typing import Optional

# 最大输入大小限制
MAX_CODE_SIZE = 50000  # 50KB
MAX_FILE_SIZE = 100000  # 100KB
MAX_PATH_LENGTH = 500


class SecurityValidator:
    """安全验证器"""

    ALLOWED_COMMANDS = {
        'pnpm': ['type-check', 'lint', 'build', 'test', 'install'],
        'npm': ['run', 'test', 'build', 'install'],
        'pm2': ['logs', 'status', 'list', 'restart'],
        'git': ['status', 'diff', 'log', 'show', 'branch'],
    }

    # 敏感信息模式 (更完整)
    SENSITIVE_PATTERNS = [
        (r'(api[_-]?key|token|password|secret|auth|credential)[\s:=]+[^\s\'"]+', r'\1=***'),
        (r'Bearer\s+[\w\-\.]+', 'Bearer ***'),
        (r'sk-[a-zA-Z0-9]{20,}', 'sk-***'),  # OpenAI
        (r'AKIA[0-9A-Z]{16}', 'AKIA***'),  # AWS Access Key
        (r'ghp_[a-zA-Z0-9]{36}', 'ghp_***'),  # GitHub Token
        (r'gho_[a-zA-Z0-9]{36}', 'gho_***'),  # GitHub OAuth
        (r'xox[baprs]-[a-zA-Z0-9-]+', 'xox***'),  # Slack Token
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', '[PRIVATE KEY]'),
        (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', '[JWT TOKEN]'),
        (r'mongodb(\+srv)?://[^\s]+', 'mongodb://***'),
        (r'postgres(ql)?://[^\s]+', 'postgresql://***'),
        (r'mysql://[^\s]+', 'mysql://***'),
    ]

    @staticmethod
    def validate_path(base_path: Path, target_path: str) -> Path:
        """验证路径，防止路径遍历攻击"""
        # 检查路径长度
        if len(target_path) > MAX_PATH_LENGTH:
            raise ValueError(f"路径过长: {len(target_path)} > {MAX_PATH_LENGTH}")

        base = base_path.resolve()
        target = (base / target_path).resolve()

        # 检查符号链接
        if target.is_symlink():
            raise ValueError(f"不允许符号链接: {target_path}")

        # 使用 commonpath 进行更安全的比较
        try:
            common = Path(os.path.commonpath([base, target]))
            if common != base:
                raise ValueError(f"路径遍历攻击检测: {target_path}")
        except ValueError:
            raise ValueError(f"路径遍历攻击检测: {target_path}")

        # 双重检查
        if not str(target).startswith(str(base) + os.sep) and target != base:
            raise ValueError(f"路径遍历攻击检测: {target_path}")

        return target

    @staticmethod
    def validate_command(cmd: str, args: list[str]) -> bool:
        """验证命令和参数"""
        if cmd not in SecurityValidator.ALLOWED_COMMANDS:
            raise ValueError(f"不允许的命令: {cmd}")

        allowed_args = SecurityValidator.ALLOWED_COMMANDS[cmd]
        if args and args[0] not in allowed_args:
            raise ValueError(f"不允许的参数: {args[0]} for {cmd}")
        return True

    @staticmethod
    def validate_app_name(name: str) -> bool:
        """验证应用名称"""
        if not name or len(name) > 100:
            raise ValueError(f"应用名称长度无效")
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError(f"非法的应用名称: {name}")
        return True

    @staticmethod
    def validate_code_size(code: str, name: str = "code") -> bool:
        """验证代码大小"""
        if len(code) > MAX_CODE_SIZE:
            raise ValueError(f"{name} 过大: {len(code)} > {MAX_CODE_SIZE}")
        return True

    @staticmethod
    def sanitize_log_line(line: str, max_length: int = 1000) -> str:
        """清理日志行，移除敏感信息"""
        result = line[:max_length]
        for pattern, replacement in SecurityValidator.SENSITIVE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @staticmethod
    def sanitize_content(content: str, max_length: int = 5000) -> str:
        """清理内容，移除敏感信息"""
        result = content[:max_length]
        for pattern, replacement in SecurityValidator.SENSITIVE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @staticmethod
    def is_safe_file_extension(filename: str) -> bool:
        """检查文件扩展名是否安全"""
        dangerous_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bat', '.cmd', '.sh',
            '.ps1', '.vbs', '.js', '.jar', '.war', '.ear'
        }
        ext = Path(filename).suffix.lower()
        return ext not in dangerous_extensions
