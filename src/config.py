"""
配置管理模块 - 零配置启动 + 智能默认值 + 安全存储
"""

import os
import stat
import locale
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import yaml


@dataclass
class ShenChaConfig:
    """ShenCha 配置"""

    # API 配置
    api_url: str = ""
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    # GitHub 配置
    github_token: str = ""

    # 审计配置
    max_file_size: int = 100000  # 100KB
    exclude_patterns: list = field(default_factory=lambda: [
        "node_modules", "__pycache__", ".git", ".next",
        "dist", "build", "*.min.js", "*.lock"
    ])

    # 输出配置
    report_format: str = "markdown"  # markdown, json, html
    language: str = ""  # auto-detect if empty

    @classmethod
    def load(cls) -> "ShenChaConfig":
        """加载配置 (优先级: 环境变量 > 配置文件 > 默认值)"""
        config = cls()

        # 1. 从配置文件加载 (不包含敏感信息)
        config_file = Path.home() / ".shencha" / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text()) or {}
                # 只加载非敏感配置
                safe_keys = ["api_url", "model", "exclude_patterns", "report_format", "language", "max_file_size"]
                for key in safe_keys:
                    if key in data and data[key]:
                        setattr(config, key, data[key])
            except yaml.YAMLError:
                pass  # 忽略 YAML 解析错误

        # 2. 从环境变量加载敏感信息 (推荐方式)
        env_mapping = {
            "SHENCHA_API_URL": "api_url",
            "SHENCHA_LLM_URL": "api_url",
            "SHENCHA_API_KEY": "api_key",
            "ANTHROPIC_API_KEY": "api_key",
            "SHENCHA_MODEL": "model",
            "GITHUB_TOKEN": "github_token",
        }

        for env_key, config_key in env_mapping.items():
            value = os.getenv(env_key)
            if value:
                setattr(config, config_key, value)

        # 3. 自动检测语言
        if not config.language:
            config.language = cls._detect_language()

        return config

    @staticmethod
    def _detect_language() -> str:
        """检测系统语言"""
        try:
            lang = locale.getdefaultlocale()[0]
            return "zh" if lang and lang.startswith("zh") else "en"
        except:
            return "en"

    def save(self, include_secrets: bool = False):
        """保存配置到文件 (默认不保存敏感信息)"""
        config_dir = Path.home() / ".shencha"
        config_dir.mkdir(parents=True, exist_ok=True)

        # 非敏感配置
        data = {
            "api_url": self.api_url,
            "model": self.model,
            "exclude_patterns": self.exclude_patterns,
            "report_format": self.report_format,
            "language": self.language,
            "max_file_size": self.max_file_size,
        }

        # 敏感信息只在明确要求时保存
        if include_secrets:
            data["api_key"] = self.api_key
            data["github_token"] = self.github_token

        config_file = config_dir / "config.yaml"
        config_file.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False))

        # 设置文件权限为 600 (仅所有者可读写)
        config_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    @property
    def is_configured(self) -> bool:
        """检查是否已配置 API"""
        return bool(self.api_key)

    def get_api_headers(self) -> dict:
        """获取 API 请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def mask_sensitive(self) -> dict:
        """返回脱敏后的配置 (用于显示)"""
        return {
            "api_url": self.api_url,
            "api_key": "***" + self.api_key[-4:] if len(self.api_key) > 4 else "***",
            "model": self.model,
            "github_token": "***" + self.github_token[-4:] if len(self.github_token) > 4 else ("***" if self.github_token else ""),
            "language": self.language,
        }


# 全局配置实例
_config: Optional[ShenChaConfig] = None


def get_config() -> ShenChaConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = ShenChaConfig.load()
    return _config


def reset_config():
    """重置配置"""
    global _config
    _config = None
