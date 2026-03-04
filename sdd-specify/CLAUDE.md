# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is the SDD Specify project, a framework for software design document specification with a focus on video generation model and AI/ML development.

## Key Projects

**SDD Specify**
**Location:** /Users/fanmingyuan/Desktop/vibe-coding/claudecode/sdd-specify
**Purpose:** A specification framework for video/AI projects with strict data quality and traceability requirements

## Common Commands

```bash
# Create/update project constitution
/speckit.constitution

# Create feature specification
/speckit.specify

# Create implementation plan
/speckit.plan

# Generate tasks
/speckit.tasks
```

## Code Architecture

This project uses the speckit specification framework with:
- Constitution-driven development
- Feature specifications in spec.md
- Implementation plans in plan.md
- Task lists in tasks.md

## Configuration

- **Constitution:** `.specify/memory/constitution.md` - Project governance and principles
- **Templates:** `.specify/templates/` - Templates for specs, plans, and tasks

## Key Files

- `.specify/memory/constitution.md` - Project constitution (governing principles)
- `CLAUDE.md` - This file (runtime guidance for Claude Code)

## Code Standards

See `.specify/memory/constitution.md` for the full project constitution.

### 0. 命名规范（代码层强制遵守）
- 文件名：统一使用 kebab-case（如 video-quality-check.py、audio-validate.py）
- 类/组件名：统一使用 PascalCase（如 VideoQualityChecker、AudioConsistency）
- 函数/变量名：统一使用 camelCase（如 checkVideoIntegrity、audioSampleRate）

### 1. 数据全生命周期可追溯规范
- 所有视频数据处理函数，必须将日志输出至项目 ./logs 文件夹，日志需包含文件路径、处理时间、操作动作
- 数据清洗、过滤、修改等所有变更操作，均需在上述日志中完整记录
- 禁止执行任何无日志记录的视频数据删改操作

### 2. 视频大模型数据质量强校验规范
- 视频读取必须校验：帧率、总帧数、文件解码完整性
- 包含音频时，额外校验：采样率、声道数、音视频时长一致性

### 3. 测试哲学（Test-Optional）
- 测试推荐用于关键路径功能，但不强制要求
- 测试可在实现前或实现后编写，由实现者自行决定
- 测试文件应遵循与源文件相同的命名约定
