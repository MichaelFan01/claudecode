<!--
Sync Impact Report:
- Version change: N/A → 1.0.0
- List of modified principles: All newly created
- Added sections: Core Principles (3), Code Standards, Governance
- Removed sections: None (template was unmodified)
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md - Constitution Check section updated
  - ⚠ .specify/templates/spec-template.md - No changes needed
  - ⚠ .specify/templates/tasks-template.md - No changes needed
- Follow-up TODOs: None
-->

# SDD Specify Constitution

## Core Principles

### I. Consistent Naming Convention

All code artifacts MUST follow standardized naming patterns to ensure readability and maintainability across the project.

- **File names**: MUST use kebab-case (e.g., `video-quality-check.py`, `audio-validate.py`)
- **Class/Component names**: MUST use PascalCase (e.g., `VideoQualityChecker`, `AudioConsistency`)
- **Function/Variable names**: MUST use camelCase (e.g., `checkVideoIntegrity`, `audioSampleRate`)

**Rationale**: Consistent naming eliminates cognitive friction when navigating the codebase and ensures that all contributors can immediately identify the purpose and type of any artifact.

### II. Data Lifecycle Traceability

All video data processing operations MUST be fully logged and traceable throughout their lifecycle.

- All video data processing functions MUST output logs to the project `./logs` folder
- Logs MUST include: file path, processing time, and operation action
- All data cleaning, filtering, or modification operations MUST be completely recorded in logs
- NO video data deletion or modification operation may be performed without logging

**Rationale**: For AI/ML and video generation projects, data provenance and auditability are critical for reproducibility, debugging, and quality assurance.

### III. Video Data Quality Validation

All video data reading operations MUST perform integrity and quality validation before processing.

- Video reading MUST verify: frame rate, total frame count, and file decoding integrity
- When audio is present, video reading MUST additionally verify: sample rate, channel count, and audio-video duration consistency

**Rationale**: Video large model training and inference pipelines are highly sensitive to data quality issues. Early validation prevents wasted computation and ensures model training stability.

## Code Standards

### Test-Optional Philosophy

Testing is RECOMMENDED for all new functionality but not strictly required.

- Tests SHOULD be included for critical path functionality, complex business logic, and areas with historical bug recurrence
- When tests are written, they MAY be written either before or after implementation at the implementer's discretion
- Test files SHOULD follow the same naming conventions as source files with appropriate test prefixes/suffixes

**Rationale**: This project prioritizes rapid iteration for video/AI research while maintaining the option to add tests for production-critical components.

## Governance

This constitution supersedes all other project practices and conventions. Amendments require documentation and must preserve backward compatibility unless explicitly approved as a breaking change.

### Amendment Procedure

1. Propose change with clear rationale and impact assessment
2. Update constitution file with new version following semantic versioning
3. Review and update all dependent templates as needed
4. Document changes in the Sync Impact Report at the top of the constitution

### Versioning Policy

- **MAJOR**: Backward incompatible governance changes, principle removals, or principle redefinitions
- **MINOR**: New principles added, existing principles materially expanded, or new governance sections
- **PATCH**: Clarifications, wording improvements, typo fixes, non-semantic refinements

### Compliance Review

All feature plans MUST pass a Constitution Check before Phase 0 research commences and again after Phase 1 design completes.

**Version**: 1.0.0 | **Ratified**: 2026-03-03 | **Last Amended**: 2026-03-03
