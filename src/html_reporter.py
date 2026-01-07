"""
HTML 报告生成器 - 美观的可视化报告
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .output import AuditResult, Issue


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShenCha 审计报告 - {project_name}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #e2e8f0;
            --muted: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        header {{
            text-align: center;
            padding: 3rem 0;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid #334155;
        }}
        .logo {{ font-size: 2.5rem; font-weight: bold; color: var(--primary); }}
        .subtitle {{ color: var(--muted); margin-top: 0.5rem; }}
        .score-card {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
        }}
        .score {{
            background: var(--card);
            padding: 2rem;
            border-radius: 1rem;
            text-align: center;
            min-width: 150px;
        }}
        .score-value {{
            font-size: 3rem;
            font-weight: bold;
        }}
        .score-label {{ color: var(--muted); font-size: 0.875rem; }}
        .score-good {{ color: var(--success); }}
        .score-warn {{ color: var(--warning); }}
        .score-bad {{ color: var(--danger); }}
        .section {{
            background: var(--card);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .issue {{
            background: rgba(0,0,0,0.2);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 3px solid var(--muted);
        }}
        .issue-critical {{ border-color: var(--danger); }}
        .issue-high {{ border-color: var(--warning); }}
        .issue-medium {{ border-color: var(--primary); }}
        .issue-low {{ border-color: var(--muted); }}
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .issue-file {{ font-family: monospace; color: var(--primary); }}
        .issue-severity {{
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .severity-critical {{ background: var(--danger); }}
        .severity-high {{ background: var(--warning); color: #000; }}
        .severity-medium {{ background: var(--primary); }}
        .severity-low {{ background: #475569; }}
        .issue-message {{ margin-top: 0.5rem; }}
        .issue-suggestion {{ color: var(--muted); font-size: 0.875rem; margin-top: 0.5rem; }}
        .chart-container {{ height: 200px; margin: 1rem 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: var(--muted); font-weight: 500; }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
        }}
        .badge-success {{ background: var(--success); }}
        .badge-warning {{ background: var(--warning); color: #000; }}
        .badge-danger {{ background: var(--danger); }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--muted);
            font-size: 0.875rem;
        }}
        @media (max-width: 768px) {{
            .score-card {{ flex-direction: column; align-items: center; }}
            .container {{ padding: 1rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="logo">🔍 ShenCha</div>
        <div class="subtitle">AI 代码审计报告</div>
    </header>

    <div class="container">
        <div class="score-card">
            <div class="score">
                <div class="score-value {score_class}">{score}</div>
                <div class="score-label">代码评分</div>
            </div>
            <div class="score">
                <div class="score-value">{total_files}</div>
                <div class="score-label">扫描文件</div>
            </div>
            <div class="score">
                <div class="score-value {issues_class}">{total_issues}</div>
                <div class="score-label">发现问题</div>
            </div>
            <div class="score">
                <div class="score-value {critical_class}">{critical_issues}</div>
                <div class="score-label">严重问题</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">📊 问题分布</div>
            <table>
                <tr>
                    <th>类别</th>
                    <th>数量</th>
                    <th>占比</th>
                </tr>
                {category_rows}
            </table>
        </div>

        <div class="section">
            <div class="section-title">🔴 问题列表</div>
            {issues_html}
        </div>

        {extra_sections}
    </div>

    <footer>
        <p>由 ShenCha v2.1 生成 | {timestamp}</p>
        <p>{project_path}</p>
    </footer>
</body>
</html>'''


class HTMLReporter:
    """HTML 报告生成器"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.report_dir = project_path / ".shencha" / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        result: AuditResult,
        extra_data: Optional[Dict[str, Any]] = None,
        lang: str = "zh"
    ) -> Path:
        """生成 HTML 报告"""
        # 计算统计
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_category = {}

        for issue in result.issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        # 生成问题 HTML
        issues_html = self._generate_issues_html(result.issues)

        # 生成类别行
        category_rows = ""
        total = len(result.issues) or 1
        for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            pct = count / total * 100
            category_rows += f"<tr><td>{cat}</td><td>{count}</td><td>{pct:.0f}%</td></tr>"

        # 额外部分
        extra_sections = ""
        if extra_data:
            if "vulnerabilities" in extra_data:
                extra_sections += self._generate_vuln_section(extra_data["vulnerabilities"])
            if "coverage" in extra_data:
                extra_sections += self._generate_coverage_section(extra_data["coverage"])
            if "performance" in extra_data:
                extra_sections += self._generate_perf_section(extra_data["performance"])

        # 填充模板
        html = HTML_TEMPLATE.format(
            lang=lang,
            project_name=self.project_path.name,
            score=result.score,
            score_class="score-good" if result.score >= 80 else "score-warn" if result.score >= 60 else "score-bad",
            total_files=result.total_files,
            total_issues=len(result.issues),
            issues_class="score-good" if len(result.issues) == 0 else "score-warn" if len(result.issues) < 10 else "score-bad",
            critical_issues=by_severity["critical"],
            critical_class="score-good" if by_severity["critical"] == 0 else "score-bad",
            category_rows=category_rows or "<tr><td colspan='3'>无数据</td></tr>",
            issues_html=issues_html or "<p>未发现问题 ✅</p>",
            extra_sections=extra_sections,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            project_path=str(self.project_path),
        )

        # 保存
        report_file = self.report_dir / f"report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        report_file.write_text(html, encoding="utf-8")

        return report_file

    def _generate_issues_html(self, issues: List[Issue]) -> str:
        """生成问题列表 HTML"""
        if not issues:
            return ""

        html = ""
        for issue in issues[:50]:
            html += f'''
            <div class="issue issue-{issue.severity}">
                <div class="issue-header">
                    <span class="issue-file">{issue.file}:{issue.line}</span>
                    <span class="issue-severity severity-{issue.severity}">{issue.severity.upper()}</span>
                </div>
                <div class="issue-message">{issue.message}</div>
                {f'<div class="issue-suggestion">💡 {issue.suggestion}</div>' if issue.suggestion else ''}
            </div>
            '''
        return html

    def _generate_vuln_section(self, data: Dict) -> str:
        """生成漏洞部分"""
        html = '<div class="section"><div class="section-title">🔒 依赖漏洞</div>'
        for scanner, result in data.items():
            if result.get("error"):
                html += f"<p>⚠️ {scanner}: {result['error']}</p>"
            elif result.get("total", 0) == 0:
                html += f"<p>✅ {scanner}: 未发现漏洞</p>"
            else:
                html += f"<p>🔴 {scanner}: {result['total']} 个漏洞 ({result.get('critical', 0)} 严重)</p>"
        html += "</div>"
        return html

    def _generate_coverage_section(self, data: Dict) -> str:
        """生成覆盖率部分"""
        cov = data.get("line_coverage", 0)
        icon = "🟢" if cov >= 80 else "🟡" if cov >= 60 else "🔴"
        return f'''
        <div class="section">
            <div class="section-title">🧪 测试覆盖率</div>
            <p>{icon} 行覆盖率: {cov:.1f}%</p>
            <p>语句: {data.get("covered_statements", 0)}/{data.get("total_statements", 0)}</p>
        </div>
        '''

    def _generate_perf_section(self, data: Dict) -> str:
        """生成性能部分"""
        return f'''
        <div class="section">
            <div class="section-title">⚡ 性能分析</div>
            <p>复杂度问题: {data.get("complexity_count", 0)}</p>
            <p>N+1 查询风险: {data.get("n_plus_one_count", 0)}</p>
            <p>Bundle 大小: {data.get("total_bundle_size", 0) / 1024:.1f} KB</p>
        </div>
        '''
