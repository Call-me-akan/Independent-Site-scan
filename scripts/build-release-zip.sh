#!/usr/bin/env bash
# 打包 release 目录为 zip（跨平台：macOS/Linux/Windows runner 都可用，依赖 python）
# 用法: build-release-zip.sh <zip输出路径> <要打包的目录>
set -euo pipefail

ZIP_OUT="${1:?用法: build-release-zip.sh <zip输出路径> <打包目录>}"
SRC_DIR="${2:?缺少打包目录}"

if [ ! -d "$SRC_DIR" ]; then
  echo "目录不存在: $SRC_DIR"
  exit 1
fi

cd "$SRC_DIR"
python3 - <<PYEOF
import zipfile, pathlib
src = pathlib.Path('.')
with zipfile.ZipFile('$ZIP_OUT', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(src.rglob('*')):
        if f.is_file():
            z.write(f, f.relative_to(src))
print('zip created: $1')
PYEOF
echo "打包完成: $1"
ls -la "$ZIP_OUT" || true
cd - >/dev/null