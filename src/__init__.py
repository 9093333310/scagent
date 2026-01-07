"""
ShenCha Agent v2.1 - AI 代码审计助手

🚀 快速开始:
    shencha              # 审计当前目录
    shencha ./project    # 审计指定项目
    shencha -q           # 快速审计
    shencha config       # 配置向导
    shencha doctor       # 环境检查

📖 文档: https://github.com/x-tavern/shencha-agent
"""

__version__ = "2.1.0"
__author__ = "X-Tavern Team"

# 核心组件
from .agent import ShenChaAgent
from .knowledge import KnowledgeBase, Pattern, Fix, Insight
from .reporters import AuditReporter

# 检查器
from .frontend_checker import FrontendChecker, FrontendCheckResult
from .log_analyzer import LogAnalyzer, LogAnalysisResult

# 修复器
from .parallel_fixer import ParallelFixer, FixTask, FixResult, FixPriority

# 安全
from .security import SecurityValidator

# 配置
from .config import ShenChaConfig, get_config

# 错误处理
from .errors import ShenChaError, ConfigError, APIError, handle_error

# 输出格式化
from .output import OutputFormatter, Issue, AuditResult

# 缓存
from .cache import FileCache

# GitHub 集成
from .integrations import GitHubIntegration, PRContext

# 扫描器
from .scanners import DependencyScanner, CoverageAnalyzer, PerformanceAnalyzer

# HTML 报告
from .html_reporter import HTMLReporter

# CLI 入口
from .cli import main

__all__ = [
    # 版本
    "__version__",
    "__author__",
    # 核心
    "ShenChaAgent",
    "KnowledgeBase",
    "Pattern",
    "Fix",
    "Insight",
    "AuditReporter",
    # 检查器
    "FrontendChecker",
    "FrontendCheckResult",
    "LogAnalyzer",
    "LogAnalysisResult",
    # 修复器
    "ParallelFixer",
    "FixTask",
    "FixResult",
    "FixPriority",
    # 安全
    "SecurityValidator",
    # 配置
    "ShenChaConfig",
    "get_config",
    # 错误
    "ShenChaError",
    "ConfigError",
    "APIError",
    "handle_error",
    # 输出
    "OutputFormatter",
    "Issue",
    "AuditResult",
    # 缓存
    "FileCache",
    # GitHub
    "GitHubIntegration",
    "PRContext",
    # 扫描器
    "DependencyScanner",
    "CoverageAnalyzer",
    "PerformanceAnalyzer",
    # HTML 报告
    "HTMLReporter",
    # CLI
    "main",
]


def cli():
    """CLI 入口点 (兼容旧版)"""
    main()
