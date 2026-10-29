# Azeroth Survivors Android

为 Android 12 及以上手机制作的社区 APK，保留 Aethus 原作的玩法、中文资源和合作入口。首版使用官方 **0.126.0 / 3e72472a** 网页核心；游戏 WASM 保持原始内容。

这版仍是网页核心的安卓封装，不是从原作 Rust 源码编译的原生安卓游戏。APK 包含完整资源，约 874 MiB；画面和运算在手机本地执行。合作需要联网。

## 安装与启动

1. 将 `dist/AzerothSurvivors-0.126.0-android.1-universal.apk` 传到手机安装。
2. 更新 Android System WebView 和 Chrome。
3. 打开 App，点“开始游戏”。内置模式会先检查可用的 WebGPU 适配器和设备。
4. 内置模式无法启动时，使用“Chrome 模式”。它仍读取 APK 内的本地资源。
5. 游戏横屏运行，使用原作触控界面。Chrome 模式首次触控后会尝试进入全屏。

Android 版本满足要求不代表每种 GPU 或驱动都能运行。目标是现代主流 Android 手机；没有宣称所有机型兼容或保证帧率。无 Google Play 的手机也可安装 APK，但需要自行具备支持 WebGPU 的 WebView 或 Chrome；Chrome 模式只寻找已安装的 Chrome 稳定、Beta、Dev、Canary 包。

使用 Chrome 模式时请保留本地资源服务。退出后可以从启动页或通知点“停止游戏资源服务”。该服务仅绑定 `127.0.0.1:47615`，不对局域网提供游戏文件。Chrome 自身的地址栏可能出现；没有绕过网站关联验证来伪装 TWA。

## 存档和联机

内置模式和 Chrome 模式的浏览器存储独立，使用游戏内 Options → Saves 导出／导入迁移。内置模式的导出通过 Android 系统文件选择器保存，导入使用系统文档选择器；这两个流程仍需真机确认。更新 APK 时保留同一签名，不要通过卸载来更新，以免丢失 App 私有存档。

合作入口沿用原作。安卓适配脚本仅将本机 `/coop` WebSocket 地址改为官方 `wss://wow.aethus.pl/coop/...`；官方返回的游戏中继地址保持不变。所有玩家需核对相同游戏版本，当前为 **0.126.0**。之前的 Mac 0.123.0 包未在本次任务中更新。

官方 0.126.0 更新说明包含中文、日文、韩文的输入法改进。本 APK 已包含新增 `ime.js` 模块和官方中日韩字型，但尚未在真实安卓键盘上验证中文名称输入。

## 实现与安全边界

- Android 原生启动页、横屏与全屏处理；硬件加速 WebView。
- 启动时真实请求 WebGPU adapter/device，失败时提供明确提示和 Chrome 入口。
- 保留原作 Android UA 与 `pipe_warm=0`、`pbr_lite=1` 手机图形预设。
- APK 内压缩资源直接通过 AssetManager 流式读取，不必先解压成第二份资源包。
- HTTP 支持 Range、ETag 与更新后缓存重新验证。
- JavaScript 桥接只有图形检测和受限存档导出，不提供任意文件、命令或应用执行接口。
- 保持 TLS 验证；明文网络仅允许 loopback；外部页面不能嵌入桥接窗口。
- 不含广告、账号系统或额外分析 SDK；原作的官方网络请求仍由原作核心执行。

## 构建

需要 Python 3.11+、JDK 17、Google Android SDK API 35 和 Build-Tools 35.0.0。当前脚本直接使用 javac/d8/aapt2/apksigner，不依赖 Gradle。

`scripts/sync_official.py` 下载同一标记的原始核心、动态模块、变化资源及索引，验证 WASM 编译和导入，生成 `assets/latest-web-core/core-manifest.json`。完整的大型资源基底来自已保留的官方 Mac 包 `Contents/Resources/www`，只读使用，不修改 Mac App。

```sh
python3 scripts/build_apk.py \
  --sdk /path/to/android-sdk \
  --java-home /path/to/jdk17 \
  --web '/path/to/Azeroth Survivors.app/Contents/Resources/www' \
  --core /path/to/verified-web-core
```

输出有 APK、SHA256SUMS.txt 和 build-manifest.json。签名密钥仅保存在 `.private/`，不放入 APK 或源码分发包。要保持后续更新兼容，需保留此目录；不要公开它。

## 验证范围

实际状态记录于 `evidence/verification.json`。安装成功、启动页显示、资源服务工作、浏览器模拟触控以及真实手机入图／流畅度，是不同层级的验证；不能互相代替。

来源：[原作](https://wow.aethus.pl/)、[官方版本清单](https://wow.aethus.pl/exe/latest.json)、[原始 Mac 社区封装](https://github.com/myslithell/azeroth-survivors)。官方字型的 OFL 授权文字随 APK 附带。
