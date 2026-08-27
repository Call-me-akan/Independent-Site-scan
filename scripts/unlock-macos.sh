#!/usr/bin/env bash
# 解除 macOS Gatekeeper 对未签名二进制的拦截
# 用法: ./scripts/unlock-macos.sh /path/to/monitor-macos
# 或:  ./scripts/unlock-macos.sh            (默认当前目录 dist/monitor)
set -euo pipefail

TARGET="${1:-dist/monitor}"
if [ ! -f "$TARGET" ]; then
  echo "文件不存在: $TARGET"
  echo "用法: ./scripts/unlock-macos.sh /path/to/monitor-macos"
  exit 1
fi

echo "解除隔离属性: $TARGET"
xattr -dr com.apple.quarantine "$TARGET" 2>/dev/null || true
chmod +x "$TARGET"
echo "✅ 完成。现在可以运行:"
echo "   $TARGET web"