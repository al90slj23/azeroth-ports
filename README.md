# Azeroth Ports

Aethus 原作游戏的非官方社区封装与逆向研究仓库。现有社区版本使用原作提供的核心，没有从原作 Rust 源码重新编译。

## 两个板块

| 板块 | 工作范围 | 入口 |
|---|---|---|
| 封装优化 | Android／Mac 安装包、触控、界面、中文、性能、离线体验与合作兼容 | [封装优化](ports/README.md) |
| REA 逆向研究 | 用固定版本 REA 分析原始 JS、WASM 和 Windows 原生程序，追踪资源显示、技能数值与联网逻辑 | [REA 研究区](reverse-engineering/README.md) |

`android/`、`macos/` 保留现有构建、签名和存档路径；研究区独立保存工具入口、目标版本、问题清单和分析结论。研究补丁经过对应版本验证后，才能进入封装版。REA 分析结果不等于已经恢复完整源码。

逆向主目标固定为已取得的官方 **0.135.1 / Web0898d5e3**；0.134.0保留固定研究结果，0.126.0保留历史回归参考。当前[14阶段独立研究切片](reverse-engineering/reports/2026-11-01-headless-tail0135-independent-review.md)已完成8种子1614帧22607阶段、11次选择、22615次原件入口调用0差异（67源/60core/16角色）。主切片的phase1仍为研究输入，6未知技能/2预算边界保留。

新增[独立默认开局](reverse-engineering/reports/2026-11-01-opening0135.md)：16组、32次完整原件入口、0声明差异，连续产生2条附属对象、4NPC、2个kind2、事件声明及69个边界对象，六vector和全部新增消息均对照；[独审通过](reverse-engineering/reports/2026-11-01-opening0135-independent-review.md)。世界侧已有[M2碰撞／候选与导航生产](reverse-engineering/reports/2026-11-01-world-raster0135-independent-review.md)、[world查询与位置消费者](reverse-engineering/reports/2026-11-01-world-consumers0135-independent-review.md)独审通过，[WMO碰撞生产](reverse-engineering/reports/2026-11-01-wmo-geometry0135.md)覆盖实际readset全部410文件、[独审通过](reverse-engineering/reports/2026-11-01-wmo-geometry0135-independent-review.md)。开局仍以已解析world为显式输入，尚未接入上述主切片，完整asset→world生产、渲染和独立一局未完成。

[真实世界与开局观察](reverse-engineering/reports/2026-11-01-entry-world0135-probe.md)的453份MPQ／561次GET仍是历史原件观察；本轮新增bootstrap与主切片帧均为0。history的[164组/924调用组件](reverse-engineering/reports/2026-11-01-incoming-history0135.md)与[真实DBC9组/37调用组合](reverse-engineering/reports/2026-11-01-browser-history0135-independent-review.md)分别保留，各层不相加。现有安装包不随研究目标自动更新，详见[版本策略](reverse-engineering/VERSION_STRATEGY.md)与[覆盖清单](reverse-engineering/RECONSTRUCTION.md)。

[真实915观测](reverse-engineering/reports/2026-11-01-effect-system0135-probe.md)确认本批时钟和两类效果队列保持空；后继主切片使用独立模型重新生成预期，保留原始三域读回。非空延迟动作另有500组对照（383正常、117预期原版错误），不代表全部915。完整880还缺其他入口、2376特殊事件及前段/party/终态组合，完整自然帧和独立一局未完成。

## 当前封装版本

| 平台 | 当前游戏核心 | 入口 |
|---|---|---|
| macOS / Apple Silicon | 0.123.0 | [macos/README.md](macos/README.md) |
| Android 12+ | 0.126.0 | [android/README.md](android/README.md) |

两端目前使用不同版本的核心，未统一更新。合作游戏前需要核对各端的游戏版本；本仓库不代表已完成所有机型或跨平台联机验收。

## Android 安装包

[下载 Android 第四版（0.126.0-android.4）](https://github.com/al90slj23/azeroth-ports/releases/tag/android-v0.126.0-r4)。保留原版卡片直接选择，原“重抽”按钮和点击区域等比放大两倍；同时包含快捷浮窗暂停、HUD 缩放、图形调节、电池温度和部分简体中文补译。

使用相同签名，可直接覆盖之前的社区 Android 包；不要先卸载，以免丢失存档。Release 附带 APK、SHA-256 校验、实际画面及验证摘要。桌面模拟已验证鼠标和菜单模式触控，真实手机普通触控、温度和性能仍需真机确认。

## 目录

- `ports/`：封装优化板块的工作入口。
- `reverse-engineering/`：REA 工具入口、目标基线、研究问题与分析结论。
- `macos/mac/`：Electron 启动器、本地静态服务、合作代理、存档移转与测试。
- `macos/scripts/`：macOS 打包脚本。
- `android/app/`：Android 启动页、WebView、存档桥接与本地资源服务。
- `android/web/`：安卓网页适配层。
- `android/scripts/`、`android/tests/`：核心同步、资源准备、APK 构建与测试。

## 测试

在仓库根目录运行已有的 Node.js 测试：

```sh
node --test macos/mac/static-server.test.js macos/mac/profile-migration.test.js macos/mac/coop-proxy.test.js
node --test android/tests/android-bridge.test.js android/tests/touch-tools.test.js android/tests/performance.test.js android/tests/localization-resources.test.js
```

准备好已验证的官方核心后，可检查刷新按钮补丁与引擎暂停导入（后一项需要先构建资源）：

```sh
python3 android/tests/native-reroll-patch.test.py
python3 android/tests/pause-packaging.test.py
```

这些测试验证本地实现，不等同于真实 Android 手机兼容性、性能或完整游戏流程验收。详细验证范围见各平台 README。

## 构建

仓库保存平台封装源码、测试、所需的字体授权资料，以及 REA 研究脚本和精简分析报告。完整游戏资源、已下载的核心快照、SDK、逆向工具、原始分析报告、虚拟环境与构建产物不进入 Git。仅克隆源码不足以生成完整安装包；本机的大型资源保存在外置硬盘，需要按各平台说明准备并通过脚本校验。

macOS 需要 Python 3.11+、Node.js、Xcode Command Line Tools、固定版本的原始 Mac ZIP 和已验证的核心快照：

```sh
python3 macos/scripts/package_macos.py \
  --archive /path/to/AzerothSurvivors-macOS-AppleSilicon.zip \
  --output /path/to/new-output-directory \
  --web-core /path/to/verified-web-core
```

Android 需要 Python 3.11+、JDK 17、Android SDK API 35 / Build-Tools 35.0.0，以及完整 Mac 包中的 `Contents/Resources/www` 资源基底。该基底由安卓脚本只读使用；用参数明确指定本机资源和工具位置：

```sh
python3 android/scripts/sync_official.py \
  --base '/path/to/Azeroth Survivors.app/Contents/Resources/www' \
  --output /path/to/new-web-core

python3 android/scripts/build_apk.py \
  --sdk /path/to/android-sdk \
  --java-home /path/to/jdk17 \
  --web '/path/to/Azeroth Survivors.app/Contents/Resources/www' \
  --core /path/to/verified-web-core
```

同步脚本获取执行时的官方核心，不保证仍是上表版本。复现现有版本应使用已保留且通过校验的对应快照。macOS 打包输出目录必须不存在；安卓构建结果写入 `android/dist/`。

Android 更新依赖同一签名。`android/.private/` 内的签名密钥和密码只保存在本机，必须妥善保留和备份，禁止提交到 Git。两端既有产品名称、包标识和存档路径沿用各自实现。

## 来源与授权

- 原作者及官方游戏：[Aethus](https://wow.aethus.pl/)。
- Mac 封装基础：[myslithell/azeroth-survivors](https://github.com/myslithell/azeroth-survivors)。
- 版本来源、文件校验、原作资源和字体授权说明分别见 [macOS README](macos/README.md) 与 [Android README](android/README.md)。

原作核心和资源沿用各自权利人的授权；本仓库没有为整个游戏新增统一开源许可。随源码保存的官方中日韩字体附带原有 OFL 授权文本。
