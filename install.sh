#!/bin/bash
# ShenCha Agent 一键安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/x-tavern/shencha-agent/main/install.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logo
print_logo() {
    echo -e "${CYAN}"
    echo '   _____ _                  _____ _           '
    echo '  / ____| |                / ____| |          '
    echo ' | (___ | |__   ___ _ __  | |    | |__   __ _ '
    echo '  \___ \| '\''_ \ / _ \ '\''_ \ | |    | '\''_ \ / _` |'
    echo '  ____) | | | |  __/ | | || |____| | | | (_| |'
    echo ' |_____/|_| |_|\___|_| |_| \_____|_| |_|\__,_|'
    echo ''
    echo -e "${PURPLE} AI-Powered Autonomous Code Audit Agent${NC}"
    echo ''
}

# 打印步骤
step() {
    echo -e "${BLUE}==>${NC} $1"
}

# 成功信息
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 警告信息
warn() {
    echo -e "${YELLOW}!${NC} $1"
}

# 错误信息
error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# 检查命令是否存在
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# 主安装流程
main() {
    print_logo

    echo -e "${CYAN}开始安装 ShenCha Agent...${NC}\n"

    # 1. 检查 Python
    step "检查 Python 环境..."
    if check_command python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc -l 2>/dev/null || python3 -c "print(1 if $PYTHON_VERSION >= 3.10 else 0)") == "1" ]]; then
            success "Python $PYTHON_VERSION ✓"
        else
            error "需要 Python 3.10+，当前版本: $PYTHON_VERSION"
        fi
    else
        error "未找到 Python3，请先安装 Python 3.10+"
    fi

    # 2. 检查 pip
    step "检查 pip..."
    if check_command pip3; then
        success "pip3 ✓"
    else
        warn "pip3 未找到，尝试安装..."
        python3 -m ensurepip --upgrade 2>/dev/null || error "无法安装 pip"
    fi

    # 3. 安装 ShenCha
    step "安装 ShenCha Agent..."
    pip3 install --upgrade shencha-agent 2>/dev/null || {
        warn "PyPI 安装失败，尝试从 GitHub 安装..."
        pip3 install git+https://github.com/x-tavern/shencha-agent.git || error "安装失败"
    }
    success "ShenCha Agent 安装完成"

    # 4. 验证安装
    step "验证安装..."
    if check_command shencha; then
        VERSION=$(shencha --version 2>/dev/null || echo "v2.1.0")
        success "shencha 命令可用 ($VERSION)"
    else
        warn "shencha 命令未在 PATH 中，可能需要重新打开终端"
    fi

    # 5. 配置向导
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 安装成功！${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "快速开始:"
    echo -e "  ${YELLOW}shencha${NC}              # 在当前目录启动交互模式"
    echo -e "  ${YELLOW}shencha ./my-project${NC} # 审计指定项目"
    echo -e "  ${YELLOW}shencha --help${NC}       # 查看帮助"
    echo ""
    echo -e "配置 API (可选):"
    echo -e "  ${YELLOW}shencha config${NC}       # 交互式配置向导"
    echo ""
    echo -e "文档: ${BLUE}https://github.com/x-tavern/shencha-agent${NC}"
    echo ""
}

main "$@"
