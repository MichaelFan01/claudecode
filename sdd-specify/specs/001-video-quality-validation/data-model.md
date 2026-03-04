# Data Model: 视频质量验证模块

**Date**: 2026-03-03
**Feature**: 001-video-quality-validation

## Entities

### VideoValidationResult

单个视频文件的验证结果，包含各验证项的通过/失败状态及详细信息。

**Attributes**:
- `filePath` (string, required): 视频文件的绝对路径
- `timestamp` (datetime, required): 验证执行时间
- `status` (enum, required): 整体验证状态 - "PASS", "FAIL", "PARTIAL"
- `frameRate` (float, optional): 视频帧率（FPS）
- `frameRatePass` (boolean, optional): 帧率验证是否通过
- `totalFrames` (integer, optional): 视频总帧数
- `totalFramesPass` (boolean, optional): 总帧数验证是否通过
- `decodeIntegrityPass` (boolean, required): 解码完整性验证是否通过
- `decodeError` (string, optional): 解码错误信息（如验证失败）
- `hasAudio` (boolean, required): 是否包含音频轨道
- `audioSampleRate` (integer, optional): 音频采样率（Hz）
- `audioSampleRatePass` (boolean, optional): 采样率验证是否通过
- `audioChannels` (integer, optional): 音频声道数
- `audioChannelsPass` (boolean, optional): 声道数验证是否通过
- `videoDuration` (float, optional): 视频时长（秒）
- `audioDuration` (float, optional): 音频时长（秒）
- `avSyncPass` (boolean, optional): 音视频时长一致性验证是否通过
- `validationErrors` (array of string, optional): 所有验证错误列表

**Validation Rules**:
- `filePath` 必须是非空字符串
- `timestamp` 必须是有效的日期时间
- `status` 必须是 "PASS", "FAIL", "PARTIAL" 之一
- 如果 `hasAudio` 为 true，则必须包含音频相关字段

---

### BatchValidationReport

批量验证的汇总报告，包含总文件数、通过数、失败数、各失败原因统计。

**Attributes**:
- `reportId` (string, required): 报告唯一标识符
- `startTime` (datetime, required): 批量验证开始时间
- `endTime` (datetime, required): 批量验证结束时间
- `totalFiles` (integer, required): 处理的总文件数
- `passedFiles` (integer, required): 完全通过验证的文件数
- `failedFiles` (integer, required): 验证失败的文件数
- `partialFiles` (integer, required): 部分通过验证的文件数
- `results` (array of VideoValidationResult, required): 每个文件的详细验证结果
- `failureSummary` (object, optional): 失败原因统计
  - `decodeErrors` (integer): 解码错误数量
  - `frameRateErrors` (integer): 帧率错误数量
  - `audioErrors` (integer): 音频相关错误数量
  - `avSyncErrors` (integer): 音视频同步错误数量
  - `otherErrors` (integer): 其他错误数量

**Validation Rules**:
- `totalFiles` = `passedFiles` + `failedFiles` + `partialFiles`
- `results` 数组长度必须等于 `totalFiles`
- `failureSummary` 中的错误数之和应等于 `failedFiles` + `partialFiles`

---

### ValidationLog

验证操作的日志记录，包含文件路径、处理时间、执行的验证操作。

**Attributes**:
- `logId` (string, required): 日志条目唯一标识符
- `timestamp` (datetime, required): 日志记录时间
- `operation` (string, required): 执行的操作类型 - "VALIDATE_SINGLE", "VALIDATE_BATCH", "GENERATE_REPORT"
- `filePath` (string, optional): 相关文件路径（单文件验证时）
- `directoryPath` (string, optional): 相关目录路径（批量验证时）
- `status` (string, required): 操作状态 - "STARTED", "COMPLETED", "ERROR"
- `message` (string, optional): 详细消息
- `durationMs` (integer, optional): 操作耗时（毫秒）

**Validation Rules**:
- `operation` 必须是 "VALIDATE_SINGLE", "VALIDATE_BATCH", "GENERATE_REPORT" 之一
- `status` 必须是 "STARTED", "COMPLETED", "ERROR" 之一
- 如果 `operation` 是 "VALIDATE_SINGLE"，则 `filePath` 必须存在
- 如果 `operation` 是 "VALIDATE_BATCH"，则 `directoryPath` 必须存在

## State Transitions

### VideoValidationResult Status

- `PASS`: 所有验证项都通过
- `FAIL`: 至少一个关键验证项失败（解码完整性）
- `PARTIAL`: 非关键验证项失败但关键项通过（如音频验证失败但视频验证通过）

### BatchValidationReport Completion

报告状态从进行中到完成的转换：
1. 创建时状态为进行中
2. 所有文件处理完成后状态变为完成
3. 生成汇总统计数据
