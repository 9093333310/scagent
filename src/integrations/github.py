"""GitHub 集成 - PR 审查"""
import os
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

try:
    from github import Github, GithubException
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False


@dataclass
class PRFile:
    """PR 文件变更"""
    filename: str
    status: str
    additions: int
    deletions: int
    patch: Optional[str] = None


@dataclass
class PRContext:
    """PR 上下文"""
    number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    files: List[PRFile] = field(default_factory=list)
    diff_summary: str = ""


class GitHubIntegration:
    """GitHub 集成"""

    CODE_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.cpp', '.c', '.rb', '.php'}

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if HAS_GITHUB and self.token:
            self.client = Github(self.token)
        else:
            self.client = None

    def get_pr_context(self, repo_name: str, pr_number: int) -> PRContext:
        """获取 PR 上下文"""
        if not self.client:
            raise ValueError("GitHub token 未配置或 PyGithub 未安装")

        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        files = []
        for f in pr.get_files():
            if self._is_code_file(f.filename):
                files.append(PRFile(
                    filename=f.filename,
                    status=f.status,
                    additions=f.additions,
                    deletions=f.deletions,
                    patch=f.patch[:5000] if f.patch else None
                ))

        return PRContext(
            number=pr.number,
            title=pr.title,
            description=pr.body or "",
            author=pr.user.login,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            files=files,
            diff_summary=self._compress_diff(files)
        )

    def _compress_diff(self, files: List[PRFile]) -> str:
        """压缩 diff"""
        lines = []
        for f in files[:20]:
            lines.append(f"## {f.filename} ({f.status}) +{f.additions}/-{f.deletions}")
            if f.patch:
                key_lines = [l for l in f.patch.split('\n') if l.startswith(('+', '-', '@@'))][:30]
                lines.append('\n'.join(key_lines))
        return '\n\n'.join(lines)

    def _is_code_file(self, filename: str) -> bool:
        return any(filename.endswith(ext) for ext in self.CODE_EXTENSIONS)

    def post_comment(self, repo_name: str, pr_number: int, body: str):
        """发布评论"""
        if not self.client:
            raise ValueError("GitHub token 未配置")
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(body)

    def post_review(self, repo_name: str, pr_number: int, body: str, event: str = "COMMENT"):
        """发布审查"""
        if not self.client:
            raise ValueError("GitHub token 未配置")
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        pr.create_review(body=body, event=event)
