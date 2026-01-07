"""ShenCha Agent 核心类 - 重构版"""
from pathlib import Path
from typing import Optional
import os

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server

from .tools import create_all_tools
from .hooks import create_hooks
from ..knowledge import KnowledgeBase
from ..reporters import AuditReporter
from ..utils.logger import setup_logger

logger = setup_logger("shencha.agent")


class ShenChaAgent:
    """审查 Agent - 核心协调类"""

    def __init__(
        self,
        project_path: str,
        config_path: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ):
        self.project_path = Path(project_path).resolve()
        self.config_path = config_path
        self.llm_base_url = llm_base_url or os.getenv("SHENCHA_LLM_URL")
        self.llm_api_key = llm_api_key or os.getenv("SHENCHA_API_KEY")

        # 状态
        self.session_id: Optional[str] = None
        self.cycle_count = 0
        self.is_running = False

        # 组件
        self.knowledge = KnowledgeBase(self.project_path / ".shencha" / "knowledge")
        self.reporter = AuditReporter(self.project_path / ".shencha" / "reports")

        # MCP
        self.mcp_server = None
        self.options = None

        logger.info(f"Agent 初始化: {self.project_path}")

    async def initialize(self):
        """初始化 Agent"""
        logger.info("🔧 初始化 ShenCha Agent...")

        await self._setup_directories()
        await self.knowledge.load()

        self.mcp_server = create_all_tools(self.project_path, self.knowledge, self.reporter)
        self.options = self._create_options()

        logger.info(f"✅ Agent 初始化完成, 知识库条目: {self.knowledge.entries}")

    async def _setup_directories(self):
        """创建必要目录"""
        (self.project_path / ".shencha" / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.project_path / ".shencha" / "reports").mkdir(parents=True, exist_ok=True)
        (self.project_path / ".shencha" / "cache").mkdir(parents=True, exist_ok=True)

    def _create_options(self) -> ClaudeAgentOptions:
        """创建 Agent 选项"""
        return ClaudeAgentOptions(
            mcp_servers=[self.mcp_server],
            hooks=create_hooks(self.knowledge, self.reporter),
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是 ShenCha Agent (审查)，一个自主代码审计系统。

你的能力：
1. 分析代码文件，发现安全、性能、质量问题
2. 使用多专家视角（UI、产品、架构、逻辑）进行全方位审计
3. 自动生成修复建议并应用
4. 持续学习和积累知识
5. 审查 GitHub Pull Request

工作原则：
- 安全第一，不执行危险操作
- 每次修改前先备份
- 详细记录所有发现和修复
- 主动与用户沟通进展"""

    async def run_once(self) -> dict:
        """运行单次审计"""
        self.cycle_count += 1
        logger.info(f"🔍 开始审计周期 #{self.cycle_count}")
        # 实际审计逻辑由 LLM 驱动
        return {"cycle": self.cycle_count, "status": "completed"}

    async def run_interactive(self):
        """运行交互模式"""
        self.is_running = True
        logger.info("💬 进入交互模式")
        # 交互逻辑
