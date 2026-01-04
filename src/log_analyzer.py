#!/usr/bin/env python3
"""
日志分析器 - PM2 错误日志、运行时错误检测

用于分析：
- PM2 错误日志
- Next.js 运行时错误
- API 错误
- 数据库连接错误
- 第三方服务错误
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorCategory(Enum):
    """错误类别"""
    RUNTIME = "runtime"           # 运行时错误
    DEPENDENCY = "dependency"     # 依赖问题
    DATABASE = "database"         # 数据库错误
    API = "api"                   # API 错误
    AUTHENTICATION = "auth"       # 认证错误
    NETWORK = "network"           # 网络错误
    CONFIGURATION = "config"      # 配置错误
    MEMORY = "memory"             # 内存问题
    UNKNOWN = "unknown"


@dataclass
class LogError:
    """日志错误条目"""
    timestamp: str
    level: LogLevel
    category: ErrorCategory
    message: str
    stack_trace: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    count: int = 1
    raw_log: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "file": self.file,
            "line": self.line,
            "count": self.count,
        }


@dataclass
class LogAnalysisResult:
    """日志分析结果"""
    errors: list[LogError] = field(default_factory=list)
    warnings: list[LogError] = field(default_factory=list)
    error_patterns: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    analyzed_lines: int = 0
    time_range: Optional[tuple[str, str]] = None

    @property
    def total_errors(self) -> int:
        return sum(e.count for e in self.errors)

    @property
    def critical_errors(self) -> list[LogError]:
        critical_categories = {ErrorCategory.RUNTIME, ErrorCategory.DATABASE, ErrorCategory.DEPENDENCY}
        return [e for e in self.errors if e.category in critical_categories]

    def to_dict(self) -> dict:
        return {
            "total_errors": self.total_errors,
            "total_warnings": len(self.warnings),
            "critical_errors": len(self.critical_errors),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "error_patterns": self.error_patterns,
            "recommendations": self.recommendations,
            "analyzed_lines": self.analyzed_lines,
            "time_range": self.time_range,
        }


class LogAnalyzer:
    """PM2/Next.js 日志分析器"""

    # 错误模式定义
    ERROR_PATTERNS = {
        # 依赖问题
        r"'sharp' is required": (ErrorCategory.DEPENDENCY, "sharp 图片处理库未安装"),
        r"Cannot find module '([^']+)'": (ErrorCategory.DEPENDENCY, "缺失模块: {0}"),
        r"Module not found": (ErrorCategory.DEPENDENCY, "模块未找到"),

        # 运行时错误
        r"TypeError: Cannot read properties? of (null|undefined)": (ErrorCategory.RUNTIME, "空指针访问"),
        r"TypeError: (\w+) is not a function": (ErrorCategory.RUNTIME, "类型错误: {0} 不是函数"),
        r"ReferenceError: (\w+) is not defined": (ErrorCategory.RUNTIME, "引用错误: {0} 未定义"),
        r"SyntaxError": (ErrorCategory.RUNTIME, "语法错误"),

        # 数据库错误
        r"PrismaClient.*error": (ErrorCategory.DATABASE, "Prisma 数据库错误"),
        r"Connection.*refused": (ErrorCategory.DATABASE, "数据库连接被拒绝"),
        r"ECONNREFUSED": (ErrorCategory.DATABASE, "连接被拒绝"),
        r"ER_ACCESS_DENIED": (ErrorCategory.DATABASE, "数据库访问被拒绝"),

        # API 错误
        r"Failed to find Server Action": (ErrorCategory.API, "Server Action 未找到（可能是部署不匹配）"),
        r"API.*error|Error.*API": (ErrorCategory.API, "API 错误"),
        r"fetch failed": (ErrorCategory.NETWORK, "网络请求失败"),

        # 认证错误
        r"Unauthorized|401": (ErrorCategory.AUTHENTICATION, "认证失败"),
        r"JWT.*expired|Token.*expired": (ErrorCategory.AUTHENTICATION, "Token 过期"),

        # 内存问题
        r"JavaScript heap out of memory": (ErrorCategory.MEMORY, "JavaScript 堆内存不足"),
        r"FATAL ERROR.*Heap": (ErrorCategory.MEMORY, "致命内存错误"),

        # 配置错误
        r"Missing.*environment|env.*not.*set": (ErrorCategory.CONFIGURATION, "环境变量缺失"),
    }

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()

    async def get_pm2_logs(self, lines: int = 500, app_name: str = "sillytavern-web") -> str:
        """获取 PM2 错误日志"""
        try:
            result = await asyncio.create_subprocess_exec(
                "pm2", "logs", app_name, "--lines", str(lines), "--nostream",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=30)
            return stdout.decode("utf-8", errors="ignore")

        except Exception as e:
            return f"获取 PM2 日志失败: {str(e)}"

    async def get_next_logs(self) -> str:
        """获取 Next.js 开发服务器日志（如果运行中）"""
        # 这个主要用于开发环境
        log_file = self.project_path / "apps" / "web" / ".next" / "trace"
        if log_file.exists():
            return log_file.read_text(encoding="utf-8", errors="ignore")[-50000:]
        return ""

    def parse_log_entry(self, line: str) -> Optional[LogError]:
        """解析单条日志"""
        if not line.strip():
            return None

        # 检测错误级别
        is_error = any(x in line.lower() for x in ["error", "fatal", "critical", "exception"])
        is_warning = any(x in line.lower() for x in ["warn", "warning"])

        if not is_error and not is_warning:
            return None

        level = LogLevel.ERROR if is_error else LogLevel.WARNING

        # 匹配已知错误模式
        category = ErrorCategory.UNKNOWN
        message = line.strip()[:200]

        for pattern, (cat, msg_template) in self.ERROR_PATTERNS.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                category = cat
                try:
                    message = msg_template.format(*match.groups()) if match.groups() else msg_template
                except:
                    message = msg_template
                break

        # 提取时间戳（如果有）
        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', line)
        timestamp = timestamp_match.group() if timestamp_match else datetime.now().isoformat()

        # 提取文件和行号
        file_match = re.search(r'at\s+(?:.*\s+)?\(?([^:]+):(\d+):\d+\)?', line)
        file_path = file_match.group(1) if file_match else None
        line_num = int(file_match.group(2)) if file_match else None

        return LogError(
            timestamp=timestamp,
            level=level,
            category=category,
            message=message,
            file=file_path,
            line=line_num,
            raw_log=line.strip()[:500],
        )

    def deduplicate_errors(self, errors: list[LogError]) -> list[LogError]:
        """去重并计数"""
        unique = {}
        for error in errors:
            key = (error.category.value, error.message)
            if key in unique:
                unique[key].count += 1
            else:
                unique[key] = error
        return sorted(unique.values(), key=lambda x: x.count, reverse=True)

    def generate_recommendations(self, errors: list[LogError]) -> list[str]:
        """根据错误生成修复建议"""
        recommendations = []

        categories_found = {e.category for e in errors}

        if ErrorCategory.DEPENDENCY in categories_found:
            # 检查具体缺失的依赖
            sharp_errors = [e for e in errors if "sharp" in e.message.lower()]
            if sharp_errors:
                recommendations.append("🔧 安装 sharp: pnpm add sharp")

            module_errors = [e for e in errors if "缺失模块" in e.message]
            if module_errors:
                modules = set(e.message.replace("缺失模块: ", "") for e in module_errors)
                recommendations.append(f"📦 安装缺失依赖: pnpm add {' '.join(modules)}")

        if ErrorCategory.RUNTIME in categories_found:
            null_errors = [e for e in errors if "空指针" in e.message]
            if null_errors:
                recommendations.append("⚠️ 检查空指针访问，添加可选链操作符（?.）或空值检查")

        if ErrorCategory.DATABASE in categories_found:
            recommendations.append("🔌 检查数据库连接配置和服务状态")
            recommendations.append("📝 运行 prisma migrate deploy 确保数据库迁移完成")

        if ErrorCategory.API in categories_found:
            server_action_errors = [e for e in errors if "Server Action" in e.message]
            if server_action_errors:
                recommendations.append("🔄 重新构建并重启服务: pnpm build:clean && pm2 restart sillytavern-web")

        if ErrorCategory.MEMORY in categories_found:
            recommendations.append("💾 增加 Node.js 内存限制: NODE_OPTIONS='--max-old-space-size=4096'")

        if ErrorCategory.CONFIGURATION in categories_found:
            recommendations.append("⚙️ 检查 .env 文件和 ecosystem.config.js 中的环境变量")

        return recommendations

    async def analyze(self, lines: int = 500, app_name: str = "sillytavern-web") -> LogAnalysisResult:
        """执行完整的日志分析"""
        result = LogAnalysisResult()

        # 获取 PM2 日志
        log_content = await self.get_pm2_logs(lines, app_name)
        log_lines = log_content.split("\n")
        result.analyzed_lines = len(log_lines)

        # 解析每行日志
        all_errors = []
        all_warnings = []

        for line in log_lines:
            parsed = self.parse_log_entry(line)
            if parsed:
                if parsed.level == LogLevel.ERROR:
                    all_errors.append(parsed)
                else:
                    all_warnings.append(parsed)

        # 去重
        result.errors = self.deduplicate_errors(all_errors)
        result.warnings = self.deduplicate_errors(all_warnings)

        # 统计错误模式
        for error in result.errors:
            key = f"{error.category.value}:{error.message[:50]}"
            result.error_patterns[key] = result.error_patterns.get(key, 0) + error.count

        # 生成建议
        result.recommendations = self.generate_recommendations(result.errors)

        # 时间范围
        timestamps = [e.timestamp for e in all_errors + all_warnings if e.timestamp]
        if timestamps:
            result.time_range = (min(timestamps), max(timestamps))

        return result

    async def analyze_recent_errors(self, hours: int = 24) -> LogAnalysisResult:
        """分析最近N小时的错误"""
        # 获取更多日志以覆盖时间范围
        return await self.analyze(lines=2000)

    def get_actionable_fixes(self, result: LogAnalysisResult) -> list[dict]:
        """获取可自动修复的问题"""
        fixes = []

        for error in result.errors:
            if error.category == ErrorCategory.DEPENDENCY:
                if "sharp" in error.message.lower():
                    fixes.append({
                        "type": "install_dependency",
                        "package": "sharp",
                        "command": "pnpm add sharp",
                        "priority": "high",
                    })
                elif "缺失模块" in error.message:
                    module = error.message.replace("缺失模块: ", "").strip()
                    if not module.startswith(".") and not module.startswith("@/"):
                        fixes.append({
                            "type": "install_dependency",
                            "package": module,
                            "command": f"pnpm add {module}",
                            "priority": "high",
                        })

            elif error.category == ErrorCategory.API:
                if "Server Action" in error.message:
                    fixes.append({
                        "type": "rebuild",
                        "command": "pnpm build:clean && pm2 restart sillytavern-web",
                        "priority": "medium",
                    })

        return fixes


async def main():
    """测试入口"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    analyzer = LogAnalyzer(project_path)

    print("🔍 分析 PM2 错误日志...")
    result = await analyzer.analyze(lines=100)

    print(f"\n📊 分析结果:")
    print(f"   总错误数: {result.total_errors}")
    print(f"   严重错误: {len(result.critical_errors)}")
    print(f"   警告数: {len(result.warnings)}")

    if result.errors:
        print(f"\n🔴 主要错误:")
        for error in result.errors[:10]:
            print(f"   [{error.category.value}] {error.message} (×{error.count})")

    if result.recommendations:
        print(f"\n💡 修复建议:")
        for rec in result.recommendations:
            print(f"   {rec}")

    print(f"\n详细结果:")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
