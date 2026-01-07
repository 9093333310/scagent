"""
输出格式化模块 - 美观的终端输出
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown
from rich.tree import Tree
from rich.syntax import Syntax
from rich import box

console = Console()


@dataclass
class Issue:
    """问题"""
    file: str
    line: int
    severity: str  # critical, high, medium, low
    category: str  # security, performance, quality, style
    message: str
    suggestion: Optional[str] = None


@dataclass
class AuditResult:
    """审计结果"""
    total_files: int = 0
    issues: List[Issue] = None
    score: int = 100
    duration: float = 0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class OutputFormatter:
    """输出格式化器"""

    SEVERITY_COLORS = {
        "critical": "red",
        "high": "yellow",
        "medium": "cyan",
        "low": "dim",
    }

    SEVERITY_ICONS = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "⚪",
    }

    CATEGORY_ICONS = {
        "security": "🔒",
        "performance": "⚡",
        "quality": "✨",
        "style": "🎨",
        "logic": "🧠",
        "ui": "🖼️",
    }

    @staticmethod
    def print_welcome():
        """打印欢迎信息"""
        console.print("""[cyan]
   _____ _                  _____ _
  / ____| |                / ____| |
 | (___ | |__   ___ _ __  | |    | |__   __ _
  \\___ \\| '_ \\ / _ \\ '_ \\ | |    | '_ \\ / _` |
  ____) | | | |  __/ | | || |____| | | | (_| |
 |_____/|_| |_|\\___|_| |_| \\_____|_| |_|\\__,_|
[/cyan]
[magenta] AI-Powered Autonomous Code Audit Agent v2.1[/magenta]
""")

    @staticmethod
    def print_summary(result: AuditResult):
        """打印审计摘要"""
        # 计算统计
        by_severity = {}
        by_category = {}
        for issue in result.issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        # 创建表格
        table = Table(
            title="📊 审计摘要",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("指标", style="cyan")
        table.add_column("数值", justify="right")
        table.add_column("状态")

        # 添加行
        table.add_row(
            "扫描文件",
            str(result.total_files),
            "[green]✓[/green]"
        )

        total_issues = len(result.issues)
        issue_status = "[green]✓[/green]" if total_issues == 0 else "[yellow]![/yellow]"
        table.add_row("发现问题", str(total_issues), issue_status)

        critical = by_severity.get("critical", 0)
        critical_status = "[red]✗[/red]" if critical > 0 else "[green]✓[/green]"
        table.add_row("严重问题", str(critical), critical_status)

        # 评分
        score_color = "green" if result.score >= 80 else "yellow" if result.score >= 60 else "red"
        table.add_row("代码评分", f"[{score_color}]{result.score}/100[/{score_color}]", "")

        console.print(table)

    @staticmethod
    def print_issues(issues: List[Issue], max_display: int = 10):
        """打印问题列表"""
        if not issues:
            console.print("\n[green]✓ 未发现问题[/green]")
            return

        console.print(f"\n[bold]发现 {len(issues)} 个问题:[/bold]\n")

        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 4))

        for i, issue in enumerate(sorted_issues[:max_display]):
            icon = OutputFormatter.SEVERITY_ICONS.get(issue.severity, "⚪")
            color = OutputFormatter.SEVERITY_COLORS.get(issue.severity, "white")
            cat_icon = OutputFormatter.CATEGORY_ICONS.get(issue.category, "📝")

            console.print(f"{icon} [{color}]{issue.file}:{issue.line}[/{color}]")
            console.print(f"   {cat_icon} {issue.message}")
            if issue.suggestion:
                console.print(f"   [dim]💡 {issue.suggestion}[/dim]")
            console.print()

        if len(issues) > max_display:
            console.print(f"[dim]... 还有 {len(issues) - max_display} 个问题[/dim]")

    @staticmethod
    def print_file_tree(files: List[str], title: str = "项目结构"):
        """打印文件树"""
        tree = Tree(f"[bold cyan]{title}[/bold cyan]")

        # 构建树结构
        paths = {}
        for file in files[:50]:  # 限制显示数量
            parts = file.split("/")
            current = paths
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        def add_to_tree(node: Tree, data: dict):
            for name, children in sorted(data.items()):
                if children:
                    branch = node.add(f"[cyan]{name}/[/cyan]")
                    add_to_tree(branch, children)
                else:
                    node.add(f"[dim]{name}[/dim]")

        add_to_tree(tree, paths)
        console.print(tree)

    @staticmethod
    def print_code_snippet(code: str, language: str = "python", title: str = ""):
        """打印代码片段"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        if title:
            console.print(Panel(syntax, title=title, border_style="cyan"))
        else:
            console.print(syntax)

    @staticmethod
    def print_diff(old_code: str, new_code: str, filename: str = ""):
        """打印代码差异"""
        console.print(Panel(
            f"[red]- {old_code}[/red]\n[green]+ {new_code}[/green]",
            title=f"[cyan]修改: {filename}[/cyan]" if filename else "代码修改",
            border_style="cyan"
        ))

    @staticmethod
    def print_report(content: str):
        """打印 Markdown 报告"""
        md = Markdown(content)
        console.print(Panel(md, title="📋 审计报告", border_style="cyan"))

    @staticmethod
    def create_progress() -> Progress:
        """创建进度条"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        )

    @staticmethod
    def print_success(message: str):
        """打印成功信息"""
        console.print(f"[green]✓[/green] {message}")

    @staticmethod
    def print_warning(message: str):
        """打印警告信息"""
        console.print(f"[yellow]![/yellow] {message}")

    @staticmethod
    def print_error(message: str):
        """打印错误信息"""
        console.print(f"[red]✗[/red] {message}")

    @staticmethod
    def print_info(message: str):
        """打印信息"""
        console.print(f"[cyan]ℹ[/cyan] {message}")

    @staticmethod
    def print_step(step: int, total: int, message: str):
        """打印步骤"""
        console.print(f"[cyan][{step}/{total}][/cyan] {message}")


# 便捷函数
fmt = OutputFormatter()
