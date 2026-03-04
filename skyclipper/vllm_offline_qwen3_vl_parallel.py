#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行版本：TransNet生产者 + Qwen3-VL消费者
核心架构：
1. TransNet进程池：8卡并行处理视频，生成场景边界
2. Qwen3-VL进程：从队列取视频，批量推理
3. 队列通信：TransNet完成后放入队列，Qwen3-VL消费

使用场景：
- TransNet快速处理大量视频
- Qwen3-VL充分利用8卡90%显存

NOTE: This is a compatibility wrapper. For new code, use:
python -m src.cli.process_videos --video_list <list> --output_jsonl <output>
"""

import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

import torch.multiprocessing as mp

# Import from the new modular structure
from src.cli.process_videos import main


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()
