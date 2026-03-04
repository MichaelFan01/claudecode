<!--
SYNC IMPACT REPORT
==================
Version change: [NEW PROJECT] → 1.0.0
Added principles:
  - I. Naming Conventions (NEW)
Added sections:
  - Code Style Guidelines (NEW)
Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Constitution Check updated
  ⚠️ .specify/templates/spec-template.md - No updates needed
  ⚠️ .specify/templates/tasks-template.md - No updates needed
Follow-up TODOs: None
-->

# SkyClipper Constitution

## Core Principles

### I. Naming Conventions (NON-NEGOTIABLE)

**Rules:**
- **文件名 (File names)**: MUST use kebab-case (lowercase with hyphens, e.g., `video-parser.py`, `merge-and-parse-clips.py`)
- **组件名 (Component names)**: MUST use PascalCase (capitalized with no separators, e.g., `VideoProcessor`, `SceneDetector`)
- **函数名 (Function names)**: MUST use camelCase (lowercase start, capitalized subsequent words, e.g., `parseVideoClip()`, `mergeScenes()`)

**Rationale**: Consistent naming improves code readability, reduces cognitive load when switching between files, and ensures the codebase follows industry-standard conventions for its language/stack.

## Code Style Guidelines

This section captures additional style and formatting expectations for the project.

## Governance

- This constitution supersedes all other project-specific style guides.
- Amendments require documentation and version increment per semantic versioning rules.
- All code reviews MUST verify compliance with naming conventions outlined in Principle I.
- Use README.md for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-03-04 | **Last Amended**: 2026-03-04
