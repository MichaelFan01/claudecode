# Data Model: SkyClipper

**Feature**: 001-refactor-codebase | **Date**: 2026-03-04

## Core Entities

### Video
Represents a single video file to be processed.

**Fields**:
- `video_id`: Unique identifier for the video (string)
- `video_path`: Absolute path to the video file (string)
- `fps`: Frames per second (float, optional)
- `duration`: Total duration in seconds (float, optional)
- `metadata`: Additional video metadata (dict, optional)

**Relationships**:
- Has many `Shot`s
- Has many `Scene`s

---

### Shot
Represents a single camera shot (raw clip) detected by TransNet.

**Fields**:
- `video_id`: Reference to parent video (string)
- `segment_id`: Index within video segments (integer)
- `clip_id`: Unique clip identifier (integer)
- `action_id`: Action category identifier (integer)
- `action_desc`: Description of the action (string, optional)
- `clip_desc`: Description of this specific shot (string)
- `start_time`: Start timestamp (string, format: HH:MM:SS.sss)
- `end_time`: End timestamp (string, format: HH:MM:SS.sss)
- `duration`: Duration in seconds (float)

**Validation**:
- `start_time` must be before `end_time`
- `duration` must be positive
- `action_id` must be a positive integer

---

### Scene
Represents a merged semantic scene (5-15 seconds) combining related shots.

**Fields**:
- `video_id`: Reference to parent video (string)
- `scene_id`: Unique scene identifier (integer)
- `action_desc`: Description of the main action (string)
- `scene_desc`: Description of the full scene (string)
- `start_time`: Start timestamp (string, format: HH:MM:SS.sss)
- `end_time`: End timestamp (string, format: HH:MM:SS.sss)
- `duration`: Duration in seconds (float)
- `num_clips`: Number of shots merged into this scene (integer)

**Validation**:
- `duration` must be between 5.0 and 15.0 seconds (configurable)
- `num_clips` must be at least 1
- Time ranges must not overlap within the same video

---

### ProcessingTask
Represents a task in the video processing pipeline queue.

**Fields**:
- `video_id`: Video identifier (string)
- `video_path`: Path to video file (string)
- `transnet_path`: Path to cached TransNet results (string, optional)
- `video_metadata`: Additional metadata (dict, optional)
- `status`: Processing status (enum: pending, processing, completed, failed)
- `error`: Error message if failed (string, optional)

**State Transitions**:
- `pending` → `processing` → `completed`
- `pending` → `processing` → `failed`
