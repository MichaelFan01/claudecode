# Tasks: 视频质量验证模块

**Input**: Design documents from `/specs/001-video-quality-validation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are optional per constitution - recommended but not required for this feature

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan
- [x] T002 Initialize Python project with dependencies (opencv-python, click, ffmpeg-python)
- [x] T003 [P] Create logs directory with .gitkeep in logs/.gitkeep
- [x] T004 [P] Create .gitignore for Python project and logs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create data models in src/video_quality_validator/models.py
- [x] T006 [P] Create logging utilities in src/video_quality_validator/utils.py
- [x] T007 [P] Create package __init__.py in src/video_quality_validator/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 验证单个视频文件基本属性 (Priority: P1) 🎯 MVP

**Goal**: 实现单个视频文件的基本属性验证（帧率、总帧数、解码完整性），作为MVP功能交付

**Independent Test**: 可以通过提供一个有效的视频文件和一个损坏的视频文件，验证模块能正确识别并报告验证结果

### Implementation for User Story 1

- [x] T008 [P] [US1] Create VideoQualityValidator core class structure in src/video_quality_validator/core.py
- [x] T009 [P] [US1] Implement video frame rate validation in src/video_quality_validator/core.py
- [x] T010 [P] [US1] Implement video total frames validation in src/video_quality_validator/core.py
- [x] T011 [US1] Implement video decode integrity validation in src/video_quality_validator/core.py
- [x] T012 [US1] Add logging for all validation operations (follows constitution Principle II)
- [x] T013 [US1] Create VideoValidationResult builder methods in src/video_quality_validator/core.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 验证包含音频的视频文件 (Priority: P2)

**Goal**: 扩展验证功能以支持音频属性验证和音视频一致性检查

**Independent Test**: 可以通过提供一个音视频同步的文件和一个音视频时长不一致的文件，验证模块能正确识别差异

### Implementation for User Story 2

- [x] T014 [P] [US2] Add audio detection capability in src/video_quality_validator/core.py
- [x] T015 [P] [US2] Implement audio sample rate validation in src/video_quality_validator/core.py
- [x] T016 [P] [US2] Implement audio channel count validation in src/video_quality_validator/core.py
- [x] T017 [US2] Implement video duration extraction in src/video_quality_validator/core.py
- [x] T018 [US2] Implement audio duration extraction in src/video_quality_validator/core.py
- [x] T019 [US2] Implement audio-video sync validation in src/video_quality_validator/core.py
- [x] T020 [US2] Add logging for audio validation operations
- [x] T021 [US2] Handle partial validation status (PASS/FAIL/PARTIAL) correctly

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 批量验证多个视频文件 (Priority: P3)

**Goal**: 实现批量验证功能，支持目录扫描和汇总报告生成

**Independent Test**: 可以通过提供包含多个有效和无效视频的目录，验证模块能批量处理并生成汇总报告

### Implementation for User Story 3

- [x] T022 [P] [US3] Implement directory scanning for video files in src/video_quality_validator/core.py
- [x] T023 [P] [US3] Add recursive scanning option in src/video_quality_validator/core.py
- [x] T024 [US3] Implement BatchValidationReport generation in src/video_quality_validator/core.py
- [x] T025 [US3] Implement failure summary statistics in src/video_quality_validator/core.py
- [x] T026 [US3] Add parallel validation support (optional, default=1)
- [x] T027 [US3] Add logging for batch validation operations
- [x] T028 [US3] Create batch validation progress tracking

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: CLI Interface & Polish

**Purpose**: Command line interface and cross-cutting improvements

- [x] T029 [P] Create Click CLI main command in src/video_quality_validator/cli.py
- [x] T030 [P] Add 'validate' subcommand with options in src/video_quality_validator/cli.py
- [x] T031 [P] Add 'batch-validate' subcommand with options in src/video_quality_validator/cli.py
- [x] T032 [P] Implement text output formatting in src/video_quality_validator/cli.py
- [x] T033 [P] Implement JSON output formatting in src/video_quality_validator/cli.py
- [x] T034 Add output file writing capability
- [x] T035 [P] Create README.md with installation and usage instructions
- [x] T036 Add setup.py or pyproject.toml for package installation
- [x] T037 Run quickstart.md validation to ensure user can complete flow in <5 minutes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **CLI & Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 core classes but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on US1 core validation but independently testable

### Within Each User Story

- Models before services
- Core validation before CLI integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Within User Story 1, tasks T008-T010 marked [P] can run in parallel
- Within User Story 2, tasks T014-T016 marked [P] can run in parallel
- Within User Story 3, tasks T022-T023 marked [P] can run in parallel
- Within CLI phase, tasks T029-T033 marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch core class structure and basic validations together:
Task: "Create VideoQualityValidator core class structure in src/video_quality_validator/core.py"
Task: "Implement video frame rate validation in src/video_quality_validator/core.py"
Task: "Implement video total frames validation in src/video_quality_validator/core.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - MVP delivers core video validation!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add CLI Interface → Full feature complete
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (MVP)
   - Developer B: User Story 2 (Audio validation)
   - Developer C: User Story 3 (Batch validation)
3. Stories complete and integrate independently

---

## Task Summary

- **Total Tasks**: 37 tasks
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 3 tasks
- **Phase 3 (US1 - MVP)**: 6 tasks
- **Phase 4 (US2 - Audio)**: 8 tasks
- **Phase 5 (US3 - Batch)**: 7 tasks
- **Phase 6 (CLI & Polish)**: 9 tasks

- **Parallel Opportunities**: 17 tasks marked [P]
- **Independent Testable Increments**: 3 user stories + CLI

**MVP Scope**: Just User Story 1 + minimal CLI - delivers core video validation capability

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All tasks follow constitution naming conventions: kebab-case files, PascalCase classes, camelCase functions/variables
- All video data processing includes logging to ./logs folder (constitution Principle II)
- All video reading includes validation checks (constitution Principle III)
