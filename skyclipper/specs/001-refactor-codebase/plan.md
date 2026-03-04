# Implementation Plan: 代码库重构

**Branch**: `001-refactor-codebase` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-refactor-codebase/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

重构整个 SkyClipper 工程模块，包括：
1. 建立清晰的模块化代码结构
2. 为核心功能添加完整测试覆盖
3. 简化代码逻辑，移除冗余代码
4. 创建 HTML 流程图可视化主流程
5. 完善 README 文档使其易于上手

技术方法：采用模块化重构策略，保持功能不变的前提下逐步拆分现有代码到独立模块。

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: PyTorch, vLLM, Transformers, TransNetV2-PyTorch, Decord, Pandas
**Storage**: JSONL files, CSV files
**Testing**: pytest
**Target Platform**: Linux server with CUDA GPUs
**Project Type**: CLI tool / video processing pipeline
**Performance Goals**: Maintain existing processing throughput
**Constraints**: Must maintain backward compatibility with existing input/output formats
**Scale/Scope**: 3 main Python scripts (~1500+ LOC total)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Naming Conventions**: All new files follow kebab-case, components use PascalCase, functions use camelCase
- [x] **Compliance**: No violations of constitution principles identified


## Project Structure

### Documentation (this feature)

```text
specs/001-refactor-codebase/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── core/                      # 核心模块
│   ├── video-processor.py      # 视频处理核心类
│   ├── scene-detector.py     # TransNet场景检测
│   ├── action-recognizer.py # Qwen3-VL动作识别
│   └── result-merger.py      # 结果合并与解析
│   └── visualizer.py        # 可视化工具
├── cli/                       # 命令行入口
│   ├── process-videos.py    # 视频处理主入口
│   ├── merge-results.py     # 结果合并入口
│   └── visualize.py        # 可视化入口
└── utils/                     # 工具函数
    ├── time-utils.py       # 时间处理工具
    ├── xml-parser.py       # XML解析工具
    └── json-utils.py       # JSON工具
    └── video-utils.py      # 视频工具

tests/
├── unit/                     # 单元测试
│   ├── test-time-utils.py
│   ├── test-xml-parser.py
│   └── test-json-utils.py
├── integration/              # 集成测试
│   ├── test-video-processor.py
│   ├── test-scene-detector.py
│   └── test-result-merger.py
│   └── test-visualizer.py
└── fixtures/                 # 测试数据

docs/
├── flow-diagram.html       # 主流程HTML流程图
└── architecture.md       # 架构说明

data/                        # 数据目录
    └── prompt-templates/   # 提示词模板

# 保留原有脚本（向后兼容）
├── vllm-offline-qwen3-vl-parallel.py  # 原始主脚本（调用新模块）
├── merge-and-parse-clips.py              # 原始合并脚本（调用新模块）
├── parser-vis.py                        # 原始可视化脚本（调用新模块）
├── run-singlenode.sh
├── run-multinode.sh
└── README.md
```

**Structure Decision**: 采用单项目结构，将现有功能按模块化到 src/ 目录下，保持根目录的原始脚本作为向后兼容的入口点。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
