# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Install
pip install -e .

# Run
shencha              # Interactive mode
shencha -q           # Quick audit
shencha config       # Setup wizard
shencha doctor       # Check environment
```

## Project Structure (v2.1)

```
src/
├── cli.py              # 🎯 Main CLI (Rich-based, user-friendly)
├── config.py           # ⚙️ Configuration management
├── errors.py           # ❌ Error handling with friendly messages
├── output.py           # 🎨 Beautiful terminal output (Rich)
├── security.py         # 🔒 Input validation, path protection
│
├── agent/              # 🤖 Core Agent (modular)
│   ├── core.py         # Agent orchestration
│   ├── hooks.py        # Event hooks
│   └── tools/          # MCP Tools
│       ├── analysis.py # analyze_file, scan_project
│       ├── fix.py      # propose_fix, apply_fix
│       ├── expert.py   # expert_*_audit (UI, Arch, Logic)
│       ├── knowledge_tools.py
│       └── github_tools.py
│
├── integrations/       # 🔗 Third-party
│   └── github.py       # GitHub PR review
│
├── cache/              # 💾 Caching
│   └── file_cache.py   # Content-hash based
│
├── utils/              # 🛠️ Utilities
│   ├── async_io.py     # Async file operations
│   └── logger.py       # Unified logging
│
├── knowledge.py        # 📚 Knowledge base
├── reporters.py        # 📊 Report generation
├── frontend_checker.py # TypeScript/ESLint
├── log_analyzer.py     # PM2 log analysis
└── parallel_fixer.py   # Concurrent fixes
```

## Key Commands

```bash
# Development
pip install -e ".[dev]"
pytest --cov=src
black src/ && isort src/

# CLI
shencha                    # Interactive audit
shencha ./project -q       # Quick audit
shencha pr owner/repo 123  # PR review
shencha config             # Configuration wizard
shencha doctor             # Environment check
```

## Environment Variables

```bash
SHENCHA_API_KEY=<key>      # Required: LLM API key
SHENCHA_LLM_URL=<url>      # Optional: Custom API endpoint
GITHUB_TOKEN=<token>       # Optional: For PR review
```

## Architecture Highlights

1. **User Experience First**: Rich-based CLI with progress bars, colors, and friendly errors
2. **Zero Config Start**: Works out of the box, `shencha config` for customization
3. **Security Built-in**: `SecurityValidator` for all file/command operations
4. **Modular Tools**: Each tool in separate file under `src/agent/tools/`
5. **Multi-Expert System**: UI, Architecture, Logic, Security experts
6. **GitHub Integration**: PR review with `shencha pr` command

## Adding New Features

1. **New Tool**: Add to `src/agent/tools/`, register in `__init__.py`
2. **New Command**: Add to `src/cli.py` using `@cli.command()`
3. **New Expert**: Add to `src/agent/tools/expert.py`
