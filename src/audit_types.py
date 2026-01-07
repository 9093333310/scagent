"""
扩展审计能力 - 新增审计类型
"""

# 可审计的内容类型
AUDIT_CAPABILITIES = {
    # ===== 前端 =====
    "frontend": {
        "typescript": "TypeScript 类型检查、类型安全",
        "react": "React 组件结构、Hooks 使用、性能优化",
        "vue": "Vue 组件、Composition API、响应式",
        "css": "CSS 规范、命名、响应式设计",
        "accessibility": "无障碍性 (WCAG)、屏幕阅读器支持",
        "bundle": "Bundle 大小、Tree Shaking、代码分割",
        "i18n": "国际化完整性、硬编码字符串",
    },

    # ===== 后端 =====
    "backend": {
        "python": "Python 代码质量、PEP8、类型提示",
        "nodejs": "Node.js 最佳实践、异步处理",
        "api_design": "REST/GraphQL 设计、版本控制、错误处理",
        "database": "SQL 注入、N+1 查询、索引优化",
        "authentication": "认证安全、JWT、Session 管理",
        "authorization": "权限控制、RBAC、资源访问",
    },

    # ===== 安全 =====
    "security": {
        "injection": "SQL/命令/XSS 注入",
        "secrets": "敏感信息泄露、硬编码密钥",
        "dependencies": "依赖漏洞 (npm audit, pip-audit)",
        "crypto": "加密算法、密钥管理",
        "input_validation": "输入验证、边界检查",
        "path_traversal": "路径遍历、文件访问",
    },

    # ===== 架构 =====
    "architecture": {
        "solid": "SOLID 原则遵循",
        "patterns": "设计模式应用",
        "coupling": "模块耦合度",
        "complexity": "圈复杂度、认知复杂度",
        "dependencies": "依赖管理、循环依赖",
        "layers": "分层架构、边界清晰度",
    },

    # ===== 性能 =====
    "performance": {
        "memory": "内存泄漏、大对象",
        "cpu": "CPU 热点、算法效率",
        "io": "I/O 阻塞、异步优化",
        "caching": "缓存策略、缓存失效",
        "database": "慢查询、索引使用",
        "network": "请求优化、并发控制",
    },

    # ===== 测试 =====
    "testing": {
        "coverage": "测试覆盖率",
        "unit": "单元测试质量",
        "integration": "集成测试",
        "e2e": "端到端测试",
        "mocking": "Mock 使用",
        "assertions": "断言质量",
    },

    # ===== DevOps =====
    "devops": {
        "docker": "Dockerfile 最佳实践、镜像安全",
        "kubernetes": "K8s 配置、资源限制",
        "ci_cd": "Pipeline 安全、Secret 管理",
        "monitoring": "日志、指标、告警",
        "infrastructure": "IaC 安全、配置管理",
    },

    # ===== 文档 =====
    "documentation": {
        "readme": "README 完整性",
        "api_docs": "API 文档",
        "comments": "代码注释",
        "changelog": "变更日志",
        "architecture": "架构文档",
    },
}

# 按项目类型推荐的审计组合
PROJECT_PRESETS = {
    "react_app": ["frontend.typescript", "frontend.react", "frontend.accessibility", "security.injection", "testing.coverage"],
    "vue_app": ["frontend.typescript", "frontend.vue", "frontend.accessibility", "security.injection", "testing.coverage"],
    "python_api": ["backend.python", "backend.api_design", "backend.database", "security.injection", "security.authentication"],
    "nodejs_api": ["backend.nodejs", "backend.api_design", "backend.database", "security.injection", "security.authentication"],
    "fullstack": ["frontend.typescript", "backend.api_design", "security.injection", "architecture.solid", "testing.coverage"],
    "microservices": ["architecture.coupling", "devops.docker", "devops.kubernetes", "performance.network", "security.secrets"],
}

# 快速审计命令
QUICK_COMMANDS = {
    "security": "安全审计 - 检查注入、泄露、漏洞",
    "performance": "性能审计 - 检查内存、CPU、I/O",
    "quality": "质量审计 - 检查代码规范、复杂度",
    "full": "全面审计 - 所有维度",
}
