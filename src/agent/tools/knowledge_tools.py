"""知识库工具集"""
import json
from typing import Any
from claude_agent_sdk import tool


def create_knowledge_tools(knowledge):
    """创建知识库工具"""

    @tool("learn_pattern", "学习新的问题模式", {
        "name": str, "regex": str, "issue_type": str, "severity": str, "fix_suggestion": str
    })
    async def learn_pattern(args: dict[str, Any]) -> dict[str, Any]:
        """学习新模式"""
        import re
        try:
            re.compile(args["regex"])
        except re.error as e:
            return {"content": [{"type": "text", "text": f"无效的正则表达式: {e}"}], "is_error": True}

        knowledge.add_pattern(
            name=args["name"],
            regex=args["regex"],
            issue_type=args.get("issue_type", "quality"),
            severity=args.get("severity", "medium"),
            fix_suggestion=args.get("fix_suggestion", "")
        )

        return {"content": [{"type": "text", "text": f"已学习模式: {args['name']}"}]}

    @tool("get_knowledge", "获取知识库内容", {"category": str})
    async def get_knowledge(args: dict[str, Any]) -> dict[str, Any]:
        """获取知识库"""
        category = args.get("category", "all")
        summary = knowledge.get_summary(category)
        return {"content": [{"type": "text", "text": json.dumps(summary, indent=2, ensure_ascii=False)}]}

    @tool("save_insight", "保存项目洞察", {
        "title": str, "insight": str, "category": str, "priority": str, "expert_source": str
    })
    async def save_insight(args: dict[str, Any]) -> dict[str, Any]:
        """保存洞察"""
        knowledge.add_insight(
            title=args["title"],
            insight=args["insight"],
            category=args.get("category", "general"),
            priority=args.get("priority", "medium"),
            expert_source=args.get("expert_source", "general")
        )
        return {"content": [{"type": "text", "text": f"已保存洞察: {args['title']}"}]}

    return [learn_pattern, get_knowledge, save_insight]
