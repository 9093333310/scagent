#!/usr/bin/env python3
"""
并行修复器 - 多线程/多进程并行修复代码问题

功能：
- 多线程并行处理多个文件的修复
- 按优先级排序修复任务
- 自动备份和回滚
- 修复进度追踪
- 冲突检测和处理
"""

import asyncio
import json
import shutil
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from enum import Enum
import threading
import re


class FixPriority(Enum):
    """修复优先级"""
    CRITICAL = 1    # 运行时崩溃
    HIGH = 2        # 编译失败
    MEDIUM = 3      # 类型警告
    LOW = 4         # 代码规范


class FixStatus(Enum):
    """修复状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FixTask:
    """修复任务"""
    id: str
    file_path: str
    issue_type: str
    description: str
    priority: FixPriority
    fix_function: Optional[Callable] = None
    old_code: Optional[str] = None
    new_code: Optional[str] = None
    line_number: Optional[int] = None
    status: FixStatus = FixStatus.PENDING
    error_message: Optional[str] = None
    backup_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "issue_type": self.issue_type,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "error_message": self.error_message,
            "line_number": self.line_number,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class FixResult:
    """修复结果"""
    task: FixTask
    success: bool
    message: str
    changes_made: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task.id,
            "success": self.success,
            "message": self.message,
            "changes_made": self.changes_made,
        }


class ParallelFixer:
    """并行代码修复器"""

    def __init__(self, project_path: str | Path, max_workers: int = 4):
        self.project_path = Path(project_path).resolve()
        self.max_workers = max_workers
        self.backup_dir = self.project_path / ".shencha" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 线程安全的任务队列和结果
        self._lock = threading.Lock()
        self._tasks: list[FixTask] = []
        self._results: list[FixResult] = []
        self._file_locks: dict[str, threading.Lock] = {}

    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """获取文件锁（防止同一文件被多个线程同时修改）"""
        with self._lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]

    def _backup_file(self, file_path: Path) -> Optional[Path]:
        """备份文件"""
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()[:8]

        backup_name = f"{file_path.name}.{timestamp}.{content_hash}.bak"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _restore_file(self, file_path: Path, backup_path: Path) -> bool:
        """从备份恢复文件"""
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
            return True
        return False

    def add_task(self, task: FixTask):
        """添加修复任务"""
        with self._lock:
            self._tasks.append(task)

    def add_tasks(self, tasks: list[FixTask]):
        """批量添加任务"""
        with self._lock:
            self._tasks.extend(tasks)

    def create_fix_task(
        self,
        file_path: str,
        issue_type: str,
        description: str,
        priority: FixPriority,
        old_code: Optional[str] = None,
        new_code: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> FixTask:
        """创建修复任务"""
        task_id = f"{file_path}:{line_number or 0}:{hashlib.md5(description.encode()).hexdigest()[:8]}"

        return FixTask(
            id=task_id,
            file_path=file_path,
            issue_type=issue_type,
            description=description,
            priority=priority,
            old_code=old_code,
            new_code=new_code,
            line_number=line_number,
        )

    def _execute_fix(self, task: FixTask) -> FixResult:
        """执行单个修复任务"""
        file_path = self.project_path / task.file_path
        file_lock = self._get_file_lock(task.file_path)

        with file_lock:
            try:
                task.status = FixStatus.IN_PROGRESS

                if not file_path.exists():
                    task.status = FixStatus.FAILED
                    task.error_message = "文件不存在"
                    return FixResult(task, False, "文件不存在")

                # 备份文件
                backup_path = self._backup_file(file_path)
                task.backup_path = str(backup_path) if backup_path else None

                content = file_path.read_text(encoding="utf-8")

                # 如果提供了具体的替换代码
                if task.old_code and task.new_code:
                    if task.old_code not in content:
                        task.status = FixStatus.SKIPPED
                        return FixResult(task, False, "找不到要替换的代码")

                    new_content = content.replace(task.old_code, task.new_code, 1)
                    file_path.write_text(new_content, encoding="utf-8")

                    task.status = FixStatus.SUCCESS
                    task.completed_at = datetime.now().isoformat()
                    return FixResult(
                        task, True,
                        f"成功替换代码",
                        changes_made=f"- {task.old_code[:50]}...\n+ {task.new_code[:50]}..."
                    )

                # 如果提供了自定义修复函数
                elif task.fix_function:
                    result = task.fix_function(content, task)
                    if result:
                        file_path.write_text(result, encoding="utf-8")
                        task.status = FixStatus.SUCCESS
                        task.completed_at = datetime.now().isoformat()
                        return FixResult(task, True, "自定义修复成功")
                    else:
                        task.status = FixStatus.FAILED
                        return FixResult(task, False, "自定义修复失败")

                else:
                    task.status = FixStatus.SKIPPED
                    return FixResult(task, False, "没有提供修复方案")

            except Exception as e:
                task.status = FixStatus.FAILED
                task.error_message = str(e)

                # 尝试回滚
                if task.backup_path:
                    self._restore_file(file_path, Path(task.backup_path))

                return FixResult(task, False, f"修复失败: {str(e)}")

    def run_parallel(self, dry_run: bool = False) -> list[FixResult]:
        """并行执行所有修复任务"""
        # 按优先级排序
        sorted_tasks = sorted(self._tasks, key=lambda t: t.priority.value)

        if dry_run:
            return [FixResult(t, True, "Dry run - 未实际执行") for t in sorted_tasks]

        results = []

        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._execute_fix, task): task
                for task in sorted_tasks
            }

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  {'✅' if result.success else '❌'} {task.file_path}: {result.message}")
                except Exception as e:
                    results.append(FixResult(task, False, f"异常: {str(e)}"))
                    print(f"  ❌ {task.file_path}: 异常 - {str(e)}")

        with self._lock:
            self._results = results

        return results

    async def run_parallel_async(self, dry_run: bool = False) -> list[FixResult]:
        """异步版本的并行修复"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.run_parallel(dry_run))

    def get_summary(self) -> dict:
        """获取修复摘要"""
        with self._lock:
            tasks = self._tasks
            results = self._results

        success_count = len([r for r in results if r.success])
        failed_count = len([r for r in results if not r.success])

        by_priority = {}
        for task in tasks:
            p = task.priority.name
            if p not in by_priority:
                by_priority[p] = {"total": 0, "success": 0, "failed": 0}
            by_priority[p]["total"] += 1
            if task.status == FixStatus.SUCCESS:
                by_priority[p]["success"] += 1
            elif task.status == FixStatus.FAILED:
                by_priority[p]["failed"] += 1

        return {
            "total_tasks": len(tasks),
            "completed": len(results),
            "success": success_count,
            "failed": failed_count,
            "by_priority": by_priority,
            "tasks": [t.to_dict() for t in tasks],
            "results": [r.to_dict() for r in results],
        }


# ========== 预定义的修复函数 ==========

class CommonFixes:
    """常用修复函数集合"""

    @staticmethod
    def fix_import_type(content: str, task: FixTask) -> Optional[str]:
        """修复 import type 错误 (TS1361)"""
        # 将 import type { X } 改为 import { X }
        pattern = r"import\s+type\s+\{([^}]+)\}"

        def replace_import(match):
            imports = match.group(1)
            return f"import {{ {imports} }}"

        new_content = re.sub(pattern, replace_import, content)
        return new_content if new_content != content else None

    @staticmethod
    def fix_missing_optional_chain(content: str, task: FixTask) -> Optional[str]:
        """添加可选链操作符"""
        # 这个需要更复杂的分析，暂时返回 None
        return None

    @staticmethod
    def fix_prisma_import(content: str, task: FixTask) -> Optional[str]:
        """修复 Prisma 导入问题"""
        # 将 import { PrismaClient } 替换为 import { prisma }
        if "import { PrismaClient" in content and "prisma" not in content.lower():
            new_content = content.replace(
                "import { PrismaClient",
                "import { prisma"
            )
            # 同时替换 new PrismaClient()
            new_content = re.sub(
                r'const\s+\w+\s*=\s*new\s+PrismaClient\s*\(\s*\)',
                '// prisma 已通过 import 导入',
                new_content
            )
            return new_content
        return None

    @staticmethod
    def add_null_check(content: str, task: FixTask) -> Optional[str]:
        """添加空值检查"""
        if task.line_number:
            lines = content.split("\n")
            if 0 < task.line_number <= len(lines):
                line = lines[task.line_number - 1]
                # 简单的空值检查添加
                if ".digest" in line:
                    new_line = line.replace(".digest", "?.digest")
                    lines[task.line_number - 1] = new_line
                    return "\n".join(lines)
        return None


# ========== 批量修复生成器 ==========

class FixTaskGenerator:
    """从检查结果生成修复任务"""

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()

    def from_typescript_errors(self, errors: list[dict]) -> list[FixTask]:
        """从 TypeScript 错误生成修复任务"""
        tasks = []

        for error in errors:
            code = error.get("code", "")
            file_path = error.get("file", "")
            line = error.get("line", 0)
            message = error.get("message", "")

            # 根据错误代码确定优先级
            if code in ("TS2552", "TS2304", "TS2307"):
                priority = FixPriority.CRITICAL
            elif code in ("TS2339", "TS2345", "TS2322"):
                priority = FixPriority.HIGH
            else:
                priority = FixPriority.MEDIUM

            # 创建任务
            task = FixTask(
                id=f"ts_{code}_{file_path}:{line}",
                file_path=file_path,
                issue_type=f"typescript:{code}",
                description=message,
                priority=priority,
                line_number=line,
            )

            # 分配修复函数
            if code == "TS1361":
                task.fix_function = CommonFixes.fix_import_type
            elif code == "TS2552" and "prisma" in message.lower():
                task.fix_function = CommonFixes.fix_prisma_import

            tasks.append(task)

        return tasks

    def from_log_errors(self, errors: list[dict]) -> list[FixTask]:
        """从日志错误生成修复任务"""
        tasks = []

        for error in errors:
            category = error.get("category", "unknown")
            message = error.get("message", "")

            # 依赖问题
            if category == "dependency":
                if "sharp" in message.lower():
                    task = FixTask(
                        id="dep_sharp",
                        file_path="package.json",
                        issue_type="dependency:missing",
                        description="安装 sharp 图片处理库",
                        priority=FixPriority.CRITICAL,
                    )
                    tasks.append(task)

            # 空指针问题
            elif category == "runtime" and "空指针" in message:
                file_path = error.get("file", "")
                line = error.get("line", 0)
                if file_path:
                    task = FixTask(
                        id=f"runtime_null_{file_path}:{line}",
                        file_path=file_path,
                        issue_type="runtime:null_access",
                        description="添加空值检查",
                        priority=FixPriority.HIGH,
                        line_number=line,
                        fix_function=CommonFixes.add_null_check,
                    )
                    tasks.append(task)

        return tasks


async def main():
    """测试入口"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."

    fixer = ParallelFixer(project_path, max_workers=4)

    # 添加示例任务
    task1 = fixer.create_fix_task(
        file_path="test.ts",
        issue_type="typescript:TS2339",
        description="Property does not exist",
        priority=FixPriority.HIGH,
        old_code="obj.foo",
        new_code="obj?.foo",
    )

    fixer.add_task(task1)

    print("🔧 并行修复器测试")
    print(f"   最大工作线程: {fixer.max_workers}")

    # Dry run
    print("\n📋 Dry run:")
    results = fixer.run_parallel(dry_run=True)
    for r in results:
        print(f"   {r.task.file_path}: {r.message}")

    print("\n📊 摘要:")
    print(json.dumps(fixer.get_summary(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
