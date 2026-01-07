# ShenCha VS Code Extension

AI-powered code audit tool with multi-expert analysis.

## Features

- **Audit Current File**: Right-click or use command palette
- **Audit Project**: Full project analysis with HTML report
- **Auto Audit**: Optional auto-audit on save
- **Inline Diagnostics**: Issues shown in Problems panel

## Installation

```bash
cd vscode-extension
npm install
npm run compile
```

Then press F5 in VS Code to launch Extension Development Host.

## Requirements

- ShenCha CLI installed: `pip install shencha`
- Anthropic API key configured

## Commands

- `ShenCha: Audit Current File` - Audit the active file
- `ShenCha: Audit Project` - Audit entire workspace
- `ShenCha: Show Report` - Open latest HTML report

## Settings

- `shencha.apiKey` - Anthropic API key
- `shencha.autoAudit` - Enable auto-audit on save
- `shencha.language` - Report language (en/zh)
