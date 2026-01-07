"""
国际化支持 - 中英文双语
"""

from typing import Dict

# 语言包
MESSAGES: Dict[str, Dict[str, str]] = {
    "zh": {
        # CLI
        "welcome": "欢迎使用 ShenCha AI 代码审计助手",
        "audit_start": "开始审计...",
        "audit_complete": "审计完成",
        "scanning_files": "扫描文件结构...",
        "analyzing_code": "分析代码质量...",
        "checking_security": "检查安全问题...",
        "generating_report": "生成报告...",

        # Config
        "config_wizard": "配置向导",
        "api_config": "API 配置",
        "api_hint": "ShenCha 需要 LLM API 来进行代码分析",
        "api_url": "API 地址",
        "api_key": "API Key",
        "github_config": "GitHub 配置 (可选)",
        "github_hint": "用于 PR 审查功能",
        "config_github": "是否配置 GitHub Token?",
        "config_saved": "配置已保存",
        "config_ready": "现在可以运行 shencha 开始审计了！",

        # Doctor
        "env_check": "环境检查",
        "check_item": "检查项",
        "status": "状态",
        "description": "说明",
        "python_version": "Python 版本",
        "api_configured": "API 配置",
        "configured": "已配置",
        "not_configured": "未配置",
        "run_config": "运行 shencha config 配置",
        "github_token": "GitHub Token",
        "optional": "可选",
        "for_pr_review": "用于 PR 审查",
        "dependencies": "依赖包",
        "complete": "完整",
        "env_ok": "环境检查通过！可以开始使用了。",
        "env_incomplete": "请先完成上述配置。",

        # Interactive
        "interactive_mode": "交互模式",
        "input_hint": "输入问题或命令，输入 'quit' 退出",
        "quick_commands": "快捷命令:",
        "cmd_audit": "运行完整审计",
        "cmd_report": "生成报告",
        "cmd_fix": "自动修复问题",
        "cmd_help": "显示帮助",
        "goodbye": "再见！",
        "unknown_command": "未知命令",
        "type_help": "输入 help 查看可用命令",

        # Errors
        "error": "错误",
        "path_not_found": "路径不存在",
        "api_not_configured": "未配置 API",
        "run_config_first": "请先运行: shencha config",
        "or_set_env": "或设置环境变量:",

        # Summary
        "audit_summary": "审计摘要",
        "metric": "指标",
        "value": "数值",
        "files_scanned": "扫描文件",
        "issues_found": "发现问题",
        "critical_issues": "严重问题",
        "code_score": "代码评分",
        "report_path": "详细报告",

        # Issues
        "no_issues": "未发现问题",
        "issues_list": "发现 {count} 个问题:",
        "more_issues": "... 还有 {count} 个问题",

        # PR Review
        "pr_review": "审查 PR",
        "pr_complete": "PR 审查完成",
        "comment_posted": "评论已发布",
    },

    "en": {
        # CLI
        "welcome": "Welcome to ShenCha AI Code Audit Assistant",
        "audit_start": "Starting audit...",
        "audit_complete": "Audit complete",
        "scanning_files": "Scanning file structure...",
        "analyzing_code": "Analyzing code quality...",
        "checking_security": "Checking security issues...",
        "generating_report": "Generating report...",

        # Config
        "config_wizard": "Configuration Wizard",
        "api_config": "API Configuration",
        "api_hint": "ShenCha requires LLM API for code analysis",
        "api_url": "API URL",
        "api_key": "API Key",
        "github_config": "GitHub Configuration (Optional)",
        "github_hint": "For PR review feature",
        "config_github": "Configure GitHub Token?",
        "config_saved": "Configuration saved",
        "config_ready": "Now you can run shencha to start auditing!",

        # Doctor
        "env_check": "Environment Check",
        "check_item": "Check Item",
        "status": "Status",
        "description": "Description",
        "python_version": "Python Version",
        "api_configured": "API Config",
        "configured": "Configured",
        "not_configured": "Not configured",
        "run_config": "Run shencha config",
        "github_token": "GitHub Token",
        "optional": "Optional",
        "for_pr_review": "For PR review",
        "dependencies": "Dependencies",
        "complete": "Complete",
        "env_ok": "Environment check passed! Ready to use.",
        "env_incomplete": "Please complete the configuration above.",

        # Interactive
        "interactive_mode": "Interactive Mode",
        "input_hint": "Enter question or command, type 'quit' to exit",
        "quick_commands": "Quick commands:",
        "cmd_audit": "Run full audit",
        "cmd_report": "Generate report",
        "cmd_fix": "Auto-fix issues",
        "cmd_help": "Show help",
        "goodbye": "Goodbye!",
        "unknown_command": "Unknown command",
        "type_help": "Type help for available commands",

        # Errors
        "error": "Error",
        "path_not_found": "Path not found",
        "api_not_configured": "API not configured",
        "run_config_first": "Please run first: shencha config",
        "or_set_env": "Or set environment variable:",

        # Summary
        "audit_summary": "Audit Summary",
        "metric": "Metric",
        "value": "Value",
        "files_scanned": "Files Scanned",
        "issues_found": "Issues Found",
        "critical_issues": "Critical Issues",
        "code_score": "Code Score",
        "report_path": "Detailed Report",

        # Issues
        "no_issues": "No issues found",
        "issues_list": "Found {count} issues:",
        "more_issues": "... {count} more issues",

        # PR Review
        "pr_review": "Review PR",
        "pr_complete": "PR review complete",
        "comment_posted": "Comment posted",
    }
}


class I18n:
    """国际化工具"""

    _lang: str = "zh"

    @classmethod
    def set_language(cls, lang: str):
        """设置语言"""
        cls._lang = lang if lang in MESSAGES else "en"

    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        """获取翻译文本"""
        text = MESSAGES.get(cls._lang, MESSAGES["en"]).get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text

    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        """get 的别名"""
        return cls.get(key, **kwargs)


# 便捷函数
def t(key: str, **kwargs) -> str:
    """翻译函数"""
    return I18n.get(key, **kwargs)


def set_lang(lang: str):
    """设置语言"""
    I18n.set_language(lang)
