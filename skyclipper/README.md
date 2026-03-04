# SkyClipper - 视频动作分析与场景分割工具

基于 TransNetV2 和 Qwen3-VL 的智能视频分析工具，自动识别动作变化和镜头切换，生成精准的时序标注。

## 功能特性

- 🎬 **场景检测**：使用 TransNetV2 自动检测镜头边界
- 🤸 **动作识别**：基于 Qwen3-VL 的智能动作理解和分类
- ⚡ **并行架构**：TransNet 生产者 + Qwen3-VL 消费者模式
- 🚀 **高性能**：多卡并行处理，充分利用 GPU 资源
- 📊 **双级输出**：支持 shot 级别和 scene 级别的结果
- 🌐 **中英双语**：支持中文和英文提示模板
- 👁️ **可视化**：内置交互式 HTML 查看器

## 核心架构

```
┌─────────────────────┐
│  TransNet 进程池    │  8卡并行场景检测
│  (Producer)         │  快速生成镜头边界
└──────────┬──────────┘
           │ Queue
           ▼
┌─────────────────────┐
│  Qwen3-VL 进程      │  批量推理
│  (Consumer)         │  动作识别+描述生成
└─────────────────────┘
```

**查看完整流程图：** [docs/flow-diagram.html](docs/flow-diagram.html) - 交互式流程图，点击节点查看详细信息。

## 项目结构（模块化）

```
skyclipper/
├── src/
│   ├── cli/                    # 命令行接口
│   │   ├── process_videos.py   # 视频处理主入口
│   │   ├── merge_results.py    # 结果合并工具
│   │   └── visualize.py       # 可视化工具
│   ├── core/                   # 核心模块
│   │   ├── scene_detector.py   # TransNet 场景检测
│   │   ├── action_recognizer.py # Qwen3-VL 动作识别
│   │   ├── video_processor.py  # 管道编排
│   │   ├── result_merger.py   # 结果合并逻辑
│   │   └── visualizer.py      # HTML 生成
│   └── utils/                  # 工具模块
│       ├── time_utils.py       # 时间转换工具
│       ├── xml_parser.py       # XML 解析工具
│       ├── json_utils.py       # JSON 处理工具
│       └── video_utils.py      # 视频处理工具
├── tests/                       # 测试代码
│   ├── unit/                   # 单元测试
│   └── integration/            # 集成测试
├── docs/                        # 文档
│   └── flow-diagram.html       # 交互式流程图
├── data/
│   └── prompt-templates/       # 提示模板
```

## 使用方式（新）

### 方式一：使用模块化 CLI（推荐）

```bash
# 处理视频
python -m src.cli.process_videos \
    --video_list input.csv \
    --output_jsonl output.jsonl

# 合并结果
python -m src.cli.merge_results \
    --temp_dir output/temp \
    --output_shot shot.jsonl \
    --output_scene scene.jsonl

# 可视化
python -m src.cli.visualize \
    --input_jsonl scene.jsonl \
    --output_html viewer.html
```

### 方式二：使用原始脚本（向后兼容）

原始脚本仍然可用，它们现在内部调用新的模块化代码：

| 脚本 | 功能 |
|------|------|
| `vllm_offline_qwen3_vl_parallel.py` | 核心推理脚本，并行处理视频 |
| `merge_and_parse_clips.py` | 合并多节点输出并生成 shot/scene 级别结果 |
| `parser_vis.py` | 可视化工具，生成交互式 HTML |

## 快速开始

### 1. 准备输入数据

创建 CSV 文件，包含以下列：
- `video_path`: 视频文件路径
- 其他元数据（可选）

示例：
```csv
video_path,fps,duration
/path/to/video1.mp4,30,120.5
/path/to/video2.mp4,24,95.3
```

### 2. 调试模式（单机）

适合开发调试，快速验证效果：

```bash
bash run_singlenode.sh
```

**关键参数：**
- 处理少量视频（默认100个）
- 输出详细日志
- 单机多卡并行

### 3. 生产模式（多机多卡）

适合大规模数据处理：

```bash
bash run_multinode.sh
```

**特点：**
- 多节点分布式处理
- 自动负载均衡
- 容错机制

### 4. 合并和解析结果

处理多节点输出，生成两个级别的结果：

```bash
python merge_and_parse_clips.py \
    --temp_dir output/temp \
    --output_shot video_clips_shot.jsonl \
    --output_scene video_clips_scene.jsonl \
    --min_duration 5.0 \
    --max_duration 15.0
```

**输出说明：**
- **shot 级别**：原始镜头片段，不合并
- **scene 级别**：合并后的场景片段（5-15秒）

### 5. 可视化

生成交互式 HTML 查看器：

```bash
python parser_vis.py \
    --jsonl video_clips_scene.jsonl \
    --output viewer.html
```

在浏览器中打开 `viewer.html` 即可：
- 播放视频片段
- 查看动作标注
- 对比时间轴
- 审核标注质量

## 完整工作流程

```bash
# 步骤 1: 单机调试（验证效果）
bash run_singlenode.sh

# 步骤 2: 多机运行（大规模处理）
bash run_multinode.sh

# 步骤 3: 合并结果
python merge_and_parse_clips.py \
    --temp_dir output/temp \
    --output_shot video_clips_shot.jsonl \
    --output_scene video_clips_scene.jsonl

# 步骤 4: 可视化审核
python parser_vis.py \
    --jsonl video_clips_scene.jsonl \
    --output viewer.html
```

## 核心概念

### 动作 (Action)

**动作**是视频中主要对象执行的独特、有意义的活动。特点：

- **具体的**："人物在做咖啡" ✓，而不是 "人物在厨房" ✗
- **以活动为核心**：基于对象正在**做什么**
- **连续的**：同一动作持续直到活动发生明确变化

**动作变化示例：**
- 行走 → 跑步（移动方式改变）
- 站立 → 坐下（姿态改变）
- 交谈 → 打斗（互动类型改变）
- 阅读书籍 → 合上书站起来（活动改变）

**不算动作变化的情况：**
- 同一动作的不同机位拍摄
- 同一活动的特写 vs 全景
- 同一对话中切到反应镜头

### 镜头 (Shot)

在同一动作内，根据**镜头变化**进行细分：
- 机位变化
- 推拉摇移
- 切换剪辑

### 场景 (Scene)

合并相关的短镜头，生成 5-15 秒的语义完整片段。

## 输出格式

### Shot 级别（原始）

```json
{
  "video_id": "abc123",
  "video_path": "/path/to/video.mp4",
  "segment_id": 0,
  "clip_id": 1,
  "action_id": 1,
  "action_desc": "人物在街上行走",
  "clip_desc": "全景镜头展示人物从左向右穿过街道",
  "start_time": "00:00:05.200",
  "end_time": "00:00:09.800",
  "duration": 4.6
}
```

### Scene 级别（合并后）

```json
{
  "video_id": "abc123",
  "video_path": "/path/to/video.mp4",
  "scene_id": 1,
  "action_desc": "人物在街上行走",
  "scene_desc": "全景镜头展示人物从左向右穿过街道，随后切换到人物正面特写",
  "start_time": "00:00:05.200",
  "end_time": "00:00:15.400",
  "duration": 10.2,
  "num_clips": 2
}
```

## 配置参数

### TransNet 配置

- `--transnet_workers`: TransNet 并行进程数（默认 8）
- `--transnet_threshold`: 场景检测阈值（默认 0.2）
- `--transnet_cache_dir`: 场景检测结果缓存目录

### Qwen3-VL 配置

- `--model_path`: 模型路径
- `--batch_size`: 批处理大小（默认 16）
- `--queue_batch_size`: 队列批处理大小（默认 16）
- `--language`: 语言模式（zh/en）

### 视频处理配置

- `--fps`: 采样帧率（默认 2.0）
- `--width`: 图像宽度（默认 360）
- `--max_segment_seconds`: 最大片段时长（默认 120秒）
- `--max_frames_per_segment`: 每个片段最大帧数（默认 240）
- `--skip_start_seconds`: 跳过开头秒数
- `--skip_end_seconds`: 跳过结尾秒数

### 合并参数

- `--min_duration`: 场景最小时长（默认 5.0秒）
- `--max_duration`: 场景最大时长（默认 15.0秒）
- `--num_workers`: 并行处理进程数

## 性能优化建议

### 单机调试

```bash
# 测试前 10 个视频，快速迭代
head -n 11 input.csv > test.csv  # 包含表头
bash run_singlenode.sh
```

### 生产环境

1. **TransNet 优化**：
   - 增加 `--transnet_workers` 利用多卡
   - 启用缓存避免重复计算

2. **Qwen3-VL 优化**：
   - 调整 `--batch_size` 充分利用显存
   - 使用 `--queue_batch_size` 控制吞吐量

3. **视频处理优化**：
   - 降低 `--fps` 减少帧数
   - 减小 `--width` 加速解码
   - 增大 `--max_segment_seconds` 减少片段数

## 常见问题

**Q: 如何跳过片头片尾？**  
A: 使用 `--skip_start_seconds` 和 `--skip_end_seconds` 参数。

**Q: 动作分割太细碎怎么办？**  
A: 使用 `merge_and_parse_clips.py` 合并为 scene 级别，调整 `--min_duration` 和 `--max_duration`。

**Q: 如何处理超长视频？**  
A: 调整 `--max_segment_seconds` 和 `--max_frames_per_segment` 参数。

**Q: GPU 显存不足？**  
A: 减小 `--batch_size`、`--width` 或 `--max_frames_per_segment`。

**Q: 多节点输出如何合并？**  
A: 使用 `merge_and_parse_clips.py` 自动合并所有 `node_*.jsonl` 文件并去重。

## 目录结构

```
skyclipper/
├── README.md                          # 本文档
├── vllm_offline_qwen3_vl_parallel.py # 核心推理脚本
├── run_singlenode.sh                 # 单机运行脚本
├── run_multinode.sh                  # 多机运行脚本
├── merge_and_parse_clips.py          # 结果合并和解析
├── parser_vis.py                     # 可视化工具
├── prompt_template_action_zh.txt     # 中文提示模板
├── prompt_template_action_en.txt     # 英文提示模板
├── transnetv2-pytorch-weights.pth    # TransNet 模型权重
├── input_data/                       # 输入数据目录
│   └── test.csv                      # 测试用视频列表
└── output/                           # 输出目录
    ├── temp/                         # 临时文件（多节点输出）
    │   ├── node_0.jsonl
    │   ├── node_1.jsonl
    │   └── ...
    ├── video_clips_shot.jsonl        # Shot 级别结果
    ├── video_clips_scene.jsonl       # Scene 级别结果
    └── viewer.html                   # 可视化页面
```

## 依赖环境

- Python 3.8+
- PyTorch
- vLLM
- Transformers
- TransNetV2-PyTorch
- Decord
- Pandas
- Numpy

## 许可证

请参考项目许可证文件。

---

**提示：** 建议先用单机模式处理少量视频验证效果，再切换到多机模式进行大规模处理。

