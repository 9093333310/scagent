"""
ShenCha Agent - 基于 Claude Agent SDK 的自主代码审计系统

特性：
- 完全 LLM 驱动的自主决策
- 持续运行和学习
- 与用户实时沟通
- 知识库积累和应用
- 前后端代码检查 (TypeScript/ESLint)
- PM2 错误日志分析
- 多线程并行修复
"""

from .agent import ShenChaAgent, main, async_main
from .knowledge import KnowledgeBase, Pattern, Fix, Insight
from .reporters import AuditReporter, ConsoleReporter
from .frontend_checker import FrontendChecker, FrontendCheckResult, TypeScriptError, MissingDependency
from .log_analyzer import LogAnalyzer, LogAnalysisResult, LogError, ErrorCategory
from .parallel_fixer import ParallelFixer, FixTask, FixResult, FixPriority, FixStatus, FixTaskGenerator, CommonFixes

__version__ = "2.0.0"
__author__ = "X-Tavern Team"

__all__ = [
    # Agent
    "ShenChaAgent",
    "main",
    "async_main",
    # Knowledge
    "KnowledgeBase",
    "Pattern",
    "Fix",
    "Insight",
    # Reporters
    "AuditReporter",
    "ConsoleReporter",
    # Frontend Checker
    "FrontendChecker",
    "FrontendCheckResult",
    "TypeScriptError",
    "MissingDependency",
    # Log Analyzer
    "LogAnalyzer",
    "LogAnalysisResult",
    "LogError",
    "ErrorCategory",
    # Parallel Fixer
    "ParallelFixer",
    "FixTask",
    "FixResult",
    "FixPriority",
    "FixStatus",
    "FixTaskGenerator",
    "CommonFixes",
]
