# Azeroth Ports

当前功能对齐目标为 **0.139.1 / `b89633f9b`**，于 **2026-11-02T14:31:18Z** 再核并另存[官方Windows／Web原件与完整静态profile](reverse-engineering/reports/2026-11-02-official0139-1-acquisition-identity.md)；新版[非致死伤害80组／125完整原件调用](reverse-engineering/reports/2026-11-02-combat0139-1-independent-review.md)已独审通过；[30入口与143声明字段的静态迁移](reverse-engineering/reports/2026-11-02-engine0139-1-incremental-independent-review.md)单独登记，不代表整局行为相同。固定139的[近身自动施法](reverse-engineering/reports/2026-11-02-player-autocast0139-independent-review.md)、[普通刷怪前40秒域](reverse-engineering/reports/2026-11-02-spawn-schedule0139-independent-review.md)与[Windows升级值机器码仿真／WASM配对](reverse-engineering/reports/2026-11-02-native-upgrade0139-independent-review.md)分别独审通过。固定139的[连续360组件步／尸体清理v2](reverse-engineering/reports/2026-11-02-player-enemy0139-v2-independent-review.md)、[首60秒四种波次／资源生成](reverse-engineering/reports/2026-11-02-spawn-schedule0139-v3-independent-review.md)和[运动暂停／恢复](reverse-engineering/reports/2026-11-02-world-pause0139-independent-review.md)也已独审；同帧消息顺序修正采用新代码／新原件，旧失败批保持拒绝。自然首次升级／续战与刷怪尚在接线；旧139结果不转记1391。自然App／输入、完整主循环、独立渲染、Windows应用执行和独立完整一局仍未验收。安装包与存档未替换。

历史138核对：官方元数据本轮核对至 **2026-11-01T23:57:03Z**：仍为0.138.0、同一EXE SHA／大小及首页stamp `9552af247ddb`，见[只读核对收据](reverse-engineering/evidence/official-goal-phase-network-check-20261101T235701.350290Z/receipt.json)。最新138另有[属性计算10569组／10569完整1512及独审](reverse-engineering/reports/2026-11-02-stats0138.md)，与[非致死伤害80组／125调用](reverse-engineering/reports/2026-11-02-combat0138-independent-review.md)分别登记；[13入口迁移守卫](reverse-engineering/reports/2026-11-02-flow0138-migration.md)属于静态证据，不能计为新版连续流程通过。最新138的[默认构造162次fresh1571及独审](reverse-engineering/reports/2026-11-02-initial-state0138.md)也已通过，覆盖502B已知投影及40个完整速度包；borrowedflatview、累计338580个None和未进入phase1均单独标明。现有安装包与存档未替换。

本轮固定135的[移动→战斗→真实符文拾取](reverse-engineering/reports/2026-11-02-opening-moving-rune0135.md)完成新460帧／4选卡／44次完整968输入／6488阶段／6490原件入口，0声明差异，[独审通过](reverse-engineering/reports/2026-11-02-opening-moving-rune0135-independent-review.md)。第444帧（raw索引443）消费实际刷出的kind5符文，停止移动后继续16帧；恢复请求133，但当时满血266，故只证明cap、移除与通知链，不称非零回血增量。117源／100production、snapshot／独立预解析world／部分类型App和外部clock边界明确。

[移动2328的38组／完整968本地输入33组](reverse-engineering/reports/2026-11-02-player-motion0135.md)和[校正确认199的88组](reverse-engineering/reports/2026-11-02-player-correction0135.md)均各自独审通过。真实键盘／摇杆生产、自然App／完整880、远端同步仍未接通；ACK组件尚未作为连续流程动作接线。135结果不转记138，Windows原生执行与独立完整一局均为0。

历史[静止玩家750帧物理状态闭环](reverse-engineering/reports/2026-11-02-opening-player-sources0135.md)及[raw451资源→750帧模型入口](reverse-engineering/reports/2026-11-02-raw-physical7500135.md)保持各自范围，后继[raw451→移动460模型入口](reverse-engineering/reports/2026-11-02-raw-moving-rune0135.md)已另跑，79项终态模型组合一致，新增原件case仍为0；各批计数不相加。后续纯模型探路到920帧／7选／level8，停在玩家致死受伤边界，**新增原件case为0**；下一步恢复死亡／复活、冻结运动和失败recap，再做连续原件验证。[普通敌人来源163组完整1073与独审](reverse-engineering/reports/2026-11-02-incoming-source0135.md)补齐名称／分类→history组件，尚未接连续死亡。[死亡40组](reverse-engineering/reports/2026-11-02-player-death0135.md)与[recap103组](reverse-engineering/reports/2026-11-02-player-death-recap0135.md)已分别独审，但仅空地形组件域；实际非平地停止运动和有序AI队列仍待接，不能宣称完整失败一局。以下较早收据保持各自历史范围。

Aethus 原作游戏的非官方社区封装与逆向研究仓库。现有社区版本使用原作提供的核心，没有从原作 Rust 源码重新编译。

资源与运行逻辑分开：历史实验曾通过本机MPQ读取器提供包内文件；当前139世界构造使用原作静态资源中的WDT／ADT地图与M2／WMO模型等独立文件。既有[MPQ读取器](reverse-engineering/reconstruction/resource_spec/mpq.py)仅支持已明确实现的classic v0范围，不能据此称任意资源包都可直接使用。地图几何读取已验证，不代表贴图／材质／动画／音频或Logo来源全部恢复。

独立重建负责资源解析与加载、碰撞和导航、画面与动画，以及刷怪、技能、伤害、成长、存档和联机。复用素材本身不会恢复Azeroth Survivors的玩法规则；现有社区封装仍运行原作核心，与独立重建的验收分开。

## 两个板块

| 板块 | 工作范围 | 入口 |
|---|---|---|
| 封装优化 | Android／Mac 安装包、触控、界面、中文、性能、离线体验与合作兼容 | [封装优化](ports/README.md) |
| REA 逆向研究 | 用固定版本 REA 分析原始 JS、WASM 和 Windows 原生程序，追踪资源显示、技能数值与联网逻辑 | [REA 研究区](reverse-engineering/README.md) |

`android/`、`macos/` 保留现有构建、签名和存档路径；研究区独立保存工具入口、目标版本、问题清单和分析结论。研究补丁经过对应版本验证后，才能进入封装版。REA 分析结果不等于已经恢复完整源码。

逆向持续对齐官方最新稳定版，每轮固定版本与SHA。**此前核对的固定0.137.0 / `d171b8f9f`，已建立[175327函数完整静态profile](reverse-engineering/reports/2026-11-02-wasm0137-profile.md)，并取得[非致死伤害913的80组/125次完整调用0差异](reverse-engineering/reports/2026-11-02-combat0137.md)**；这是局部数值动态域，[限定数值域独审通过](reverse-engineering/reports/2026-11-02-combat0137-independent-review.md)，完整游戏帧/Windows原生执行仍为0。[0.136.0 / `fe24fb74c`](reverse-engineering/reports/2026-11-01-wasm0136-profile.md)保留完整静态profile与迁移候选，动态验收同样为0；开局组合动态实验继续固定在**0.135.1 / `90898d5e3`**。旧`0898d5e3`是历史截短alias，原收据不覆写，旧通过不转记136或137。

此前metadata核对截至 **2026-11-01T16:51:40Z**，官方manifest仍为同一137 EXE SHA、HTML stamp仍为`c628fd68823e`；仅复查清单/页面，未重取大二进制，见[核对收据](reverse-engineering/evidence/official-latest137-closecheck-20261101T165135.413048Z/receipt.json)。

固定135的[历史14阶段独立研究切片](reverse-engineering/reports/2026-11-01-headless-tail0135-independent-review.md)保留8种子1614帧22607阶段、11次选择、22615次原件入口调用0差异（67源/60core/16角色），其phase1/初始zero槽是该旧批研究输入。后续真实开局→战斗→升级与选卡组合使用新的135收据，不合并这些历史计数。0.134.0与0.126.0继续保留各自固定研究结果。

固定135新增[400帧／第四次选卡与Battle Shout组合](reverse-engineering/reports/2026-11-02-opening-battle-combat0135.md)：400受控帧／4select／5604stage／5606原件入口、0声明差异，98源／85 production；实际第379帧选择Battle Shout，随后完成6673施放、effect8与属性变化，最终level5／XP6／gold53。修复后fresh收据SHA `b5d9c546789401d738b43cc58cac1d7aeb117c94753ed4d63f60d923224520a7`，该限定投影已通过[400帧只读独审](reverse-engineering/reports/2026-11-02-opening-combat0135-400frame-independent-review.md)（receipt SHA `376b09cd9ce10da25396d815824432e48eb456dbb1aeaea9674db95d25aa6482`），核对24,443,084个已知叶；905包峰值及其未恢复的payload语义仍只观察。原件snapshot、独立预解析world与外部f32调度的范围保持明确，完整880／Windows执行／独立一局仍为0。

另有[raw451资源→world→opening→400帧](reverse-engineering/evidence/asset-combat400-owned-20261101T174254.757426Z/model400/receipt.json)纯modelselfcheck：67,281,330B、92源与资源前后不变，不读原件memory／WASM／预解析world，400帧／4select也达到level5／XP6／gold53；三项world SHA、四guardian实体／GUID／timer及None字节均核对。[35项终态衔接](reverse-engineering/evidence/asset-combat400-owned-20261101T174254.757426Z/projection-bridge.json)与差分组合一致；这层不新增原件case或完整880帧。

[Battle组件134组／171调用](reverse-engineering/reports/2026-11-02-battle-shout0135-independent-review.md)与[CAS codec两正例／26负例全拒绝](reverse-engineering/reports/2026-11-02-opening-combat0135-cas-codec-review.md)已分别通过各自范围独审。CAS保留6008条完整logical records（1,662,490,742B；unique blobs 83,331,346B），没有删阶段或字段；旧`171633.375141Z` decoder批与120／250 checkpoint保留，不与最终400计数相加。该400旧批当时的下一纯模型帧401为`pending_due_event:G2444`资源40秒到期；[资源组件64组](reverse-engineering/reports/2026-11-02-resource-spawn0135.md)单独差分0差异，未接入这批旧400；后继500使用独立新收据，不能倒填旧批。

固定135的[250帧守卫出生组合](reverse-engineering/reports/2026-11-02-opening-guardian-combat0135.md)完成250受控帧／3select／3503stage／3505原件调用、0差异，94源/84 production；跨20秒4守卫出生并继续50帧，U68地址保持None、timer所有者按GUID严格核payload。该限定投影已通过[最终只读独审](reverse-engineering/reports/2026-11-02-opening-combat0135-250frame-independent-review.md)（receipt SHA `556693d5bac9b86545dd89a57b042bdb54823e49d4f845b5547a3a978d7158c7`），仍是预解析world、原件snapshot及外部clock域；旧120收据保持原身份，不相加。

另有[raw451资产→world→opening→250帧](reverse-engineering/evidence/asset-combat250-owned-20261101T163850.979737Z/model250/receipt.json)的纯modelselfcheck：67,281,330B、91源前后不变，不读原memory/预解析world/WASM，250帧／3select至level4／XP3。复用同一world的[后继纯模型](reverse-engineering/evidence/asset-combat250-owned-20261101T163850.979737Z/continuation/receipt.json)继续至379帧／4select，第380帧因实际选到battle_shout停止；没有重抽卡。379是该旧模型的边界，当时原件差分到250；后继400验收另列，旧收据计数不改，完整880/native/一局仍为0。

此前固定135的[120帧真实开局→战斗→XP/首次选卡闭环](reverse-engineering/reports/2026-11-01-opening-combat0135.md)：单human warrior／seed0／navigation False，120受控帧、1次选择、1681阶段、1683原件入口0差异（90源/80 production）。phase1来自真实1089，六类opening对象保留实际capacity及None未知字节；level2实际选择index0的thunder_clap后继续33帧。模型使用预解析独立world，原件从合法snapshot恢复，时间由显式外部调度推进；尚非完整880、Windows执行或独立一局，旧回归与新case分别计数。 该限定投影已通过[只读独审](reverse-engineering/reports/2026-11-02-opening-combat0135-independent-review.md)，receipt SHA `2b768595711ff9f5daea0fcd718c4e963b8d2d02b652823285444000e2e96d2d`；原packet payload语义仍只观察。

同版另有[raw资产→world→opening→120帧独立入口](reverse-engineering/reports/2026-11-01-opening-combat0135.md)：真实451文件／67,281,330B、9tiles，87源前后不变；未读原memory、预解析world或WASM，三个world产物SHA与既有独立查询world一致，最终level2／XP6／gold7、1次选卡。它补足资产生产入口这一层，不增加上述原件差分case，也不等于完整880或完整一局。

新增[独立默认开局](reverse-engineering/reports/2026-11-01-opening0135.md)：16组、32次完整原件入口、0声明差异，连续产生2条附属对象、4NPC、2个kind2、事件声明及69个边界对象，六vector和全部新增消息均对照；[独审通过](reverse-engineering/reports/2026-11-01-opening0135-independent-review.md)。世界侧已有[M2碰撞／候选与导航生产](reverse-engineering/reports/2026-11-01-world-raster0135-independent-review.md)、[world查询与位置消费者](reverse-engineering/reports/2026-11-01-world-consumers0135-independent-review.md)独审通过，[WMO碰撞生产](reverse-engineering/reports/2026-11-01-wmo-geometry0135.md)覆盖实际readset全部410文件、[独审通过](reverse-engineering/reports/2026-11-01-wmo-geometry0135-independent-review.md)。该16组原件验收仍以已解析world为输入，尚未接入旧主切片；后继资产组合另列。

新增[451资源→Elwynn查询world→默认开局](reverse-engineering/reports/2026-11-01-asset-world0135.md)：生产过程不读snapshot或执行原程序，terrain规范投影4,022,968B、nav78,400B、secondary1,254,400B及78包与一份历史原件结果相符，[整体独审通过](reverse-engineering/reports/2026-11-01-asset-world0135-independent-review.md)。[placement13组原件验证](reverse-engineering/reports/2026-11-01-world-placements0135.md)与[cache静态恢复](reverse-engineering/reports/2026-11-01-world-cache0135.md)另计；该历史对照新增原件调用、bootstrap和主切片帧均为0。完整物理App/Rc/VFS所有权、其它地图、渲染与独立一局仍未完成。

新增App外围的独立组件：[transport43组/220调用](reverse-engineering/reports/2026-11-01-transport0135.md)限quiet域、宿主调用0；[空history与地址熵24组/96调用](reverse-engineering/reports/2026-11-01-app-history0135.md)只预测entropy的408B，另384B地址词保持opaque，四map为typed-state静态规则。[App构造32组静态重组](reverse-engineering/reports/2026-11-01-app-state0135.md)冻结10源、0新WASM调用；[真实cast投影](reverse-engineering/reports/2026-11-01-app-state0135-capture.md)730B中33B为显式输入、697B独立预测，4,438B保持None。四份组件/投影均已通过各自范围的独审，不增加旧主切片计数。

[自然原App/Metal观察](reverse-engineering/reports/2026-11-01-full-app0135-probe.md)（[观察独审通过](reverse-engineering/reports/2026-11-01-full-app0135-independent-review.md)）已显示正常中文角色选择页，8次完整idle880返回、0 page error、999次HTTP均200；App Game tag2，尚未进入一局。CSP阻止presence外发，不能称“没有联网尝试”。这是执行原程序的观察，独立gameplay帧仍为0；早期SwiftShader错误和首Metal批的研究observer/font边界完整保留，独立App/880及整局仍未恢复。

[真实世界与开局观察](reverse-engineering/reports/2026-11-01-entry-world0135-probe.md)的453份MPQ内文件／561次GET仍是历史原件观察；该历史资源/开局组合不增加bootstrap或主切片帧。history的[164组/924调用组件](reverse-engineering/reports/2026-11-01-incoming-history0135.md)与[真实DBC9组/37调用组合](reverse-engineering/reports/2026-11-01-browser-history0135-independent-review.md)分别保留，各层不相加。现有安装包不随研究目标自动更新，详见[版本策略](reverse-engineering/VERSION_STRATEGY.md)与[覆盖清单](reverse-engineering/RECONSTRUCTION.md)。

[真实915观测](reverse-engineering/reports/2026-11-01-effect-system0135-probe.md)确认本批时钟和两类效果队列保持空；后继主切片使用独立模型重新生成预期，保留原始三域读回。非空延迟动作另有500组对照（383正常、117预期原版错误），不代表全部915。完整880还缺其他入口、2376特殊事件及前段/party/终态组合，独立完整自然帧和独立一局未完成。

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
