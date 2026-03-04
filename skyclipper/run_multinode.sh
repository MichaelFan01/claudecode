#!/bin/bash
# 多机多卡运行脚本 - Smart Clipper
# 用法: 在每个节点上运行此脚本，设置不同的 NODE_RANK
# 例如：
#   Node 0: NODE_RANK=0 bash run_multinode.sh
#   Node 1: NODE_RANK=1 bash run_multinode.sh
#   Node 2: NODE_RANK=2 bash run_multinode.sh
set -e

pip install decord -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install imageio imageio-ffmpeg transnetv2-pytorch orjson opencv-python psutil tqdm -i https://pypi.tuna.tsinghua.edu.cn/simple
nvidia-smi
nvcc --version
# ==================== 多节点配置 ====================
# 从环境变量获取节点信息（支持火山云和PyTorch分布式）
if [ -n "$MLP_ROLE_INDEX" ]; then
    # 火山云环境
    NODE_RANK=$MLP_ROLE_INDEX
    echo "检测到火山云环境: MLP_ROLE_INDEX=$NODE_RANK"
elif [ -n "$RANK" ]; then
    # PyTorch分布式环境
    NODE_RANK=$RANK
    echo "检测到PyTorch分布式环境: RANK=$NODE_RANK"
elif [ -n "$NODE_RANK" ]; then
    # 手动设置的NODE_RANK
    echo "使用手动设置的NODE_RANK=$NODE_RANK"
else
    # 默认为单节点
    NODE_RANK=0
    echo "未检测到分布式环境，使用单节点模式: NODE_RANK=0"
fi

# 节点总数（必须在所有节点上设置相同的值）
NUM_NODES=4  # 👈 根据实际节点数修改

echo "================================================================"
echo "多节点视频处理 - Smart Clipper"
echo "================================================================"
echo "节点配置:"
echo "  当前节点: $NODE_RANK"
echo "  节点总数: $NUM_NODES"
echo "================================================================"

# ==================== 路径配置 ====================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_DIR}"

BASE_DIR="/ai-video-nas-sh-b-2/yuqiang.xie/skyclipper"
INPUT_CSV="${BASE_DIR}/input_data/test.csv"
OUTPUT_DIR="${BASE_DIR}/output/output_multinode"
OUTPUT_JSONL="${OUTPUT_DIR}/output.jsonl"


# 模型路径
MODEL_PATH="/ai-video-nas-sh-b-2/mingshan.chang/models/Qwen3-VL-30B-A3B-Instruct"

# TransNet 配置
TRANSNET_WEIGHTS="${BASE_DIR}/transnetv2-pytorch-weights.pth"
TRANSNET_CACHE_DIR="${OUTPUT_DIR}/transnet_cache"
TRANSNET_WORKERS=8      # TransNet worker数量（建议=GPU数量）
TRANSNET_THRESHOLD=0.2  # 场景检测阈值（动漫建议0.15-0.20）

# 处理参数
QUEUE_BATCH_SIZE=32     # 队列积累大小（积累多少视频后开始处理）
BATCH_SIZE=32           # Qwen3-VL推理批量大小（一次推理多少个segments）
FPS=2.0                 # 视频采样帧率
WIDTH=360               # 视频宽度
MAX_SEGMENT_SECONDS=120 # 最大segment长度（秒）
MAX_FRAMES_PER_SEGMENT=240  # 每个segment最大帧数

# 掐头去尾设置
SKIP_START_SECONDS=0    # 跳过视频开头的秒数（0=不跳过）
SKIP_END_SECONDS=0      # 跳过视频结尾的秒数（0=不跳过）
NO_SEGMENT_SPLIT=false  # 是否不切分segments

# ==================== 创建输出目录 ====================
# 每个节点独立创建目录（mkdir -p 是幂等的，不会冲突）
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${TRANSNET_CACHE_DIR}"
echo "Node $NODE_RANK: 创建输出目录完成"

# 创建测试用的视频列表（可选：限制处理的视频数量）
# 注意：如果多节点同时运行，建议只在外部预先创建测试CSV
# TEST_CSV="${OUTPUT_DIR}/test_videos.csv"
# if [ ! -f "$TEST_CSV" ]; then
#     head -n 1001 "$INPUT_CSV" > "$TEST_CSV"  # 头部行 + 前1000个视频
# fi
# INPUT_CSV=$TEST_CSV
# echo "Node $NODE_RANK: 使用测试视频列表: $TEST_CSV (前1000个视频)"

# ==================== 显示配置信息 ====================
echo ""
echo "================================================================"
echo "配置信息"
echo "================================================================"
echo "节点信息:"
echo "  节点编号:         $NODE_RANK / $NUM_NODES"
echo ""
echo "输入输出:"
echo "  输入CSV:          $INPUT_CSV"
echo "  输出目录:         $OUTPUT_DIR"
echo "  输出文件:         ${OUTPUT_DIR}/output_temp/node_${NODE_RANK}.jsonl"
echo "  TransNet缓存:     $TRANSNET_CACHE_DIR"
echo ""
echo "模型配置:"
echo "  Qwen3-VL模型:     $MODEL_PATH"
echo "  TransNet权重:     $TRANSNET_WEIGHTS"
echo ""
echo "处理参数:"
echo "  TransNet workers: $TRANSNET_WORKERS"
echo "  场景检测阈值:     $TRANSNET_THRESHOLD"
echo "  队列批次大小:     $QUEUE_BATCH_SIZE"
echo "  推理批次大小:     $BATCH_SIZE"
echo "  视频采样FPS:      $FPS"
echo "  视频宽度:         $WIDTH"
echo "  Max segment:      ${MAX_SEGMENT_SECONDS}秒"
echo "  掐头去尾:         开头${SKIP_START_SECONDS}秒, 结尾${SKIP_END_SECONDS}秒"
echo "================================================================"
echo ""

# ==================== 检查GPU ====================
echo "GPU 状态:"
nvidia-smi --query-gpu=index,name,memory.free --format=csv,noheader,nounits | \
    awk -F', ' '{printf "  GPU %s: %s (%.1f GB free)\n", $1, $2, $3/1024}'
echo ""

# ==================== 检查输入文件 ====================
if [ ! -f "$INPUT_CSV" ]; then
    echo "错误: 输入CSV文件不存在: $INPUT_CSV"
    exit 1
fi

# ==================== 检查模型路径 ====================
if [ ! -d "$MODEL_PATH" ]; then
    echo "错误: 模型路径不存在: $MODEL_PATH"
    exit 1
fi

# ==================== 记录开始时间 ====================
START_TIME=$(date +%s)

echo "================================================================"
echo "Node $NODE_RANK: 开始处理..."
echo "================================================================"
echo ""

# ==================== 运行处理脚本 ====================
python -u vllm_offline_qwen3_vl_parallel.py \
    --video_list "$INPUT_CSV" \
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
    --node_rank $NODE_RANK \
    --num_nodes $NUM_NODES \
    --resume \
    2>&1 | tee "${OUTPUT_DIR}/node_${NODE_RANK}.log"

# ==================== 计算耗时 ====================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
ELAPSED_HOURS=$((ELAPSED / 3600))
ELAPSED_MINS=$(((ELAPSED % 3600) / 60))
ELAPSED_SECS=$((ELAPSED % 60))

echo ""
echo "================================================================"
echo "Node $NODE_RANK: 处理完成!"
echo "================================================================"
echo "总耗时: ${ELAPSED_HOURS}小时 ${ELAPSED_MINS}分钟 ${ELAPSED_SECS}秒"
echo "输出文件: ${OUTPUT_DIR}/output_temp/node_${NODE_RANK}.jsonl"
echo "日志文件: ${OUTPUT_DIR}/node_${NODE_RANK}.log"
echo "================================================================"
echo ""

# ==================== 完成标记（可选，用于监控） ====================
# 创建完成信号文件（可用于外部监控脚本）
SYNC_DIR="${OUTPUT_DIR}/output_temp/sync"
mkdir -p "$SYNC_DIR"
DONE_FILE="${SYNC_DIR}/node_${NODE_RANK}.done"
echo "completed at $(date)" > "$DONE_FILE"
echo "elapsed: ${ELAPSED}s" >> "$DONE_FILE"
echo ""
echo "Node $NODE_RANK: 创建完成信号: $DONE_FILE"
echo ""

echo "================================================================"
echo "Node $NODE_RANK: 任务结束"
echo "================================================================"
echo ""
echo "提示："
echo "  - 各节点独立输出文件: ${OUTPUT_DIR}/output_temp/node_*.jsonl"
echo "  - 如需合并，请在所有节点完成后手动运行："
echo "    cat ${OUTPUT_DIR}/output_temp/node_*.jsonl > ${OUTPUT_DIR}/output.jsonl"
echo "================================================================"

