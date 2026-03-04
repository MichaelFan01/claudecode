# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is a multi-project workspace containing the following projects:

1. **sdd-specify** - A specification framework for software design documents with a focus on video generation model and AI/ML development.
2. **skyclipper** - A video processing and analysis project using PyTorch, vLLM, Transformers, and other ML libraries.

## Key Projects

### sdd-specify
**Location:** `/Users/fanmingyuan/Desktop/vibe-coding/claudecode/sdd-specify`
**Purpose:** A specification framework for video/AI projects with strict data quality and traceability requirements.

**Key Features:**
- Constitution-driven development
- Feature specifications in spec.md
- Implementation plans in plan.md
- Task lists in tasks.md

**Common Commands:**
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

### skyclipper
**Location:** `/Users/fanmingyuan/Desktop/vibe-coding/claudecode/skyclipper`
**Purpose:** A video processing and analysis project with advanced ML capabilities.

**Active Technologies:**
- Python 3.8+
- PyTorch, vLLM, Transformers
- TransNetV2-PyTorch, Decord, Pandas

**Key Directories:**
```text
src/
tests/
```

**Common Commands:**
```bash
cd src
pytest
ruff check .
```

## Code Standards

### Naming Conventions
- **Filenames:** kebab-case (e.g., `video-quality-check.py`, `audio-validate.py`)
- **Classes/Components:** PascalCase (e.g., `VideoQualityChecker`, `AudioConsistency`)
- **Functions/Variables:** camelCase (e.g., `checkVideoIntegrity`, `audioSampleRate`)

### Data Quality and Traceability (sdd-specify)
- All video data processing functions must log to the project's `./logs` folder
- Logs must include file path, processing time, and operation details
- All data cleaning, filtering, and modification operations must be fully logged
- No video data deletion/modification without logging

### Video Quality Validation (sdd-specify)
- Video reading must validate: frame rate, total frames, file decoding integrity
- When audio is present, additionally validate: sample rate, number of channels, audio-video duration consistency

### Testing Philosophy
- Tests are recommended for critical path functionality but not mandatory
- Tests can be written before or after implementation, at the implementer's discretion
- Test files should follow the same naming conventions as source files

## Project Navigation

To work on a specific project, navigate to its directory first:
```bash
# For sdd-specify
cd sdd-specify

# For skyclipper
cd skyclipper
```

Each project has its own `CLAUDE.md` file with more specific guidance.

## GitLab CI/CD

This repository uses GitLab CI/CD to automate updates to `CLAUDE.md` from merge request reviews. The configuration can be found in `.gitlab-ci.yml`.

To request updates to `CLAUDE.md` during MR review, add a comment mentioning `@claude` and including `CLAUDE.md` in the comment text.