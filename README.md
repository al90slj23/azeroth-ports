# Azeroth Survivors

Aethus 原作网页游戏的社区封装与平台适配。macOS 和 Android 放在同一个仓库，分别维护启动器、平台功能与打包工具；游戏核心仍由原作提供，没有从原作 Rust 源码重新编译。

| 平台 | 当前游戏核心 | 入口 |
|---|---|---|
| macOS / Apple Silicon | 0.123.0 | [macos/README.md](macos/README.md) |
| Android 12+ | 0.126.0 | [android/README.md](android/README.md) |

两端目前使用不同版本的核心，未统一更新。合作游戏前需要核对各端的游戏版本；本仓库不代表已完成所有机型或跨平台联机验收。

## 目录

- `macos/mac/`：Electron 启动器、本地静态服务、合作代理、存档移转与测试。
- `macos/scripts/`：macOS 打包脚本。
- `android/app/`：Android 启动页、WebView、存档桥接与本地资源服务。
- `android/web/`：安卓网页适配层。
- `android/scripts/`、`android/tests/`：核心同步、资源准备、APK 构建与测试。

## 测试

在仓库根目录运行已有的 Node.js 测试：

```sh
node --test macos/mac/static-server.test.js macos/mac/profile-migration.test.js macos/mac/coop-proxy.test.js
node --test android/tests/android-bridge.test.js
```

这些测试验证本地实现，不等同于真实 Android 手机兼容性、性能或完整游戏流程验收。详细验证范围见各平台 README。

## 构建

仓库只保存平台封装源码、测试及所需的字体授权资料。完整游戏资源、已下载的核心快照、SDK、虚拟环境、构建产物与本地验证资料不进入 Git。仅克隆源码不足以生成完整安装包；本机的大型资源保存在外置硬盘，需要按各平台说明准备并通过脚本校验。

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
