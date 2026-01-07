"""工具注册中心"""
from pathlib import Path
from claude_agent_sdk import create_sdk_mcp_server

from .analysis import create_analysis_tools
from .fix import create_fix_tools
from .knowledge_tools import create_knowledge_tools
from .expert import create_expert_tools


def create_all_tools(project_path: Path, knowledge, reporter):
    """创建所有工具的 MCP 服务器"""
    tools = []

    tools.extend(create_analysis_tools(project_path, knowledge))
    tools.extend(create_fix_tools(project_path, knowledge))
    tools.extend(create_knowledge_tools(knowledge))
    tools.extend(create_expert_tools(project_path, knowledge))

    return create_sdk_mcp_server("shencha", tools)


__all__ = ['create_all_tools']
