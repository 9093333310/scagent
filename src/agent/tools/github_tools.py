"""GitHub PR 审查工具"""
import json
from typing import Any
from claude_agent_sdk import tool

from ...integrations.github import GitHubIntegration


def create_github_tools():
    """创建 GitHub 工具"""
    github = GitHubIntegration()

    @tool("review_pr", "审查 GitHub Pull Request", {"repo": str, "pr_number": int, "focus": str})
    async def review_pr(args: dict[str, Any]) -> dict[str, Any]:
        """审查 PR"""
        try:
            pr_ctx = github.get_pr_context(args["repo"], args["pr_number"])
        except Exception as e:
            return {"content": [{"type": "text", "text": f"获取 PR 失败: {e}"}], "is_error": True}

        focus = args.get("focus", "all")
        prompt = f"""# PR 审查任务

**PR #{pr_ctx.number}**: {pr_ctx.title}
**作者**: {pr_ctx.author}
**分支**: {pr_ctx.head_branch} → {pr_ctx.base_branch}
**描述**: {pr_ctx.description}

## 变更文件 ({len(pr_ctx.files)} 个)
{pr_ctx.diff_summary}

## 审查重点: {focus}

请从以下角度审查：
1. 代码质量和最佳实践
2. 潜在 bug 和边界情况
3. 安全问题
4. 性能影响
5. 可维护性

生成结构化审查报告。"""

        return {"content": [{"type": "text", "text": prompt}]}

    @tool("post_pr_comment", "在 PR 上发布评论", {"repo": str, "pr_number": int, "comment": str})
    async def post_pr_comment(args: dict[str, Any]) -> dict[str, Any]:
        """发布评论"""
        try:
            github.post_comment(args["repo"], args["pr_number"], args["comment"])
            return {"content": [{"type": "text", "text": "评论已发布"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"发布失败: {e}"}], "is_error": True}

    return [review_pr, post_pr_comment]
