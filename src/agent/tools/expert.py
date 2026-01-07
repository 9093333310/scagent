"""多专家审计工具集"""
import json
from pathlib import Path
from typing import Any
from claude_agent_sdk import tool

from ...utils.async_io import read_file_async
from ...security import SecurityValidator


def create_expert_tools(project_path: Path, knowledge):
    """创建专家工具"""

    async def _get_file_content(file_path: str) -> str:
        """获取文件内容"""
        try:
            path = SecurityValidator.validate_path(project_path, file_path)
            if path.exists():
                return await read_file_async(path)
        except:
            pass
        return ""

    @tool("expert_ui_audit", "🎨 UI大师视角审计", {"file_path": str, "component_type": str})
    async def expert_ui_audit(args: dict[str, Any]) -> dict[str, Any]:
        """UI 专家审计"""
        content = await _get_file_content(args["file_path"])
        prompt = f"""# 🎨 UI大师审计

**文件**: {args['file_path']}
**组件类型**: {args.get('component_type', 'unknown')}

## 审计维度
1. 组件结构和可复用性
2. 响应式设计
3. 无障碍性 (a11y)
4. 视觉一致性
5. 对标: Apple/Stripe/Linear

## 代码
```
{content[:5000]}
```

请提供详细的 UI 审计报告。"""
        return {"content": [{"type": "text", "text": prompt}]}

    @tool("expert_architect_audit", "🏛️ 架构师视角审计", {"file_path": str, "context": str})
    async def expert_architect_audit(args: dict[str, Any]) -> dict[str, Any]:
        """架构专家审计"""
        content = await _get_file_content(args["file_path"])
        prompt = f"""# 🏛️ 架构师审计

**文件**: {args['file_path']}
**上下文**: {args.get('context', '')}

## 审计维度
1. 单一职责原则
2. 依赖管理
3. 设计模式应用
4. 可扩展性
5. 对标: Google/Meta/Netflix

## 代码
```
{content[:5000]}
```

请提供详细的架构审计报告。"""
        return {"content": [{"type": "text", "text": prompt}]}

    @tool("expert_logic_audit", "🧠 逻辑大师视角审计", {"file_path": str, "focus": str})
    async def expert_logic_audit(args: dict[str, Any]) -> dict[str, Any]:
        """逻辑专家审计"""
        content = await _get_file_content(args["file_path"])
        prompt = f"""# 🧠 逻辑大师审计

**文件**: {args['file_path']}
**关注点**: {args.get('focus', 'all')}

## 审计维度
1. 逻辑正确性
2. 边界条件处理
3. 状态转换
4. 算法效率
5. 错误处理

## 代码
```
{content[:5000]}
```

请提供详细的逻辑审计报告。"""
        return {"content": [{"type": "text", "text": prompt}]}

    @tool("multi_expert_audit", "🌟 多专家综合审计", {"file_path": str, "experts": str})
    async def multi_expert_audit(args: dict[str, Any]) -> dict[str, Any]:
        """多专家综合审计"""
        content = await _get_file_content(args["file_path"])
        experts = args.get("experts", "ui,architect,logic").split(",")

        prompt = f"""# 🌟 多专家综合审计

**文件**: {args['file_path']}
**专家团队**: {', '.join(experts)}

## 代码
```
{content[:5000]}
```

请从以下专家视角进行综合审计：
- 🎨 UI大师: 组件结构、响应式、无障碍
- 🏛️ 架构师: 设计模式、依赖管理、可扩展性
- 🧠 逻辑大师: 正确性、边界条件、算法效率
- 📊 产品经理: 功能完整性、用户体验
- ✨ 审美大师: 视觉层次、动效设计

生成综合审计报告。"""
        return {"content": [{"type": "text", "text": prompt}]}

    return [expert_ui_audit, expert_architect_audit, expert_logic_audit, multi_expert_audit]
