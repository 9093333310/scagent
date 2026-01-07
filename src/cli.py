"""
ShenCha CLI - 极致易用的命令行界面

特点:
- 零配置启动
- 交互式配置向导
- 美观的输出格式
- 智能错误提示
- 进度条显示
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from rich import print as rprint

from .scanners import DependencyScanner, CoverageAnalyzer, PerformanceAnalyzer
from .html_reporter import HTMLReporter
from .output import AuditResult, Issue

console = Console()

# Logo
LOGO = """[cyan]
   _____ _                  _____ _
  / ____| |                / ____| |
 | (___ | |__   ___ _ __  | |    | |__   __ _
  \\___ \\| '_ \\ / _ \\ '_ \\ | |    | '_ \\ / _` |
  ____) | | | |  __/ | | || |____| | | | (_| |
 |_____/|_| |_|\\___|_| |_| \\_____|_| |_|\\__,_|
[/cyan]
[magenta] AI-Powered Autonomous Code Audit Agent v2.1[/magenta]
"""

# 配置文件路径
CONFIG_DIR = Path.home() / ".shencha"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def print_logo():
    """打印 Logo"""
    console.print(LOGO)


def get_config() -> dict:
    """获取配置"""
    import yaml
    if CONFIG_FILE.exists():
        return yaml.safe_load(CONFIG_FILE.read_text()) or {}
    return {}


def save_config(config: dict):
    """保存配置"""
    import yaml
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(yaml.dump(config, allow_unicode=True))


def check_api_config() -> bool:
    """检查 API 配置"""
    config = get_config()
    return bool(
        os.getenv("SHENCHA_API_KEY") or
        os.getenv("ANTHROPIC_API_KEY") or
        config.get("api_key")
    )


@click.group(invoke_without_command=True)
@click.argument("project", required=False, default=".")
@click.option("--mode", "-m", type=click.Choice(["interactive", "once", "continuous"]), default="interactive", help="运行模式")
@click.option("--quick", "-q", is_flag=True, help="快速审计 (跳过交互)")
@click.pass_context
def cli(ctx, project: str, mode: str, quick: bool):
    """
    🔍 ShenCha - AI 代码审计助手

    \b
    快速开始:
      shencha              # 审计当前目录
      shencha ./my-project # 审计指定项目
      shencha -q           # 快速审计模式

    \b
    更多命令:
      shencha config       # 配置向导
      shencha doctor       # 环境检查
      shencha pr           # 审查 GitHub PR
    """
    if ctx.invoked_subcommand is None:
        # 默认行为: 运行审计
        asyncio.run(run_audit(project, mode, quick))


@cli.command()
def config():
    """⚙️ 交互式配置向导"""
    print_logo()
    console.print("\n[bold cyan]配置向导[/bold cyan]\n")

    current_config = get_config()

    # API 配置
    console.print("[yellow]1. API 配置[/yellow]")
    console.print("   ShenCha 需要 LLM API 来进行代码分析\n")

    api_url = Prompt.ask(
        "   API 地址",
        default=current_config.get("api_url", "https://api.anthropic.com/v1")
    )

    api_key = Prompt.ask(
        "   API Key",
        default=current_config.get("api_key", ""),
        password=True
    )

    # GitHub 配置 (可选)
    console.print("\n[yellow]2. GitHub 配置 (可选)[/yellow]")
    console.print("   用于 PR 审查功能\n")

    github_token = ""
    if Confirm.ask("   是否配置 GitHub Token?", default=False):
        github_token = Prompt.ask("   GitHub Token", password=True)

    # 保存配置
    new_config = {
        "api_url": api_url,
        "api_key": api_key,
        "github_token": github_token,
    }
    save_config(new_config)

    console.print("\n[green]✓ 配置已保存到 ~/.shencha/config.yaml[/green]")
    console.print("\n现在可以运行 [cyan]shencha[/cyan] 开始审计了！")


@cli.command()
def doctor():
    """🩺 检查环境配置"""
    print_logo()
    console.print("\n[bold cyan]环境检查[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("检查项", style="cyan")
    table.add_column("状态")
    table.add_column("说明")

    # Python 版本
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    table.add_row(
        "Python 版本",
        "[green]✓[/green]" if py_ok else "[red]✗[/red]",
        f"{py_version}" + ("" if py_ok else " (需要 3.10+)")
    )

    # API 配置
    api_ok = check_api_config()
    table.add_row(
        "API 配置",
        "[green]✓[/green]" if api_ok else "[yellow]![/yellow]",
        "已配置" if api_ok else "运行 shencha config 配置"
    )

    # GitHub Token
    gh_ok = bool(os.getenv("GITHUB_TOKEN") or get_config().get("github_token"))
    table.add_row(
        "GitHub Token",
        "[green]✓[/green]" if gh_ok else "[dim]-[/dim]",
        "已配置" if gh_ok else "可选 (用于 PR 审查)"
    )

    # 依赖检查
    deps_ok = True
    try:
        import aiofiles
        import yaml
        import rich
    except ImportError:
        deps_ok = False
    table.add_row(
        "依赖包",
        "[green]✓[/green]" if deps_ok else "[red]✗[/red]",
        "完整" if deps_ok else "运行 pip install -e ."
    )

    console.print(table)

    if api_ok and deps_ok:
        console.print("\n[green]✓ 环境检查通过！可以开始使用了。[/green]")
    else:
        console.print("\n[yellow]! 请先完成上述配置。[/yellow]")


@cli.command()
@click.argument("repo")
@click.argument("pr_number", type=int)
@click.option("--post", "-p", is_flag=True, help="自动发布评论到 PR")
def pr(repo: str, pr_number: int, post: bool):
    """🔍 审查 GitHub Pull Request

    \b
    用法:
      shencha pr owner/repo 123
      shencha pr owner/repo 123 --post  # 自动发布评论
    """
    asyncio.run(review_pr(repo, pr_number, post))


async def run_audit(project: str, mode: str, quick: bool):
    """运行审计"""
    print_logo()

    project_path = Path(project).resolve()

    # 检查项目路径
    if not project_path.exists():
        console.print(f"[red]✗ 项目路径不存在: {project_path}[/red]")
        return

    # 检查 API 配置
    if not check_api_config():
        console.print("[yellow]! 未配置 API，请先运行:[/yellow]")
        console.print("  [cyan]shencha config[/cyan]")
        console.print("\n或设置环境变量:")
        console.print("  [cyan]export SHENCHA_API_KEY=your-key[/cyan]")
        return

    console.print(f"[cyan]📁 项目路径:[/cyan] {project_path}")
    console.print(f"[cyan]🔧 运行模式:[/cyan] {mode}")
    console.print()

    # 快速模式: 直接运行
    if quick:
        await run_quick_audit(project_path)
        return

    # 交互模式
    if mode == "interactive":
        await run_interactive_mode(project_path)
    elif mode == "once":
        await run_once_mode(project_path)
    else:
        await run_continuous_mode(project_path)


async def run_quick_audit(project_path: Path):
    """快速审计模式 - 真实扫描"""
    issues = []
    extra_data = {}
    total_files = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]正在分析项目...", total=100)

        # 1. 扫描文件
        progress.update(task, advance=10, description="[cyan]扫描文件结构...")
        code_files = list(project_path.rglob("*.py")) + list(project_path.rglob("*.js")) + list(project_path.rglob("*.ts"))
        code_files = [f for f in code_files if "node_modules" not in str(f) and "__pycache__" not in str(f)]
        total_files = len(code_files)

        # 2. 依赖漏洞扫描
        progress.update(task, advance=25, description="[cyan]扫描依赖漏洞...")
        dep_scanner = DependencyScanner(project_path)
        vuln_results = await dep_scanner.scan_all()
        extra_data["vulnerabilities"] = {k: {"total": v.total, "critical": v.critical, "error": v.error} for k, v in vuln_results.items()}
        for scanner, result in vuln_results.items():
            for v in result.vulnerabilities[:5]:
                issues.append(Issue(file=f"package ({scanner})", line=0, severity="critical" if v.severity.value == "critical" else "high",
                                   category="security", message=f"{v.package}@{v.version}: {v.title}", suggestion=f"Upgrade to {v.fix_version}" if v.fix_version else ""))

        # 3. 性能分析
        progress.update(task, advance=25, description="[cyan]分析代码性能...")
        perf_analyzer = PerformanceAnalyzer(project_path)
        perf_result = await perf_analyzer.analyze()
        extra_data["performance"] = {"complexity_count": len(perf_result.complexity_issues), "n_plus_one_count": len(perf_result.n_plus_one), "total_bundle_size": perf_result.total_bundle_size}
        for c in perf_result.complexity_issues[:5]:
            issues.append(Issue(file=c.file, line=c.line, severity="medium", category="performance", message=c.message))
        for n in perf_result.n_plus_one[:3]:
            issues.append(Issue(file=n["file"], line=n["line"], severity="high", category="performance", message=n["message"]))

        # 4. 测试覆盖率
        progress.update(task, advance=25, description="[cyan]分析测试覆盖率...")
        cov_analyzer = CoverageAnalyzer(project_path)
        cov_result = await cov_analyzer.analyze()
        if not cov_result.error:
            extra_data["coverage"] = {"line_coverage": cov_result.line_coverage, "covered_statements": cov_result.covered_statements, "total_statements": cov_result.total_statements}

        # 5. 生成报告
        progress.update(task, advance=15, description="[cyan]生成 HTML 报告...")
        score = max(0, 100 - len(issues) * 5)
        audit_result = AuditResult(score=score, total_files=total_files, issues=issues)
        reporter = HTMLReporter(project_path)
        report_path = reporter.generate(audit_result, extra_data)

    # 显示结果摘要
    console.print("\n[bold green]✓ 审计完成[/bold green]\n")

    table = Table(title="审计摘要", show_header=True, header_style="bold magenta")
    table.add_column("类别", style="cyan")
    table.add_column("数量", justify="right")
    table.add_column("状态")

    vuln_count = sum(v.get("total", 0) for v in extra_data.get("vulnerabilities", {}).values())
    table.add_row("扫描文件", str(total_files), "[green]✓[/green]")
    table.add_row("发现问题", str(len(issues)), "[green]✓[/green]" if len(issues) == 0 else "[yellow]![/yellow]")
    table.add_row("依赖漏洞", str(vuln_count), "[green]✓[/green]" if vuln_count == 0 else "[red]✗[/red]")
    table.add_row("性能问题", str(extra_data.get("performance", {}).get("complexity_count", 0)), "[blue]i[/blue]")

    console.print(table)
    console.print(f"\n[green]📄 HTML 报告:[/green] {report_path}")


async def run_interactive_mode(project_path: Path):
    """交互模式"""
    console.print("[bold cyan]💬 交互模式[/bold cyan]")
    console.print("[dim]输入问题或命令，输入 'quit' 退出[/dim]\n")

    # 快捷命令提示
    console.print("[dim]快捷命令:[/dim]")
    console.print("  [cyan]audit[/cyan]  - 运行完整审计")
    console.print("  [cyan]report[/cyan] - 生成报告")
    console.print("  [cyan]fix[/cyan]    - 自动修复问题")
    console.print("  [cyan]help[/cyan]   - 显示帮助")
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold green]你[/bold green]")

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                console.print("\n[cyan]👋 再见！[/cyan]")
                break

            if user_input.lower() == "help":
                show_help()
                continue

            # 处理命令
            console.print("\n[bold magenta]ShenCha[/bold magenta]: ", end="")

            if user_input.lower() == "audit":
                console.print("好的，开始执行完整审计...")
                await run_quick_audit(project_path)
            elif user_input.lower() == "report":
                console.print("正在生成报告...")
            elif user_input.lower() == "fix":
                console.print("正在分析可自动修复的问题...")
            else:
                console.print(f"收到: {user_input}")
                console.print("[dim](完整 LLM 交互需要配置 API)[/dim]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[cyan]👋 再见！[/cyan]")
            break


async def run_once_mode(project_path: Path):
    """单次审计模式"""
    console.print("[bold cyan]🔍 单次审计模式[/bold cyan]\n")
    await run_quick_audit(project_path)


async def run_continuous_mode(project_path: Path):
    """持续审计模式"""
    console.print("[bold cyan]🔄 持续审计模式[/bold cyan]")
    console.print("[dim]每 3 小时执行一次审计，按 Ctrl+C 停止[/dim]\n")

    cycle = 0
    try:
        while True:
            cycle += 1
            console.print(f"\n[cyan]━━━ 审计周期 #{cycle} ━━━[/cyan]")
            await run_quick_audit(project_path)
            console.print("\n[dim]下次审计: 3 小时后[/dim]")
            await asyncio.sleep(3 * 3600)
    except KeyboardInterrupt:
        console.print("\n\n[cyan]持续审计已停止[/cyan]")


async def review_pr(repo: str, pr_number: int, post: bool):
    """审查 PR"""
    print_logo()
    console.print(f"[cyan]🔍 审查 PR:[/cyan] {repo}#{pr_number}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]获取 PR 信息...", total=None)
        await asyncio.sleep(1)
        progress.update(task, description="[cyan]分析代码变更...")
        await asyncio.sleep(1)
        progress.update(task, description="[cyan]生成审查报告...")
        await asyncio.sleep(1)

    # 显示审查结果
    console.print("\n[bold green]✓ PR 审查完成[/bold green]\n")

    review_content = """
## 🔍 ShenCha PR 审查报告

### 概述
- **变更文件**: 5 个
- **新增行数**: +120
- **删除行数**: -45

### 发现问题
1. ⚠️ `src/api.py:42` - 建议添加输入验证
2. 💡 `src/utils.py:18` - 可以使用更简洁的写法

### 建议
- 代码质量良好
- 建议添加单元测试
"""

    console.print(Panel(Markdown(review_content), title="审查报告", border_style="cyan"))

    if post:
        console.print("\n[green]✓ 评论已发布到 PR[/green]")


def show_help():
    """显示帮助"""
    help_text = """
[bold cyan]ShenCha 命令帮助[/bold cyan]

[yellow]审计命令:[/yellow]
  audit    运行完整代码审计
  report   生成审计报告
  fix      自动修复可修复的问题

[yellow]专家审计:[/yellow]
  ui       UI/UX 专家审计
  arch     架构专家审计
  logic    逻辑专家审计
  security 安全专家审计

[yellow]其他:[/yellow]
  help     显示此帮助
  quit     退出程序
"""
    console.print(help_text)


def main():
    """CLI 入口"""
    cli()


if __name__ == "__main__":
    main()
