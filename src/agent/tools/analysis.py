"""分析工具集"""
import json
from pathlib import Path
from typing import Any
from claude_agent_sdk import tool

from ...security import SecurityValidator
from ...utils.async_io import read_file_async


def create_analysis_tools(project_path: Path, knowledge):
    """创建分析工具"""

    @tool("analyze_file", "深度分析单个代码文件", {"file_path": str, "focus_areas": str})
    async def analyze_file(args: dict[str, Any]) -> dict[str, Any]:
        """分析单个文件"""
        try:
            file_path = SecurityValidator.validate_path(project_path, args["file_path"])
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"安全错误: {e}"}], "is_error": True}

        if not file_path.exists():
            return {"content": [{"type": "text", "text": f"文件不存在: {args['file_path']}"}], "is_error": True}

        try:
            content = await read_file_async(file_path)
            focus = args.get("focus_areas", "all").split(",")
            known_patterns = knowledge.get_patterns_for_file(str(file_path))

            analysis = {
                "file": args["file_path"],
                "lines": len(content.split("\n")),
                "size_bytes": len(content),
                "focus_areas": focus,
                "known_patterns": known_patterns,
                "content_preview": content[:2000] if len(content) > 2000 else content,
            }
            return {"content": [{"type": "text", "text": json.dumps(analysis, indent=2, ensure_ascii=False)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"分析失败: {e}"}], "is_error": True}

    @tool("scan_project", "扫描项目结构", {"file_pattern": str, "exclude_patterns": str})
    async def scan_project(args: dict[str, Any]) -> dict[str, Any]:
        """扫描项目结构"""
        from datetime import datetime

        pattern = args.get("file_pattern", "**/*")
        excludes = args.get("exclude_patterns", "node_modules,__pycache__,.git,.next,.shencha").split(",")

        all_files = []
        for f in project_path.glob(pattern):
            if f.is_file():
                rel_path = str(f.relative_to(project_path))
                if not any(exc in rel_path for exc in excludes):
                    all_files.append({
                        "path": rel_path,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })

        all_files.sort(key=lambda x: x["modified"], reverse=True)

        # 统计文件类型
        type_counts = {}
        for f in all_files:
            ext = Path(f["path"]).suffix or "no_ext"
            type_counts[ext] = type_counts.get(ext, 0) + 1

        return {"content": [{"type": "text", "text": json.dumps({
            "total_files": len(all_files),
            "recent_files": all_files[:50],
            "file_types": type_counts
        }, indent=2, ensure_ascii=False)}]}

    @tool("find_issues", "查找特定类型问题", {"issue_type": str, "file_pattern": str})
    async def find_issues(args: dict[str, Any]) -> dict[str, Any]:
        """查找问题"""
        issue_type = args.get("issue_type", "all")
        file_pattern = args.get("file_pattern", "**/*.py")

        patterns = knowledge.get_patterns_by_type(issue_type)
        issues = []

        for f in project_path.glob(file_pattern):
            if f.is_file() and ".shencha" not in str(f):
                try:
                    content = await read_file_async(f)
                    for pattern in patterns:
                        import re
                        matches = re.findall(pattern.regex, content)
                        if matches:
                            issues.append({
                                "file": str(f.relative_to(project_path)),
                                "pattern": pattern.name,
                                "severity": pattern.severity,
                                "matches": len(matches)
                            })
                except:
                    pass

        return {"content": [{"type": "text", "text": json.dumps({
            "issue_type": issue_type,
            "total_issues": len(issues),
            "issues": issues[:50]
        }, indent=2, ensure_ascii=False)}]}

    return [analyze_file, scan_project, find_issues]
