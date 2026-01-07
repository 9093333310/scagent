"""
错误处理模块 - 友好的错误提示和恢复建议
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel

console = Console()


class ShenChaError(Exception):
    """ShenCha 基础错误"""

    def __init__(self, message: str, hint: Optional[str] = None, code: str = "E000"):
        self.message = message
        self.hint = hint
        self.code = code
        super().__init__(message)

    def display(self):
        """显示友好的错误信息"""
        error_text = f"[red]✗ {self.message}[/red]"
        if self.hint:
            error_text += f"\n\n[yellow]💡 提示:[/yellow] {self.hint}"

        console.print(Panel(
            error_text,
            title=f"[red]错误 {self.code}[/red]",
            border_style="red"
        ))


class ConfigError(ShenChaError):
    """配置错误"""

    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(
            message,
            hint or "运行 [cyan]shencha config[/cyan] 进行配置",
            "E001"
        )


class APIError(ShenChaError):
    """API 错误"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        hints = {
            401: "API Key 无效，请检查配置",
            403: "API 访问被拒绝，请检查权限",
            429: "请求过于频繁，请稍后重试",
            500: "API 服务器错误，请稍后重试",
        }
        hint = hints.get(status_code, "检查网络连接和 API 配置")
        super().__init__(message, hint, f"E1{status_code or 0:02d}")


class ProjectError(ShenChaError):
    """项目错误"""

    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(
            message,
            hint or "请确保在正确的项目目录中运行",
            "E002"
        )


class FileError(ShenChaError):
    """文件错误"""

    def __init__(self, message: str, file_path: str):
        super().__init__(
            message,
            f"文件路径: {file_path}",
            "E003"
        )


class SecurityError(ShenChaError):
    """安全错误"""

    def __init__(self, message: str):
        super().__init__(
            message,
            "此操作被安全策略阻止",
            "E004"
        )


def handle_error(error: Exception):
    """统一错误处理"""
    if isinstance(error, ShenChaError):
        error.display()
    elif isinstance(error, KeyboardInterrupt):
        console.print("\n[cyan]👋 操作已取消[/cyan]")
    elif isinstance(error, FileNotFoundError):
        ShenChaError(
            f"文件未找到: {error.filename}",
            "请检查文件路径是否正确",
            "E003"
        ).display()
    elif isinstance(error, PermissionError):
        ShenChaError(
            "权限不足",
            "请检查文件/目录权限",
            "E005"
        ).display()
    else:
        # 未知错误
        console.print(Panel(
            f"[red]{type(error).__name__}: {error}[/red]\n\n"
            "[dim]如果问题持续，请提交 Issue:[/dim]\n"
            "[blue]https://github.com/x-tavern/shencha-agent/issues[/blue]",
            title="[red]未知错误[/red]",
            border_style="red"
        ))


# 常用错误消息
ERROR_MESSAGES = {
    "no_api_key": ConfigError(
        "未配置 API Key",
        "运行 [cyan]shencha config[/cyan] 或设置环境变量 [cyan]SHENCHA_API_KEY[/cyan]"
    ),
    "no_project": ProjectError(
        "未找到项目",
        "请在项目目录中运行，或指定项目路径: [cyan]shencha ./my-project[/cyan]"
    ),
    "invalid_path": ProjectError(
        "无效的项目路径",
        "请确保路径存在且可访问"
    ),
    "no_github_token": ConfigError(
        "未配置 GitHub Token",
        "PR 审查功能需要 GitHub Token，运行 [cyan]shencha config[/cyan] 配置"
    ),
}


def raise_error(error_key: str):
    """抛出预定义错误"""
    if error_key in ERROR_MESSAGES:
        raise ERROR_MESSAGES[error_key]
    raise ShenChaError(f"未知错误: {error_key}")
