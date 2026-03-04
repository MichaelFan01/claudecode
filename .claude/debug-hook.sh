#!/bin/bash

# 调试脚本：输出所有环境变量
LOG_FILE="/Users/fanmingyuan/Desktop/vibe-coding/claudecode/.claude/hook-debug.log"

echo "=== $(date) ===" >> "$LOG_FILE"
echo "All environment variables:" >> "$LOG_FILE"
env >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "Claude related variables:" >> "$LOG_FILE"
env | grep -i "claude\|permission" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
