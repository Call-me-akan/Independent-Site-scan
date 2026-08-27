# macOS 未签名应用提示说明

## 现象

从 GitHub Release 下载的 `monitor-macos`，双击/运行时提示：

> Apple无法验证"monitor-macos"是否包含可能危害Mac安全或泄漏隐私的恶意软件。

## 原因

这不是病毒，也不是程序问题。原因：

- 本程序用 PyInstaller 打包，没有 Apple 开发者签名（需要付费开发者账号，$99/年）
- macOS Gatekeeper 会拦截**所有从网上下载的未签名应用**

本地编译的二进制（`dist/monitor`）没有隔离属性，不会提示。

## 解决办法（选一个）

### 方法 1：终端解除（推荐）

```bash
xattr -dr com.apple.quarantine ~/Downloads/monitor-macos
chmod +x ~/Downloads/monitor-macos
~/Downloads/monitor-macos web
```

或使用仓库脚本：

```bash
./scripts/unlock-macos.sh ~/Downloads/monitor-macos
```

### 方法 2：右键打开

1. 在访达中找到 `monitor-macos`
2. **右键点击** → 选择「打开」
3. 弹窗里点「打开」按钮
4. 之后双击即可正常打开

## 长期方案（可选）

如果未来要彻底消除这个提示：

- **Apple Developer 账号公证（Notarization）**：需 $99/年开发者账号 + 配置签名与公证流程，产物会显示"已验证开发者"
- **自签名 + 用户信任**：无法远程消除，仍需用户首次手动放行

## 结论

对内部使用/小范围分发，使用方法 1 或 2 即可，一次放行永久可用。