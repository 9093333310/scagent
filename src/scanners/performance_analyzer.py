"""
性能分析器 - 代码复杂度、Bundle 大小、慢查询检测
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class ComplexityIssue:
    """复杂度问题"""
    file: str
    function: str
    line: int
    complexity: int
    message: str


@dataclass
class BundleInfo:
    """Bundle 信息"""
    name: str
    size: int  # bytes
    gzip_size: int = 0


@dataclass
class PerformanceResult:
    """性能分析结果"""
    complexity_issues: List[ComplexityIssue] = field(default_factory=list)
    bundles: List[BundleInfo] = field(default_factory=list)
    n_plus_one: List[Dict] = field(default_factory=list)
    slow_patterns: List[Dict] = field(default_factory=list)
    total_bundle_size: int = 0
    avg_complexity: float = 0
    error: str = ""


class PerformanceAnalyzer:
    """性能分析器"""

    # 性能反模式
    SLOW_PATTERNS = [
        (r'for\s+\w+\s+in\s+.*:\s*\n\s*for\s+\w+\s+in', "嵌套循环 O(n²)"),
        (r'\.filter\(.*\)\.map\(', "链式 filter+map，考虑合并"),
        (r'await\s+\w+\([^)]*\)\s*\n\s*await\s+\w+\(', "串行 await，考虑 Promise.all"),
        (r'SELECT\s+\*\s+FROM', "SELECT *，建议指定字段"),
        (r'\.find\(\{[^}]*\}\)\s*$', "无索引查询"),
        (r'JSON\.parse\(JSON\.stringify\(', "深拷贝反模式，使用 structuredClone"),
        (r'new\s+Date\(\).*new\s+Date\(\)', "重复创建 Date 对象"),
        (r'document\.querySelector.*document\.querySelector', "重复 DOM 查询"),
    ]

    # N+1 查询模式
    N_PLUS_ONE_PATTERNS = [
        (r'for.*in.*:\s*\n.*\.query\(', "循环内查询 (N+1)"),
        (r'\.map\(.*=>\s*\{[^}]*fetch\(', "map 内 fetch (N+1)"),
        (r'for.*:\s*\n.*await.*\.find', "循环内 await find (N+1)"),
    ]

    def __init__(self, project_path: Path):
        self.project_path = project_path

    async def analyze(self) -> PerformanceResult:
        """分析性能"""
        result = PerformanceResult()

        # 并行执行分析
        tasks = [
            self._analyze_complexity(),
            self._analyze_bundles(),
            self._find_slow_patterns(),
        ]

        complexity, bundles, patterns = await asyncio.gather(*tasks, return_exceptions=True)

        if isinstance(complexity, list):
            result.complexity_issues = complexity
            if complexity:
                result.avg_complexity = sum(c.complexity for c in complexity) / len(complexity)

        if isinstance(bundles, list):
            result.bundles = bundles
            result.total_bundle_size = sum(b.size for b in bundles)

        if isinstance(patterns, dict):
            result.slow_patterns = patterns.get("slow", [])
            result.n_plus_one = patterns.get("n_plus_one", [])

        return result

    async def _analyze_complexity(self) -> List[ComplexityIssue]:
        """分析代码复杂度"""
        issues = []

        # Python 文件
        for py_file in self.project_path.rglob("*.py"):
            if any(p in str(py_file) for p in ["node_modules", "__pycache__", ".git", "venv"]):
                continue

            try:
                content = py_file.read_text()
                # 简单的复杂度估算：计算嵌套深度和分支数
                for i, line in enumerate(content.split("\n"), 1):
                    indent = len(line) - len(line.lstrip())
                    if indent > 20:  # 深度嵌套
                        issues.append(ComplexityIssue(
                            file=str(py_file.relative_to(self.project_path)),
                            function="",
                            line=i,
                            complexity=indent // 4,
                            message=f"嵌套深度过深 ({indent // 4} 层)"
                        ))

                # 检查函数长度
                func_pattern = re.compile(r'^(async\s+)?def\s+(\w+)\s*\(', re.MULTILINE)
                for match in func_pattern.finditer(content):
                    func_name = match.group(2)
                    start = match.start()
                    # 估算函数长度
                    lines_after = content[start:].split("\n")
                    func_lines = 0
                    for line in lines_after[1:]:
                        if line and not line[0].isspace() and not line.startswith("#"):
                            break
                        func_lines += 1

                    if func_lines > 50:
                        issues.append(ComplexityIssue(
                            file=str(py_file.relative_to(self.project_path)),
                            function=func_name,
                            line=content[:start].count("\n") + 1,
                            complexity=func_lines,
                            message=f"函数过长 ({func_lines} 行)"
                        ))
            except:
                pass

        return issues[:50]  # 限制数量

    async def _analyze_bundles(self) -> List[BundleInfo]:
        """分析 Bundle 大小"""
        bundles = []

        # 检查常见的 bundle 目录
        bundle_dirs = [
            self.project_path / "dist",
            self.project_path / "build",
            self.project_path / ".next" / "static",
        ]

        for bundle_dir in bundle_dirs:
            if not bundle_dir.exists():
                continue

            for js_file in bundle_dir.rglob("*.js"):
                size = js_file.stat().st_size
                if size > 10000:  # 只报告 > 10KB 的文件
                    bundles.append(BundleInfo(
                        name=str(js_file.relative_to(self.project_path)),
                        size=size,
                    ))

        return sorted(bundles, key=lambda x: x.size, reverse=True)[:20]

    async def _find_slow_patterns(self) -> Dict:
        """查找性能反模式"""
        slow = []
        n_plus_one = []

        code_files = list(self.project_path.rglob("*.py")) + \
                     list(self.project_path.rglob("*.ts")) + \
                     list(self.project_path.rglob("*.js"))

        for file in code_files:
            if any(p in str(file) for p in ["node_modules", "__pycache__", ".git", "dist"]):
                continue

            try:
                content = file.read_text()
                rel_path = str(file.relative_to(self.project_path))

                for pattern, message in self.SLOW_PATTERNS:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        line = content[:match.start()].count("\n") + 1
                        slow.append({
                            "file": rel_path,
                            "line": line,
                            "message": message,
                            "code": match.group()[:100],
                        })

                for pattern, message in self.N_PLUS_ONE_PATTERNS:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        line = content[:match.start()].count("\n") + 1
                        n_plus_one.append({
                            "file": rel_path,
                            "line": line,
                            "message": message,
                        })
            except:
                pass

        return {"slow": slow[:30], "n_plus_one": n_plus_one[:20]}

    def format_report(self, result: PerformanceResult) -> str:
        """格式化报告"""
        lines = ["# 性能分析报告\n"]

        # 总览
        lines.append("## 总览\n")
        lines.append(f"- 复杂度问题: {len(result.complexity_issues)}")
        lines.append(f"- 性能反模式: {len(result.slow_patterns)}")
        lines.append(f"- N+1 查询: {len(result.n_plus_one)}")
        if result.total_bundle_size > 0:
            lines.append(f"- Bundle 总大小: {result.total_bundle_size / 1024:.1f} KB")

        # 复杂度问题
        if result.complexity_issues:
            lines.append("\n## 复杂度问题\n")
            for issue in result.complexity_issues[:10]:
                lines.append(f"- **{issue.file}:{issue.line}** - {issue.message}")

        # N+1 查询
        if result.n_plus_one:
            lines.append("\n## ⚠️ N+1 查询风险\n")
            for item in result.n_plus_one[:10]:
                lines.append(f"- **{item['file']}:{item['line']}** - {item['message']}")

        # 性能反模式
        if result.slow_patterns:
            lines.append("\n## 性能反模式\n")
            for item in result.slow_patterns[:10]:
                lines.append(f"- **{item['file']}:{item['line']}** - {item['message']}")

        # Bundle 分析
        if result.bundles:
            lines.append("\n## Bundle 大小\n")
            lines.append("| 文件 | 大小 |")
            lines.append("|------|------|")
            for b in result.bundles[:10]:
                size_kb = b.size / 1024
                icon = "🔴" if size_kb > 500 else "🟡" if size_kb > 100 else "🟢"
                lines.append(f"| {b.name} | {icon} {size_kb:.1f} KB |")

        return "\n".join(lines)
