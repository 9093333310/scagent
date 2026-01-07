"""修复工具集"""
import json
import shutil
from pathlib import Path
from typing import Any
from datetime import datetime
from claude_agent_sdk import tool

from ...security import SecurityValidator
from ...utils.async_io import read_file_async, write_file_async


def create_fix_tools(project_path: Path, knowledge):
    """创建修复工具"""

    @tool("propose_fix", "生成修复建议", {"file_path": str, "issue_description": str, "fix_type": str})
    async def propose_fix(args: dict[str, Any]) -> dict[str, Any]:
        """生成修复建议"""
        try:
            file_path = SecurityValidator.validate_path(project_path, args["file_path"])
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"安全错误: {e}"}], "is_error": True}

        if not file_path.exists():
            return {"content": [{"type": "text", "text": "文件不存在"}], "is_error": True}

        content = await read_file_async(file_path)
        lines = content.split("\n")

        # 查找相关修复历史
        similar_fixes = knowledge.get_similar_fixes(args.get("issue_description", ""))

        return {"content": [{"type": "text", "text": json.dumps({
            "file": args["file_path"],
            "total_lines": len(lines),
            "issue": args.get("issue_description", ""),
            "fix_type": args.get("fix_type", "unknown"),
            "similar_fixes": similar_fixes[:3],
            "content_preview": content[:3000]
        }, indent=2, ensure_ascii=False)}]}

    @tool("apply_fix", "应用代码修复", {
        "file_path": str, "old_code": str, "new_code": str, "description": str, "dry_run": bool
    })
    async def apply_fix(args: dict[str, Any]) -> dict[str, Any]:
        """应用修复"""
        try:
            file_path = SecurityValidator.validate_path(project_path, args["file_path"])
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"安全错误: {e}"}], "is_error": True}

        if not file_path.exists():
            return {"content": [{"type": "text", "text": "文件不存在"}], "is_error": True}

        content = await read_file_async(file_path)
        old_code = args["old_code"]
        new_code = args["new_code"]
        dry_run = args.get("dry_run", True)

        if old_code not in content:
            return {"content": [{"type": "text", "text": "未找到要替换的代码"}], "is_error": True}

        new_content = content.replace(old_code, new_code, 1)

        if dry_run:
            return {"content": [{"type": "text", "text": json.dumps({
                "status": "dry_run",
                "file": args["file_path"],
                "changes": {"old": old_code[:200], "new": new_code[:200]}
            }, indent=2, ensure_ascii=False)}]}

        # 备份
        backup_dir = project_path / ".shencha" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{file_path.name}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)

        # 写入
        await write_file_async(file_path, new_content)

        # 记录修复
        knowledge.add_fix(
            file=args["file_path"],
            description=args.get("description", ""),
            old_code=old_code,
            new_code=new_code
        )

        return {"content": [{"type": "text", "text": json.dumps({
            "status": "applied",
            "file": args["file_path"],
            "backup": str(backup_path.relative_to(project_path))
        }, indent=2, ensure_ascii=False)}]}

    return [propose_fix, apply_fix]
