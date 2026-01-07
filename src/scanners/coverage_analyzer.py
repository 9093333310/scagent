"""
测试覆盖率分析器
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class FileCoverage:
    """文件覆盖率"""
    file: str
    statements: int = 0
    covered: int = 0
    missing: List[int] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return (self.covered / self.statements * 100) if self.statements > 0 else 0


@dataclass
class CoverageResult:
    """覆盖率结果"""
    total_statements: int = 0
    covered_statements: int = 0
    total_branches: int = 0
    covered_branches: int = 0
    files: List[FileCoverage] = field(default_factory=list)
    error: str = ""

    @property
    def line_coverage(self) -> float:
        return (self.covered_statements / self.total_statements * 100) if self.total_statements > 0 else 0

    @property
    def branch_coverage(self) -> float:
        return (self.covered_branches / self.total_branches * 100) if self.total_branches > 0 else 0


class CoverageAnalyzer:
    """测试覆盖率分析器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    async def analyze(self) -> CoverageResult:
        """分析覆盖率"""
        # 检测项目类型
        if (self.project_path / "package.json").exists():
            return await self._analyze_js()
        elif (self.project_path / "pyproject.toml").exists() or (self.project_path / "setup.py").exists():
            return await self._analyze_python()
        else:
            return CoverageResult(error="Unsupported project type")

    async def _analyze_python(self) -> CoverageResult:
        """分析 Python 覆盖率"""
        try:
            # 运行 pytest --cov
            proc = await asyncio.create_subprocess_exec(
                "pytest", "--cov", "--cov-report=json", "--cov-report=term-missing", "-q",
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=300)

            # 读取 coverage.json
            cov_file = self.project_path / "coverage.json"
            if not cov_file.exists():
                return CoverageResult(error="coverage.json not found. Run: pytest --cov --cov-report=json")

            data = json.loads(cov_file.read_text())

            files = []
            total_stmts = 0
            covered_stmts = 0

            for file_path, info in data.get("files", {}).items():
                summary = info.get("summary", {})
                fc = FileCoverage(
                    file=file_path,
                    statements=summary.get("num_statements", 0),
                    covered=summary.get("covered_lines", 0),
                    missing=info.get("missing_lines", []),
                )
                files.append(fc)
                total_stmts += fc.statements
                covered_stmts += fc.covered

            return CoverageResult(
                total_statements=total_stmts,
                covered_statements=covered_stmts,
                files=files,
            )
        except FileNotFoundError:
            return CoverageResult(error="pytest not found. Run: pip install pytest pytest-cov")
        except Exception as e:
            return CoverageResult(error=str(e))

    async def _analyze_js(self) -> CoverageResult:
        """分析 JavaScript 覆盖率"""
        try:
            # 检查是否有 coverage 目录
            cov_dir = self.project_path / "coverage"
            cov_file = cov_dir / "coverage-summary.json"

            if not cov_file.exists():
                # 尝试运行测试
                proc = await asyncio.create_subprocess_exec(
                    "npm", "test", "--", "--coverage", "--coverageReporters=json-summary",
                    cwd=str(self.project_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=300)

            if not cov_file.exists():
                return CoverageResult(error="coverage-summary.json not found")

            data = json.loads(cov_file.read_text())
            total = data.get("total", {})

            return CoverageResult(
                total_statements=total.get("statements", {}).get("total", 0),
                covered_statements=total.get("statements", {}).get("covered", 0),
                total_branches=total.get("branches", {}).get("total", 0),
                covered_branches=total.get("branches", {}).get("covered", 0),
            )
        except Exception as e:
            return CoverageResult(error=str(e))

    def format_report(self, result: CoverageResult) -> str:
        """格式化报告"""
        if result.error:
            return f"⚠️ 覆盖率分析失败: {result.error}"

        lines = ["# 测试覆盖率报告\n"]

        # 总体覆盖率
        cov = result.line_coverage
        icon = "🟢" if cov >= 80 else "🟡" if cov >= 60 else "🔴"
        lines.append(f"## 总体覆盖率: {icon} {cov:.1f}%\n")

        lines.append(f"- 语句覆盖: {result.covered_statements}/{result.total_statements}")
        if result.total_branches > 0:
            lines.append(f"- 分支覆盖: {result.covered_branches}/{result.total_branches} ({result.branch_coverage:.1f}%)")

        # 文件详情
        if result.files:
            lines.append("\n## 文件详情\n")
            lines.append("| 文件 | 覆盖率 | 语句 | 未覆盖行 |")
            lines.append("|------|--------|------|----------|")

            for f in sorted(result.files, key=lambda x: x.percentage)[:20]:
                icon = "🟢" if f.percentage >= 80 else "🟡" if f.percentage >= 60 else "🔴"
                missing = ",".join(map(str, f.missing[:5]))
                if len(f.missing) > 5:
                    missing += f"...+{len(f.missing)-5}"
                lines.append(f"| {f.file} | {icon} {f.percentage:.0f}% | {f.covered}/{f.statements} | {missing} |")

        return "\n".join(lines)
