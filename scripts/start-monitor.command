#!/bin/bash
# ============================================================
# 独立站商品监控 Agent - macOS 一键启动
# 使用方法：双击本文件即可（首次需右键→打开，或右键→打开方式→终端）
# 会自动：解除系统拦截 → 启动 WebUI → 打开浏览器
# ============================================================

# 找到本脚本所在目录（兼容从任意位置双击运行）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 程序名（与 release 文件同名，可修改）
BIN="$SCRIPT_DIR/monitor-macos"

if [ ! -f "$BIN" ]; then
  echo "❌ 未找到程序文件: $BIN"
  echo "   请确认 monitor-macos 与本脚本在同一个文件夹。"
  echo ""
  read -r -p "按回车键退出..." x
  exit 1
fi

echo "==========================================="
echo "  独立站商品监控 Agent 启动中..."
echo "==========================================="

# 1. 解除 macOS Gatekeeper 拦截（下载的未签名应用首次会被拦）
if xattr "$BIN" 2>/dev/null | grep -q quarantine; then
  echo "→ 解除系统安全拦截（首次需要，之后不用）..."
  xattr -dr com.apple.quarantine "$BIN" 2>/dev/null || true
fi

# 2. 确保可执行
chmod +x "$BIN" 2>/dev/null || true

echo "→ 启动 WebUI，浏览器将自动打开 http://127.0.0.1:8321"
echo "   （关闭本窗口 = 停止监控）"
echo "==========================================="

# 3. 启动（数据固定保存在 ~/monitor-agent，不随运行目录变化）
"$BIN" web

echo ""
echo "监控已停止。"
read -r -p "按回车键关闭窗口..." x