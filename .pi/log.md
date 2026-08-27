# 开发日志 (Development Log)

> 规则：每次改动/验证/发版，追加一条记录。格式：`- [日期] 类型 | 内容 | 验证状态`

## 2026-08-27

- [FIX] 修复 init_config 升级时只写不合并模板站点的问题。现象：用户在运行目录已有旧 config.yaml（仅 example）时，预设的 31 站不生效。根因：`init_config` 仅当文件不存在时才写模板，已存在直接 return。修复：改为「合并」——按站点 id 去重，把模板中缺失的站点合并进现有 config。
- [TEST] 新增 tests/test_config_merge.py（3 个用例）：首次运行写满模板 / 已有 config 合并预设站点且不动 webhook / 幂等。本地 pytest 26 passed。
- [VERIFY] 真实模拟：旧 config 仅 example（+自定义 webhook）→ init_config 后 32 站（example+31 预设），webhook 保留。
- [FIX] 确认 webhook 无缓存：config.yaml 实时读取，用户本地 31 站 + 飞书 + 钉钉配置完整保留。
- [PROCESS] 用户要求规范流程：开发分支 → 本地 pytest → 合 main → CI 通过 → 才打 tag 发版；每步记录本文件。本次修复改走 `fix/init-merge` 分支。
- [RELEASE] v0.5.0 已发布（预设站点模板 + 扫描/发送解耦 + daemon 总开关）。
- [RELEASE] v0.5.1 已发布（修复 init_config 合并预设站点）。
- [PROCESS-V0.5.1] 首次按规范流程执行并跑通：本地 pytest 26 passed → 建 fix/init-merge 分支 → 提交推送 → gh pr create #1 触发 CI（3.11+3.12 pass）→ gh pr merge → 合入 main → 打 v0.5.1 tag → release 构建成功。今后发版都按此流程，并在本文件记录。
- [FEATURE] 研究「开箱即用」体验：验证 v0.5.1 release 二进制在全新目录直接 `monitor web` 即可自动生成 31 站配置（实测成功）。
- [FIX] 数据目录固定化：新增 `data_dir()` 解析—— 优先级 $MONITOR_AGENT_DIR > cwd 已存在 config.yaml（开发兼容）> ~/monitor-agent（打包版固定位置）。storage/export 相对路径改为基于 data_dir 解析，解决「打包版在不同 cwd 下 config 位置漂移、换目录像丢失站点」的问题。新增 tests/test_data_dir.py（5 用例），本地 pytest 31 passed。
- [TODO] 打包版 config 固定到 ~/monitor-agent 后，需同步提供「一键启动脚本」（macOS .command / Windows .bat）封装 Gatekeeper 解除+启动 web，实现真正的双击即用。