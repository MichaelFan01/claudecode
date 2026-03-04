#!/bin/bash

# DEBUG 版本：快速诊断问题
# 只处理 1-2 个视频，打印详细的日志

set -e

# 路径配置
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

BASE_DIR="/ai-video-nas-sh-b-2/yuqiang.xie/skyclipper"
INPUT_CSV="${BASE_DIR}/input_data/test.csv"
OUTPUT_DIR="${BASE_DIR}/output/anime_debug_$(date +%Y%m%d_%H%M%S)"
OUTPUT_JSONL="${OUTPUT_DIR}/output.jsonl"

# 模型路径
MODEL_PATH="/ai-video-nas-sh-b-2/mingshan.chang/models/Qwen3-VL-30B-A3B-Instruct"

# TransNet 配置
TRANSNET_WEIGHTS="${BASE_DIR}/transnetv2-pytorch-weights.pth"
TRANSNET_CACHE_DIR="${OUTPUT_DIR}/transnet_cache"
TRANSNET_WORKERS=8      # DEBUG: 只用2个workers
TRANSNET_THRESHOLD=0.2

# 处理参数 - 为了快速测试
QUEUE_BATCH_SIZE=16      # DEBUG: 收到1个视频就开始处理
BATCH_SIZE=16            # 优化：每次推理8个segments（利用批量加速）
FPS=2.0
WIDTH=360
MAX_SEGMENT_SECONDS=120 # 优化：更长的segment（减少总数）
MAX_FRAMES_PER_SEGMENT=240

# 掐头去尾设置
SKIP_START_SECONDS=0
SKIP_END_SECONDS=0
NO_SEGMENT_SPLIT=false

# 创建输出目录
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${TRANSNET_CACHE_DIR}"

# 创建测试用的小视频列表（只取前2个视频）
TEST_CSV="${OUTPUT_DIR}/test_videos.csv"
head -n 101 "$INPUT_CSV" > "$TEST_CSV"  # 头部行 + 前100个视频

echo "==============================================="
echo "DEBUG 模式 - 并行 TransNet + Qwen3-VL"
echo "==============================================="
echo "输入文件:   $INPUT_CSV"
echo "测试文件:   $TEST_CSV"
echo "视频数量:   2 (DEBUG模式)"
echo "输出目录:   $OUTPUT_DIR"
echo "-----------------------------------------------"
echo "DEBUG 配置:"
echo "  - TransNet workers:   $TRANSNET_WORKERS"
echo "  - Queue batch size:   $QUEUE_BATCH_SIZE (收到1个立即处理)"
echo "  - Inference batch:    $BATCH_SIZE (逐个推理)"
echo "  - Max segment:        ${MAX_SEGMENT_SECONDS}秒"
echo "  - 详细日志:           启用"
echo "==============================================="
echo ""

# 检查 GPU
echo "GPU 状态:"
nvidia-smi --query-gpu=index,name,memory.free --format=csv,noheader,nounits | \
    awk -F', ' '{printf "  GPU %s: %s (%.1f GB free)\n", $1, $2, $3/1024}'
echo ""

# 记录开始时间
START_TIME=$(date +%s)

echo "🚀 开始 DEBUG 运行..."
echo "提示：观察 [Qwen3-VL DEBUG] 和 [prepare_video_data] 日志"
echo "找出耗时最长的步骤"
echo ""

# 运行
python -u vllm_offline_qwen3_vl_parallel.py \
    --video_list "$TEST_CSV" \
    --output_jsonl "$OUTPUT_JSONL" \
    --model_path "$MODEL_PATH" \
    --transnet_weights "$TRANSNET_WEIGHTS" \
    --transnet_cache_dir "$TRANSNET_CACHE_DIR" \
    --transnet_workers $TRANSNET_WORKERS \
    --transnet_threshold $TRANSNET_THRESHOLD \
    --queue_batch_size $QUEUE_BATCH_SIZE \
    --batch_size $BATCH_SIZE \
    --fps $FPS \
    --width $WIDTH \
    --max_segment_seconds $MAX_SEGMENT_SECONDS \
    --max_frames_per_segment $MAX_FRAMES_PER_SEGMENT \
    --skip_start_seconds $SKIP_START_SECONDS \
    --skip_end_seconds $SKIP_END_SECONDS \
    $(if [ "$NO_SEGMENT_SPLIT" = "true" ]; then echo "--no_segment_split"; fi) \
    --node_rank 0 \
    --num_nodes 1 2>&1 | tee "${OUTPUT_DIR}/debug.log"

# 计算耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "==============================================="
echo "✅ DEBUG 运行完成"
echo "==============================================="
echo "总耗时: ${ELAPSED} 秒"
echo ""
echo "分析日志："
echo "  1. 查看日志文件: ${OUTPUT_DIR}/debug.log"
echo "  2. 搜索 'DEBUG' 关键字找出耗时位置"
echo "  3. 检查是否有卡住的地方"
echo ""
echo "关键观察点："
echo "  - [Qwen3-VL DEBUG] 进入主循环 → 是否进入了消费者循环？"
echo "  - [Qwen3-VL DEBUG] 尝试从queue获取 → 是否能获取到任务？"
echo "  - [prepare_video_data] → 视频加载是否很慢？"
echo "  - [Qwen3-VL DEBUG] 开始 LLM 推理 → 推理是否很慢？"
echo "==============================================="

