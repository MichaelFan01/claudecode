# Research: 代码库重构

**Feature**: 001-refactor-codebase | **Date**: 2026-03-04

## 1. Python 项目模块化最佳实践

### Decision
采用清晰的包结构，分离核心逻辑、CLI 入口和工具函数。

### Rationale
- 提高代码可维护性和可测试性
- 便于单独模块开发和调试
- 符合 Python 社区标准实践

### Alternatives considered
- **保持单文件结构**: 简单但不利于测试和维护，已否决
- **按功能拆分模块**: 过度拆分，增加复杂度，已否决

---

## 2. 测试框架选择

### Decision
使用 pytest 作为主要测试框架。

### Rationale
- 简洁的断言语法
- 强大的 fixture 系统
- 丰富的插件生态
- 良好的集成测试支持

### Alternatives considered
- **unittest**: Python 标准库但语法较冗长，已否决
- **nose2**: 生态不如 pytest 活跃，已否决

---

## 3. 向后兼容性策略

### Decision
保留原有脚本作为薄包装层，内部调用新模块。

### Rationale
- 确保现有用户无需修改使用方式
- 逐步迁移风险更低
- 可以分阶段验证重构正确性

### Alternatives considered
- **完全重写并废弃旧脚本**: 风险太高，已否决
- **新旧脚本并存**: 用户困惑，已否决

---

## 4. HTML 流程图技术方案

### Decision
使用原生 HTML + CSS + JavaScript + Mermaid.js 创建交互式流程图。

### Rationale
- 无需额外构建工具
- 易于维护和修改
- Mermaid.js 提供声明式流程图语法
- 支持节点点击交互

### Alternatives considered
- **静态 PNG/SVG**: 无法交互，已否决
- **Graphviz**: 需要额外安装，已否决
- **React/复杂框架**: 过度设计，已否决

---

## 5. 代码重复检测方法

### Decision
使用人工审查 + 抽取公共函数的方式。

### Rationale
- 项目规模适中，人工审查可行
- 可以结合业务逻辑判断真正的重复
- 避免过度抽象

### Alternatives considered
- **使用自动化工具 (radon/pylint)**: 可以作为辅助，但主要依靠人工，已否决
