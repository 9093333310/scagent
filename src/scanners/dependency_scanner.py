"""
依赖漏洞扫描器 - npm audit, pip-audit, cargo audit
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum


class VulnerabilitySeverity(Enum):
    """漏洞严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class Vulnerability:
    """漏洞信息"""
    package: str
    version: str
    severity: VulnerabilitySeverity
    title: str
    description: str = ""
    cve: str = ""
    fix_version: str = ""
    url: str = ""

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "version": self.version,
            "severity": self.severity.value,
            "title": self.title,
            "cve": self.cve,
            "fix_version": self.fix_version,
        }


@dataclass
class ScanResult:
    """扫描结果"""
    scanner: str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    total: int = 0
    critical: int = 0
    high: int = 0
    moderate: int = 0
    low: int = 0
    error: str = ""

    def __post_init__(self):
        if self.vulnerabilities:
            self.total = len(self.vulnerabilities)
            for v in self.vulnerabilities:
                if v.severity == VulnerabilitySeverity.CRITICAL:
                    self.critical += 1
                elif v.severity == VulnerabilitySeverity.HIGH:
                    self.high += 1
                elif v.severity == VulnerabilitySeverity.MODERATE:
                    self.moderate += 1
                else:
                    self.low += 1


class DependencyScanner:
    """依赖漏洞扫描器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    async def scan_all(self) -> Dict[str, ScanResult]:
        """扫描所有支持的包管理器"""
        results = {}

        tasks = []
        if (self.project_path / "package.json").exists():
            tasks.append(("npm", self.scan_npm()))
        if (self.project_path / "requirements.txt").exists() or (self.project_path / "pyproject.toml").exists():
            tasks.append(("pip", self.scan_pip()))
        if (self.project_path / "Cargo.toml").exists():
            tasks.append(("cargo", self.scan_cargo()))

        for name, task in tasks:
            results[name] = await task

        return results

    async def scan_npm(self) -> ScanResult:
        """扫描 npm 依赖"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "audit", "--json",
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)

            data = json.loads(stdout.decode()) if stdout else {}
            vulnerabilities = []

            for name, info in data.get("vulnerabilities", {}).items():
                severity_map = {
                    "critical": VulnerabilitySeverity.CRITICAL,
                    "high": VulnerabilitySeverity.HIGH,
                    "moderate": VulnerabilitySeverity.MODERATE,
                    "low": VulnerabilitySeverity.LOW,
                }
                vulnerabilities.append(Vulnerability(
                    package=name,
                    version=info.get("range", ""),
                    severity=severity_map.get(info.get("severity", "low"), VulnerabilitySeverity.LOW),
                    title=info.get("title", ""),
                    fix_version=info.get("fixAvailable", {}).get("version", "") if isinstance(info.get("fixAvailable"), dict) else "",
                ))

            return ScanResult(scanner="npm", vulnerabilities=vulnerabilities)
        except asyncio.TimeoutError:
            return ScanResult(scanner="npm", error="Timeout")
        except Exception as e:
            return ScanResult(scanner="npm", error=str(e))

    async def scan_pip(self) -> ScanResult:
        """扫描 pip 依赖"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "pip-audit", "--format", "json",
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)

            data = json.loads(stdout.decode()) if stdout else []
            vulnerabilities = []

            for item in data:
                # pip-audit 输出格式
                vuln = item.get("vulns", [])
                for v in vuln:
                    vulnerabilities.append(Vulnerability(
                        package=item.get("name", ""),
                        version=item.get("version", ""),
                        severity=VulnerabilitySeverity.HIGH,  # pip-audit 不提供严重程度
                        title=v.get("id", ""),
                        description=v.get("description", ""),
                        fix_version=v.get("fix_versions", [""])[0] if v.get("fix_versions") else "",
                    ))

            return ScanResult(scanner="pip", vulnerabilities=vulnerabilities)
        except FileNotFoundError:
            return ScanResult(scanner="pip", error="pip-audit not installed. Run: pip install pip-audit")
        except Exception as e:
            return ScanResult(scanner="pip", error=str(e))

    async def scan_cargo(self) -> ScanResult:
        """扫描 Cargo 依赖"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "cargo", "audit", "--json",
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)

            data = json.loads(stdout.decode()) if stdout else {}
            vulnerabilities = []

            for v in data.get("vulnerabilities", {}).get("list", []):
                vulnerabilities.append(Vulnerability(
                    package=v.get("package", {}).get("name", ""),
                    version=v.get("package", {}).get("version", ""),
                    severity=VulnerabilitySeverity.HIGH,
                    title=v.get("advisory", {}).get("title", ""),
                    cve=v.get("advisory", {}).get("id", ""),
                ))

            return ScanResult(scanner="cargo", vulnerabilities=vulnerabilities)
        except FileNotFoundError:
            return ScanResult(scanner="cargo", error="cargo-audit not installed")
        except Exception as e:
            return ScanResult(scanner="cargo", error=str(e))

    def format_report(self, results: Dict[str, ScanResult]) -> str:
        """格式化报告"""
        lines = ["# 依赖漏洞扫描报告\n"]

        total_vulns = sum(r.total for r in results.values())
        total_critical = sum(r.critical for r in results.values())

        lines.append(f"**总计**: {total_vulns} 个漏洞 ({total_critical} 个严重)\n")

        for scanner, result in results.items():
            lines.append(f"\n## {scanner.upper()}\n")

            if result.error:
                lines.append(f"⚠️ 错误: {result.error}\n")
                continue

            if not result.vulnerabilities:
                lines.append("✅ 未发现漏洞\n")
                continue

            lines.append(f"发现 {result.total} 个漏洞:\n")
            lines.append(f"- 🔴 严重: {result.critical}")
            lines.append(f"- 🟠 高危: {result.high}")
            lines.append(f"- 🟡 中危: {result.moderate}")
            lines.append(f"- ⚪ 低危: {result.low}\n")

            for v in result.vulnerabilities[:10]:
                icon = {"critical": "🔴", "high": "🟠", "moderate": "🟡", "low": "⚪"}
                lines.append(f"\n### {icon.get(v.severity.value, '⚪')} {v.package}@{v.version}")
                lines.append(f"- **{v.title}**")
                if v.cve:
                    lines.append(f"- CVE: {v.cve}")
                if v.fix_version:
                    lines.append(f"- 修复版本: {v.fix_version}")

        return "\n".join(lines)
