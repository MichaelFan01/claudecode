# Video Quality Validator

视频质量验证模块 - 用于AI/ML训练数据的视频文件质量验证。

## 功能特性

- ✅ 视频基本属性验证（帧率、总帧数、解码完整性）
- ✅ 音频属性验证（采样率、声道数、音视频同步）
- ✅ 批量验证支持
- ✅ 完整的日志记录（符合项目宪法要求）
- ✅ JSON和文本输出格式

## 安装

```bash
# 克隆仓库后，安装依赖
pip install -e .
```

需要先安装FFmpeg：
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get install ffmpeg`

## 使用方法

### Python库使用

```python
from video_quality_validator import VideoQualityValidator

# 创建验证器
validator = VideoQualityValidator(logDir="./logs")

# 验证单个视频
result = validator.validateSingle("/path/to/video.mp4")
print(f"Status: {result.status}")
print(f"Frame Rate: {result.frameRate}")
print(f"Total Frames: {result.totalFrames}")

# 批量验证
report = validator.validateBatch("/path/to/videos", recursive=True)
print(f"Total: {report.totalFiles}")
print(f"Passed: {report.passedFiles}")
```

### CLI使用

```bash
# 验证单个视频
video-quality-validator validate /path/to/video.mp4

# 批量验证
video-quality-validator batch-validate /path/to/videos --recursive

# JSON输出
video-quality-validator validate /path/to/video.mp4 --output json
```

## 项目结构

```
src/
└── video_quality_validator/
    ├── __init__.py      # 包初始化
    ├── core.py          # 核心验证逻辑
    ├── models.py        # 数据模型
    ├── utils.py         # 工具函数
    └── cli.py           # 命令行接口

tests/                     # 测试套件
├── __init__.py
├── test_models.py         # 数据模型测试
├── test_core.py          # 核心验证逻辑测试
└── test_cli.py           # CLI接口测试

logs/                      # 日志输出目录
```

## 运行测试

本项目遵循 Test-Optional Philosophy（测试可选哲学），但测试推荐用于关键路径功能。

```bash
# 安装测试依赖
pip install -e ".[test]"

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_models.py -v

# 生成覆盖率报告（可选）
pytest tests/ --cov=src --cov-report=html
```

## 遵循的规范

本项目严格遵循项目宪法：

1. **命名规范** ✅
   - 文件名: kebab-case (`video-quality-validator`)
   - 类名: PascalCase (`VideoQualityValidator`)
   - 函数/变量: camelCase (`validateSingle`, `frameRate`)

2. **数据生命周期可追溯** ✅
   - 所有操作日志至 `./logs` 文件夹
   - 日志包含文件路径、处理时间、操作动作

3. **视频数据质量强校验** ✅
   - 视频读取校验帧率、总帧数、解码完整性
   - 音频校验采样率、声道数、音视频时长一致性
