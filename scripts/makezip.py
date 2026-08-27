#!/usr/bin/env python3
"""Zip a directory. Usage: makezip.py <output.zip> <dir>"""
import pathlib
import sys
import zipfile


def main() -> int:
    if len(sys.argv) != 3:
        print(f"用法: makezip.py <输出.zip> <目录>")
        return 1
    out, src_dir = sys.argv[1], pathlib.Path(sys.argv[2])
    if not src_dir.is_dir():
        print(f"目录不存在: {src_dir}")
        return 1
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src_dir.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(src_dir))
    print(f"zip created: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())