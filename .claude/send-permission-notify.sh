#!/bin/bash

# 飞书 Webhook URL
WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/f3310319-0abe-4ab0-8725-1741f5dfa6e7"

# 获取信息
MACHINE_NAME=$(hostname)
PROJECT_PATH=$(pwd)
REQUEST_MESSAGE="${CLAUDE_PERMISSION_REQUEST_MESSAGE:-无请求消息}"

# 转义特殊字符
escape_json() {
    local str="$1"
    str="${str//\\/\\\\}"
    str="${str//\"/\\\"}"
    str="${str//$'\n'/\\n}"
    str="${str//$'\r'/\\r}"
    str="${str//$'\t'/\\t}"
    echo -n "$str"
}

# 构建文本内容
TEXT_CONTENT="机器名: ${MACHINE_NAME}
项目路径: ${PROJECT_PATH}
请求消息:
${REQUEST_MESSAGE}

请在 Claude Code 终端中选择操作。"

# 转义内容
ESCAPED_TEXT=$(escape_json "$TEXT_CONTENT")

# 构建 JSON  payload（先用简单的 text 格式确保能工作）
JSON_PAYLOAD="{
  \"msg_type\": \"text\",
  \"content\": {
    \"text\": \"⚠️ Claude Code 权限请求\n\n${ESCAPED_TEXT}\"
  }
}"

# 发送请求
curl -X POST \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD" \
  "$WEBHOOK_URL"
