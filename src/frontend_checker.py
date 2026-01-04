#!/usr/bin/env python3
"""
前端检查器 - TypeScript 类型检查、ESLint、缺失依赖检测

用于检测前端项目中的：
- TypeScript 类型错误
- ESLint 代码规范问题
- 缺失的 npm 依赖
- 导入错误
"""

import asyncio
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"  # 会导致运行时崩溃
    HIGH = "high"          # 编译失败
    MEDIUM = "medium"      # 类型警告
    LOW = "low"            # 代码规范


@dataclass
class TypeScriptError:
    """TypeScript 错误"""
    file: str
    line: int
    column: int
    code: str  # e.g., TS2339
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass
class MissingDependency:
    """缺失的依赖"""
    module_name: str
    required_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "module": self.module_name,
            "required_by": self.required_by,
        }


@dataclass
class FrontendCheckResult:
    """前端检查结果"""
    typescript_errors: list[TypeScriptError] = field(default_factory=list)
    eslint_errors: list[dict] = field(default_factory=list)
    missing_dependencies: list[MissingDependency] = field(default_factory=list)
    import_errors: list[dict] = field(default_factory=list)

    @property
    def total_errors(self) -> int:
        return (
            len(self.typescript_errors) +
            len(self.eslint_errors) +
            len(self.missing_dependencies) +
            len(self.import_errors)
        )

    @property
    def critical_count(self) -> int:
        return len([e for e in self.typescript_errors if e.severity == ErrorSeverity.CRITICAL])

    def to_dict(self) -> dict:
        return {
            "total_errors": self.total_errors,
            "critical_count": self.critical_count,
            "typescript_errors": [e.to_dict() for e in self.typescript_errors],
            "eslint_errors": self.eslint_errors,
            "missing_dependencies": [d.to_dict() for d in self.missing_dependencies],
            "import_errors": self.import_errors,
        }


class FrontendChecker:
    """前端代码检查器"""

    # TypeScript 错误代码分类
    CRITICAL_TS_CODES = {
        "TS2552",  # Cannot find name (可能导致运行时错误)
        "TS2304",  # Cannot find name
        "TS2307",  # Cannot find module (缺失依赖)
        "TS1361",  # Cannot be used as a value (导入错误)
    }

    HIGH_TS_CODES = {
        "TS2339",  # Property does not exist
        "TS2345",  # Argument type not assignable
        "TS2322",  # Type not assignable
        "TS2554",  # Expected N arguments
        "TS7006",  # Parameter implicitly has 'any' type
    }

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()
        self.web_app_path = self.project_path / "apps" / "web"

    async def run_typescript_check(self) -> list[TypeScriptError]:
        """运行 TypeScript 类型检查"""
        errors = []

        try:
            # 运行 pnpm type-check
            result = await asyncio.create_subprocess_exec(
                "pnpm", "type-check",
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=300)
            output = stdout.decode("utf-8", errors="ignore")

            # 解析 TypeScript 错误
            # 格式: file.ts(line,column): error TSxxxx: message
            pattern = r'([^(\s]+)\((\d+),(\d+)\):\s*error\s+(TS\d+):\s*(.+?)(?=\n[^\s]|\Z)'

            for match in re.finditer(pattern, output, re.DOTALL):
                file_path, line, column, code, message = match.groups()

                # 确定严重程度
                if code in self.CRITICAL_TS_CODES:
                    severity = ErrorSeverity.CRITICAL
                elif code in self.HIGH_TS_CODES:
                    severity = ErrorSeverity.HIGH
                else:
                    severity = ErrorSeverity.MEDIUM

                errors.append(TypeScriptError(
                    file=file_path.strip(),
                    line=int(line),
                    column=int(column),
                    code=code,
                    message=message.strip().split('\n')[0],  # 只取第一行
                    severity=severity,
                ))

        except asyncio.TimeoutError:
            errors.append(TypeScriptError(
                file="<timeout>",
                line=0,
                column=0,
                code="TIMEOUT",
                message="TypeScript 检查超时（>300秒）",
                severity=ErrorSeverity.CRITICAL,
            ))
        except Exception as e:
            errors.append(TypeScriptError(
                file="<error>",
                line=0,
                column=0,
                code="ERROR",
                message=f"TypeScript 检查失败: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
            ))

        return errors

    async def run_eslint_check(self) -> list[dict]:
        """运行 ESLint 检查"""
        errors = []

        try:
            result = await asyncio.create_subprocess_exec(
                "pnpm", "lint", "--format", "json",
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await asyncio.wait_for(result.communicate(), timeout=120)

            try:
                eslint_output = json.loads(stdout.decode("utf-8", errors="ignore"))

                for file_result in eslint_output:
                    for msg in file_result.get("messages", []):
                        errors.append({
                            "file": file_result.get("filePath", ""),
                            "line": msg.get("line", 0),
                            "column": msg.get("column", 0),
                            "rule": msg.get("ruleId", "unknown"),
                            "message": msg.get("message", ""),
                            "severity": "error" if msg.get("severity") == 2 else "warning",
                        })
            except json.JSONDecodeError:
                pass  # ESLint 输出不是 JSON 格式

        except Exception:
            pass  # ESLint 可能未配置

        return errors

    def detect_missing_dependencies(self, ts_errors: list[TypeScriptError]) -> list[MissingDependency]:
        """从 TypeScript 错误中检测缺失的依赖"""
        missing = {}

        for error in ts_errors:
            if error.code == "TS2307":  # Cannot find module
                # 提取模块名
                match = re.search(r"Cannot find module '([^']+)'", error.message)
                if match:
                    module_name = match.group(1)
                    # 排除相对路径导入
                    if not module_name.startswith(".") and not module_name.startswith("@/"):
                        if module_name not in missing:
                            missing[module_name] = MissingDependency(module_name=module_name)
                        missing[module_name].required_by.append(error.file)

        return list(missing.values())

    def detect_import_errors(self, ts_errors: list[TypeScriptError]) -> list[dict]:
        """检测导入相关错误"""
        import_errors = []

        for error in ts_errors:
            if error.code in ("TS1361", "TS2552", "TS2304"):
                if "import" in error.message.lower() or "imported" in error.message.lower():
                    import_errors.append({
                        "file": error.file,
                        "line": error.line,
                        "code": error.code,
                        "message": error.message,
                        "fix_suggestion": self._suggest_import_fix(error),
                    })

        return import_errors

    def _suggest_import_fix(self, error: TypeScriptError) -> str:
        """生成导入修复建议"""
        if error.code == "TS1361":
            # 'X' cannot be used as a value because it was imported using 'import type'
            match = re.search(r"'([^']+)' cannot be used as a value", error.message)
            if match:
                name = match.group(1)
                return f"将 'import type {{ {name} }}' 改为 'import {{ {name} }}'"

        if error.code == "TS2552":
            # Cannot find name 'X'. Did you mean 'Y'?
            match = re.search(r"Did you mean '([^']+)'", error.message)
            if match:
                suggestion = match.group(1)
                return f"可能是拼写错误，建议使用 '{suggestion}'"

        return "检查导入语句是否正确"

    def categorize_errors_by_file(self, errors: list[TypeScriptError]) -> dict[str, list[TypeScriptError]]:
        """按文件分类错误"""
        by_file = {}
        for error in errors:
            if error.file not in by_file:
                by_file[error.file] = []
            by_file[error.file].append(error)
        return by_file

    def get_error_summary(self, errors: list[TypeScriptError]) -> dict:
        """生成错误摘要"""
        by_code = {}
        for error in errors:
            if error.code not in by_code:
                by_code[error.code] = {"count": 0, "message_sample": error.message}
            by_code[error.code]["count"] += 1

        return {
            "total": len(errors),
            "by_severity": {
                "critical": len([e for e in errors if e.severity == ErrorSeverity.CRITICAL]),
                "high": len([e for e in errors if e.severity == ErrorSeverity.HIGH]),
                "medium": len([e for e in errors if e.severity == ErrorSeverity.MEDIUM]),
                "low": len([e for e in errors if e.severity == ErrorSeverity.LOW]),
            },
            "by_code": dict(sorted(by_code.items(), key=lambda x: x[1]["count"], reverse=True)[:20]),
            "files_affected": len(set(e.file for e in errors)),
        }

    async def check_all(self) -> FrontendCheckResult:
        """运行所有前端检查"""
        result = FrontendCheckResult()

        # 并行运行 TypeScript 和 ESLint 检查
        ts_task = asyncio.create_task(self.run_typescript_check())
        eslint_task = asyncio.create_task(self.run_eslint_check())

        ts_errors, eslint_errors = await asyncio.gather(ts_task, eslint_task)

        result.typescript_errors = ts_errors
        result.eslint_errors = eslint_errors
        result.missing_dependencies = self.detect_missing_dependencies(ts_errors)
        result.import_errors = self.detect_import_errors(ts_errors)

        return result


async def main():
    """测试入口"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    checker = FrontendChecker(project_path)

    print("🔍 运行前端检查...")
    result = await checker.check_all()

    print(f"\n📊 检查结果:")
    print(f"   TypeScript 错误: {len(result.typescript_errors)}")
    print(f"   ESLint 错误: {len(result.eslint_errors)}")
    print(f"   缺失依赖: {len(result.missing_dependencies)}")
    print(f"   导入错误: {len(result.import_errors)}")

    if result.missing_dependencies:
        print(f"\n📦 缺失的依赖:")
        for dep in result.missing_dependencies:
            print(f"   - {dep.module_name}")

    print(f"\n详细结果:")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
