---

description: "Task list for codebase refactoring"
---

# Tasks: 代码库重构

**Input**: Design documents from `/specs/001-refactor-codebase/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly requested in the feature specification - will include test tasks
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure as defined in plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create directory structure (src/, tests/, docs/, data/)
- [X] T002 Create __init__.py files in all package directories
- [X] T003 [P] Create pytest configuration in pytest.ini
- [X] T004 [P] Move prompt templates to data/prompt-templates/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create src/utils/time-utils.py with time conversion functions
- [X] T006 [P] Create src/utils/xml-parser.py with XML parsing functions
- [X] T007 [P] Create src/utils/json-utils.py with JSON utility functions
- [X] T008 [P] Create src/utils/video-utils.py with video processing helpers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 清晰的工程结构 (Priority: P1) 🎯 MVP

**Goal**: Establish clear modular code structure following constitutional naming conventions

**Independent Test**: Verify project directory tree exists, new developer can locate target modules within 5 minutes

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Test utils module imports in tests/unit/test-utils-import.py
- [X] T010 [P] [US1] Test core module structure in tests/unit/test-core-structure.py

### Implementation for User Story 1

- [X] T011 [P] [US1] Create src/core/scene-detector.py with TransNetWorker class
- [X] T012 [P] [US1] Create src/core/action-recognizer.py with Qwen3-VL inference logic
- [X] T013 [P] [US1] Create src/core/video-processor.py with main pipeline orchestration
- [X] T014 [P] [US1] Create src/core/result-merger.py with result parsing and merging logic
- [X] T015 [P] [US1] Create src/core/visualizer.py with HTML generation logic
- [X] T016 [P] [US1] Create src/cli/process_videos.py as new CLI entry point
- [X] T017 [P] [US1] Create src/cli/merge_results.py as new CLI entry point
- [X] T018 [P] [US1] Create src/cli/visualize.py as new CLI entry point
- [X] T019 [US1] Update vllm_offline_qwen3_vl_parallel.py to import from new modules
- [X] T020 [US1] Update merge_and_parse_clips.py to import from new modules
- [X] T021 [US1] Update parser_vis.py to import from new modules

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 完整的测试覆盖 (Priority: P1) 🎯 MVP

**Goal**: Add comprehensive test coverage for all core modules

**Independent Test**: Run pytest and verify test coverage report shows 80%+ coverage for core modules

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T022 [P] [US2] Unit tests for time-utils in tests/unit/test-time-utils.py
- [X] T023 [P] [US2] Unit tests for xml-parser in tests/unit/test-xml-parser.py
- [X] T024 [P] [US2] Unit tests for json-utils in tests/unit/test-json-utils.py
- [X] T025 [P] [US2] Unit tests for scene-detector in tests/unit/test-scene-detector.py
- [X] T026 [P] [US2] Unit tests for result-merger in tests/unit/test-result-merger.py
- [X] T027 [P] [US2] Integration tests for video-processor in tests/integration/test-video-processor.py
- [X] T028 [P] [US2] Integration tests for full pipeline in tests/integration/test-full-pipeline.py

### Implementation for User Story 2

- [X] T029 [P] [US2] Create test fixtures in tests/fixtures/sample-data.py
- [X] T030 [P] [US2] Create mock video test data in tests/fixtures/mock-videos.py
- [X] T031 [P] [US2] Add test coverage configuration in .coveragerc
- [X] T032 [US2] Run test coverage and verify 80%+ coverage
- [X] T033 [US2] Fix any failing tests and address coverage gaps

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 简洁清晰的代码逻辑 (Priority: P2)

**Goal**: Simplify code logic, remove redundancy, keep functions under 50 lines

**Independent Test**: Code review shows average function length under 40 lines, no obvious redundancy

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T034 [P] [US3] Add cyclomatic complexity check in tests/quality/test-complexity.py

### Implementation for User Story 3

- [X] T035 [P] [US3] Extract duplicate XML parsing logic from both scripts to xml-parser.py
- [X] T036 [P] [US3] Extract duplicate time conversion logic from both scripts to time-utils.py
- [X] T037 [P] [US3] Simplify TransNetWorker class in scene-detector.py
- [X] T038 [P] [US3] Simplify result merging logic in result-merger.py
- [X] T039 [P] [US3] Split large functions in video-processor.py into smaller functions
- [X] T040 [US3] Remove unused imports and dead code from all modules
- [X] T041 [US3] Add docstrings to all public classes and functions
- [X] T042 [US3] Verify function lengths - refactor any over 50 lines

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - 可视化流程图 (Priority: P2)

**Goal**: Create interactive HTML flowchart showing main processing pipeline

**Independent Test**: Open flow-diagram.html in browser, verify all nodes are clickable and show details

### Tests for User Story 4 (OPTIONAL)

### Implementation for User Story 4

- [X] T043 [P] [US4] Create docs/flow-diagram.html with Mermaid.js integration
- [X] T044 [P] [US4] Define main processing flow diagram (TransNet → Queue → Qwen3-VL → Output)
- [X] T045 [P] [US4] Add node click interactions showing detailed descriptions
- [X] T046 [US4] Test flow-diagram.html in Chrome, Firefox, and Safari browsers
- [X] T047 [US4] Add flow diagram link to README.md

---

## Phase 7: User Story 5 - 清晰的README文档 (Priority: P3)

**Goal**: Update README to be clear and easy to follow for new users

**Independent Test**: New user can follow README steps and run project within 10 minutes

### Tests for User Story 5 (OPTIONAL)

### Implementation for User Story 5

- [X] T048 [P] [US5] Restructure README with clear sections (Quickstart, Configuration, Examples)
- [X] T049 [P] [US5] Add step-by-step Quickstart guide with exact commands
- [X] T050 [P] [US5] Add comprehensive configuration parameter documentation
- [X] T051 [P] [US5] Add troubleshooting section for common issues
- [X] T052 [US5] Add architecture diagram reference to flow-diagram.html
- [X] T053 [US5] Update directory structure section to show new modular layout

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T054 [P] Create architecture overview in docs/architecture.md
- [X] T055 Run full pipeline verification with existing input data
- [X] T056 Verify backward compatibility - old scripts still work
- [X] T057 Final code review and cleanup
- [X] T058 Run quickstart.md validation with fresh environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after US1 completes - Requires modular structure from US1
- **User Story 3 (P2)**: Can start after US1 completes - Requires code to simplify
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent of other stories
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Can be written in parallel

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US4 can start in parallel
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members once dependencies are met

---

## Parallel Example: User Story 1

```bash
# Launch all utility module tasks together:
Task: "Create src/utils/time-utils.py with time conversion functions"
Task: "Create src/utils/xml-parser.py with XML parsing functions"
Task: "Create src/utils/json-utils.py with JSON utility functions"
Task: "Create src/utils/video-utils.py with video processing helpers"

# Once utils are done, launch core module tasks together:
Task: "Create src/core/scene-detector.py with TransNetWorker class"
Task: "Create src/core/action-recognizer.py with Qwen3-VL inference logic"
Task: "Create src/core/result-merger.py with result parsing and merging logic"
Task: "Create src/core/visualizer.py with HTML generation logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Modular Structure)
   - Developer B: User Story 4 (Flow Diagram) in parallel
3. Once US1 is done:
   - Developer A: User Story 2 (Test Coverage)
   - Developer B: User Story 3 (Code Simplification)
   - Developer C: User Story 5 (README)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Total Tasks**: 58 tasks across 8 phases
