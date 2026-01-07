"""Hook 管理"""
from claude_agent_sdk import HookMatcher, AssistantMessage, ToolUseBlock
from ..utils.logger import get_logger

logger = get_logger("shencha.hooks")


def create_hooks(knowledge, reporter):
    """创建 Agent Hooks"""

    async def on_tool_start(tool_name: str, args: dict):
        """工具开始执行"""
        logger.info(f"🔧 工具开始: {tool_name}")
        knowledge.record_tool_usage(tool_name)

    async def on_tool_end(tool_name: str, result: dict):
        """工具执行完成"""
        is_error = result.get("is_error", False)
        status = "❌" if is_error else "✅"
        logger.info(f"{status} 工具完成: {tool_name}")

    async def on_cycle_complete(cycle: int, results: dict):
        """审计周期完成"""
        logger.info(f"📊 周期 #{cycle} 完成")
        await knowledge.save()

    return {
        "tool_start": on_tool_start,
        "tool_end": on_tool_end,
        "cycle_complete": on_cycle_complete,
    }
