# 版本与平台基线

当前功能目标已更新为**官方0.138.0**，Windows/Web原件均在4T另档并完成大小、哈希及采集前后部署一致性核对，见[138采集与版本状态](reports/2026-11-02-latest0138-state.md)。新版静态与动态证据单独登记；固定135连续流程、137局部组件的结果均不转记138。现有安装包和存档未替换。

当前[650帧／60秒波次与补给闭环](reports/2026-11-02-opening-event-combat0135.md)固定135：真实opening→战斗→5次选卡→首波次及补给→继续，9105阶段／9107原件入口0声明差异，104源／90production；[只读独审通过](reports/2026-11-02-opening-combat0135-650frame-independent-review.md)。新增全部150与声明actor169字节、GUID绑定的kind2地址来源比较。仍是原件snapshot／独立预解析world／外部clock控制的14尾阶段，完整880／Windows执行／独立完整一局均为0。

[原始451资源独立入口](evidence/asset-combat650-owned-20261101T201232.800315Z/model650/receipt.json)亦完成650帧／5select／9106摘要，97源及67,281,330B资产不变，不读原memory／WASM／预解析world；[50项终态衔接](evidence/asset-combat650-bridge-owned-20261101T202159.503837Z/projection-bridge.json)通过。这是模型自检／终态组合比较，不增加原件case。下一纯模型到665帧自然选中demo_shout后停止，不能称665原件差分；继续恢复该技能、资源消费与完整一局。以下较早记录保持各自历史范围和计数。

核对日期：2026-11-02（Asia/Taipei）。官方入口为 [wow.aethus.pl](https://wow.aethus.pl/)；`azerothsurvivors.io`自称非官方导航站，不以其版本说明作为原件身份。

**功能目标持续对齐官方最新稳定版；2026-11-01T16:21Z当时核实的固定参照为0.137.0 / `d171b8f9f`，现有[完整175327函数profile](reports/2026-11-02-wasm0137-profile.md)及[非致死伤害80组/125原件调用0差异](reports/2026-11-02-combat0137.md)，局部动态[限定数值域独审通过](reports/2026-11-02-combat0137-independent-review.md)。固定0.136.0 / `fe24fb74c`保留静态profile与迁移候选，动态验收0；开局组合动态实验仍锁定0.135.1 / `90898d5e3`。** 每轮先固定版本、SHA与资源输入，不能把浮动latest换入正在运行的实验，或把静态同形当新版通过。旧`0898d5e3`是实际9字节Web build的历史截短alias，原收据不覆写；0.134.0与0.126.0也保留各自身份。详见[先前身份采集状态](reports/2026-11-01-latest-version-state.md)。

此前metadata核对截至 **2026-11-01T16:51:40Z**，官方manifest仍为同一137 EXE SHA、HTML stamp仍为`c628fd68823e`；仅复查清单/页面，未重取大二进制，见[核对收据](evidence/official-latest137-closecheck-20261101T165135.413048Z/receipt.json)。

## 目标与固定参照

| 角色 | 版本/身份 | 用法 |
|---|---|---|
| latest Windows程序目标 | 官方更新EXE0.137.0，147844608B，SHA `aa6b254f…3a10dc8`，实际build `d171b8f9f` | 新目录已核官方大小/SHA及gzip CRC/ISIZE，未执行EXE；原生/游戏语义验收0。 |
| latest Web目标 | Web0.137.0/`d171b8f9f`，90941108B，SHA `20ec9a2b…3fe1c8`，stamp `c628fd68823e` | coherent下载及真实pointer/len9 guard通过；完整profile及913局部非致死80/125动态0差异。完整death/proc/native运行/fullgame仍未验收。 |
| 固定0.136静态迁移 | Web0.136.0/`fe24fb74c`，90927420B，SHA `48c3bce7…1eb2eef3`；native SHA `eb744751…c4d8947c` | [完整175319函数profile/RO索引与12入口候选](reports/2026-11-01-wasm0136-profile.md)保留；动态case0，不能转计137。 |
| 固定0.135动态研究 | Web0.135.1/`90898d5e3`，90959080B，SHA `c62c85f5…0dc96e2`；历史alias `0898d5e3` | 原52-role与私有builder及既有收据继续绑定该SHA。后继真实开局/战斗/升级/选卡组合另记，旧082927等计数不合并，完整880、native与独立一局仍缺。 |
| 固定0.135 Windows参照 | 官方EXE0.135.1，147797504B，SHA `71e5f176…bc59249` | 保留原采集身份，未执行EXE；Web结果不冒称native验收。 |
| 历史规则和差分参照 | Web 0.126.0 / 3e72472a，WASM SHA `06705937…b147c` | 保留所有既有规格、输入和证据作迁移/回归；固定版本工具继续拒绝其他原件，不再作主目标扩展。 |
| 固定 Windows 原生研究基线 | 官方更新 EXE 0.134.0，147793408B，SHA `ed7dc687…1a3f6` | 核对原生离线发行、平台行为和同源游戏规则；每个原生地址重新定位。 |
| 本轮App外围与自然启动 | transport43/220 quiet0host、history24/96、App32static/10源、既有cast730B投影及自然原App/Metal观察分别记录 | entropy只比已知408B、384B opaque；cast33B输入/697B预测。中文角色选择页和8idle880是原程序观察，Game tag2未开局，不是独立App/880或完整游戏。 |
| 固定同版WASM研究基线 | Web 0.134.0 / 983346a7，90953762B，SHA `2e86455a…73d52` | 已建立若干局部独立实现/原件差分；不代表完整游戏实现，也不代表0.135.1验收。 |

完整SHA与来源在[targets.json](targets.json)和相应报告。Windows版本/大小/SHA匹配[官方更新清单](https://wow.aethus.pl/exe/latest.json)；WASM身份是从本次HTTPS下载和内嵌菜单branding确认，未取得另行发布的官方WASM SHA。相同版本号不代表不同平台的二进制、布局或所有行为必然相同。

现有Mac/Android安装包没有随研究快照升级。旧Windows0.102.3仍保留为历史参考，偏移不能套到其他版本；Web差分不冒称原生EXE执行。

## 更新版本如何继续

最终功能对齐应选择明确的目标版本；研究期间不跟随“latest”浮动覆盖输入。保留已有固定基线，为新版本建立独立SHA/数据目录和差分清单。相同规则复用独立实现及语料，新功能或行为变化作为同一项目的增量模块推进。引擎、协议、资源格式若发生实质变化，要重新验证受影响模块；不是把所有已有成果作废。

此前0.134.0更新说明包含增强萨满/天赋重做、新饰品以及Ice Barrier上限变化。因此不能只因升级系数相同，就把0.126.0的整套行为标为0.134.0已支持。

此前取得0.135.1时，官方说明为修复0.135.0角色面板报错、缺少本局数值。更新说明只能指引排查，不能证明其他逻辑必然未改。manifest、EXE和Web各自身份已保存，见[当时的采集报告](reports/2026-11-01-official-0135-acquisition.md)；代码/数据变化按固定版本另验。新版本作为同一项目的增量迁移，无需重新立项。研究输入始终锁定版本与SHA，不能在一次实验中被浮动latest替换。

后继0.136.0的clock选项/API更新已单独完成静态profile与引用候选审查；0.137.0又宣布增强萨满proc互相触发、武器附魔/项链重做与两个新天赋。公告只能指引迁移排查，不证明其它路径未变。137原件另档，136静态工作及135动态实验分别保留，不能共用一个“本轮通过”标签。135/136的9字节build身份由[真实pointer/length sidecar](evidence/branding0136-identity-20261101T145343.493343Z/identity.json)确认，137也有独立[指令guard](evidence/branding0137-identity-20261101T154758.086510Z/identity.json)，不再凭固定8位regex截取。

固定135的新[真实opening→combat→XP/首次选卡闭环](reports/2026-11-01-opening-combat0135.md)为单case human warrior／seed0／navigation False：120受控帧、1次实际选择、1681阶段、1683次原件入口，0差异，90源含80 production。真实1089产生phase1及实际capacity，None未知字节不清零；首次level2的index0确为thunder_clap，随后继续33帧。模型使用预解析独立world，原件使用合法snapshot，clock由显式外部调度推进；它不是完整880、Windows执行或完整一局。旧headless/frame/death-pickup回归各自另记，不与该新case相加。

本版[目录重提](reports/2026-11-01-catalogue0135.md)还发现真实平衡差异：rockbiter伤害120→132、冷却1.786→1.3571429、范围5→10；stormstrike冷却7→6.0714288、范围6→10。原始位保留在JSON，不能把相对0.135.0的单条修复说明当作0.134.0→0.135.1完整差异。

新版各组件与组合各自验收，计数不相加。当前共享52角色只是白名单；[52保守性证明](evidence/builder135-role52-review-20261101T083845.125766Z/review.json)重建旧9-role模块字节一致、无新增runtimecase。9role snapshot和私有M2四／WMO两role只各实验准入，不改变共享角色数或代表恢复比例。主Node及M2／WMO fresh域32MiB／878deny；query／position／opening snapshot域256MiB／878deny、正常返回栈1048576。历史history／resource browser128MiB／17允许861拒绝和world browser256MiB／24允许854拒绝分开保留。

本次已取得两个层次的复用证据：

- 在0.134.0 Web中，旧0.126.0的95640/95641的两条成长曲线分别在95996/95997找到完整相同body；旧35684半径helper对应35876，旧85387舍入对应85718，原体SHA均相同。只是body身份匹配，调用者状态与ABI未由此推定。
- 在0.134.0 Windows中，从该版`.pdata`和五组表重新定位两段原生函数，五分支升级结构及五张表与既有Web规格一致，字段偏移不同；这是静态原生指令证据，不是Windows运行差分。见[新版原生函数](reports/2026-11-01-latest-native-focused.md)。

0.134.0→0.135.1已建立[完整新profile](reports/2026-11-01-wasm0135-profile.md)和[角色/布局映射](reports/2026-11-01-migration0135.md)。新原分配器为91941、属性入口1512，等级/HP/派生字段发生重排；舍入/成长/半径四个leaf对应体完全相同。[属性23词投影](reports/2026-11-01-stats0135-spec.md)已重新执行原件10569例通过，新增G1572明确为护甲上限；[tick/暂停命令投影](reports/2026-11-01-game-loop0135.md)另做6558例新版原件对照，限定空队列/无单位与原skip-spawn域；tick其他phase、完整调度和fresh终局保存仍pending。编号相同的其他函数也仍须分别验收。

新增验证分开记录：[空profile构造151](reports/2026-11-01-initial0135-independent-review.md)、[死亡placement924](reports/2026-11-01-ordinary-placement0135.md)、[真实racial720](reports/2026-11-01-racial-cast0135.md)、[kind27事件855](reports/2026-11-01-proc-events0135.md)、[trig6726/AI429组3423步](reports/2026-11-01-ai-motion0135.md)、[玩家更新/尸体285组444阶段](reports/2026-11-01-player-update0135.md)、[移动暂停396组1136阶段](reports/2026-11-01-movement-pause0135.md)。旧12组definition差异已在显式非致死context0域解释并重验；致死loot之后proc顺序仍未知。G1256是racial，旧639批basic是effect0隔离fixture，不能追溯称其验证了真实racial。

历史[同状态研究切片061901](reports/2026-11-01-headless0135.md)与[独审062623](reports/2026-11-01-headless0135-independent-review.md)验证8种子1093帧5473阶段及8次自然选择；seed3选卡后继续145帧至250，另7种子在未支持新技能前停止。phase1和初始128个全零单位槽是显式研究输入，该旧纯Node批的1089/2328在SELF/data被拒绝；后继browser已实际完成真实world/1089与4NPC/2kind2，但该旧独立模型不因此获得入口支持。全槽保留和复用、HP/RNG、真实racial、暂停/恢复序号与七个numeric keys均对照，其它keyed state单列未知。[默认扩展回归639/5068](reports/2026-11-01-default-extension0135-regression.md)不重复计新增覆盖。持续AoE693/5495组件已获独审通过，并接入后继[064308同状态切片](reports/2026-11-01-headless-area0135.md)：8seed/1614帧/9695阶段/11select、0差异。seed1/6各400帧，seed3到257帧后因cone_of_cold未知停止，其余未知不删；新area128槽88B初始内存同样是显式研究输入。后继[独立复核](reports/2026-11-01-headless-area0135-independent-review.md)已通过，前阶段次数不与后继相加。

当前[14阶段独立切片](reports/2026-11-01-headless-tail0135.md)：8seed/1614帧/22607阶段/11选择/22615原件调用，67源含60core、16角色，0差异。[旧072329](reports/2026-11-01-headless-effects0135.md)11309阶段仅作历史。14尾observer另记录3038帧/42550快照/18选择/42558调用、6预算及2phase4，未形成相同长度的独立模型。[五阶段组件573/944](reports/2026-11-01-frame-systems0135.md)、[真实胜利终态416/832及416构造](reports/2026-11-01-terminal-transition0135.md)、[107完整ADT/18413调用](reports/2026-11-01-terrain0135.md)、[真实Boss矩形390](reports/2026-11-01-effect-geometry0135.md)分别验收，不与主切片相加。[真实浏览器资源链](reports/2026-11-01-browser-resources0135.md)另以原生SELF/XHR完成3组phase1命中/15已恢复投影；17资源绑定允许、861拒绝、128MiB，区别于纯Node878全拒绝/32MiB。history后继独立组件与真实DBC组合另列，来源容器/keyed/proc完整尾部仍缺。 [浏览器独审](reports/2026-11-01-browser-resources0135-independent-review.md)通过，未重跑原件。

history的[164组/924调用组件](reports/2026-11-01-incoming-history0135-independent-review.md)与[真实DBC9fresh/37调用](reports/2026-11-01-browser-history0135-independent-review.md)分层保留；[真实world/1089观察](reports/2026-11-01-entry-world0135-probe-independent-review.md)的453MPQ／561GET仍是历史原件观察、独立模型case0，未因后继模型而改记。

本轮独立world组件包括[query959/1858与新position96/96、30源闭包联合独审](reports/2026-11-01-world-consumers0135-independent-review.md)、[真实31M2／raster114/1477最终独审](reports/2026-11-01-world-raster0135-independent-review.md)，以及[实际410WMO碰撞425/830](reports/2026-11-01-wmo-geometry0135.md)（[独审通过](reports/2026-11-01-wmo-geometry0135-independent-review.md)）。[1744／1821组件27/116独审](reports/2026-11-01-opening-entities0135-independent-review.md)通过；[整条默认开局16/32](reports/2026-11-01-opening0135.md)冻结39源、六vector及1248包／16start逐字相符，[独审通过](reports/2026-11-01-opening0135-independent-review.md)。该16组入口批world仍为显式解析输入；后继[placement13/13](reports/2026-11-01-world-placements0135.md)、[cache生产/静态独审](reports/2026-11-01-world-cache0135-independent-review.md)与[451资源组合](reports/2026-11-01-asset-world0135.md)独立生成默认Elwynn查询world并继续开局，1历史case、[整体独审通过](reports/2026-11-01-asset-world0135-independent-review.md)。不增加新原件case/bootstrap/主切片帧；物理App/Once/Rc/VFS所有权、其它地图、渲染／动画及接旧主切片仍缺。

没有直接body匹配的函数也不能立即判定规则变化：call索引、静态地址、编译布局可能改变字节。需在语义、常量、输入输出与具体副作用层继续核对。当前仍以[全模块清单](RECONSTRUCTION.md)记录未知项，不将旧版验证次数移作新版验收。

当前[独立复制运行](evidence/headless-tail135-standalone-20261101T083836.389587Z/receipt.json)61文件=60core+CLI，默认0帧停真实进场边界，显式研究输入下seed1/6各400、seed3到257；纯模型自跑不新增原件case。新资产开局另有纯模型CLI，但尚未接该旧headless CLI，旧phase1边界保持。活跃916/975 execution11/2602/2573/2376、915其余类型、前段/party/完整880、完整物理world／菜单profile／其它地图模式／非空装备天赋、全部技能AI／存档UI网络与独立完整一局仍缺。

[完整880上下文静态记录](evidence/full880-context0135-static-20261101T111231.254023Z/notes.md)保留原历史身份；后继[transport43/220](reports/2026-11-01-transport0135.md)、[history24/96](reports/2026-11-01-app-history0135.md)、[App32组静态重组](reports/2026-11-01-app-state0135.md)及[真实cast730B投影](reports/2026-11-01-app-state0135-capture.md)分别独审通过，不新增主切片帧。[自然原App/Metal观察](reports/2026-11-01-full-app0135-probe.md)（[观察独审通过](reports/2026-11-01-full-app0135-independent-review.md)）显示正常中文角色选择页并返回8次完整idle880，999HTTP200、0 page error；CSP拦截presence外发，不能说无联网尝试。早期SwiftShader真实GPU失败、首Metal研究observer达1M事件上限throw及字体404原样保留。这是单独的真实浏览器/GPU宿主域，不套旧32/128/256MiB或有限import政策；Game tag2未开局，0独立gameplay帧，完整独立App/880及一局仍缺。未来每轮继续核实latest稳定版，并在新固定版本/SHA批次增量迁移；这些0.135.1结果不外推到后续版本。

2026-11-01T13:26:11Z再次核对官方manifest与本地Windows SHA，仍为0.135.1。后继[自然UI→运行态Game](reports/2026-11-01-game-entry0135-probe.md)及[独审](reports/2026-11-01-game-entry0135-independent-review.md)观察603次完整880，其中8running/7clock推进；全量coherent memory为1,378,877,440B。它使用独立2GiB WASM/512MiB解码资产/8192文件政策，原件行为观察不增44独立domain或主切片帧；不是原生Windows执行或独立一局。

## Windows与WASM的分工

Windows原生版提供实际离线发行的程序、平台接口和资源组织。WASM同样是编译后的真实游戏核心；结构化控制流、完整指令解码和受控函数导出让规则恢复与原件差分更容易。两者应互证。此前的HTML/JS启动桥调查不代表只在分析浏览器界面；已有规则来自WASM内的真实计算和状态写入。

本次0.134.0 EXE有Rust/Bevy、wgpu/winit及Win32正面证据，确认是原生程序，见[静态拆分报告](reports/2026-11-01-official-windows-0134-static.md)。这是新增的重要原生基线，同时继续保留WASM为规则拆解与可执行对照入口。

macOS可直接用Ghidra/REA和PE解析器静态分析x86-64 Windows程序，无需先运行Windows目标。本次实际使用项目内Ghidra12.1.4/JDK21 ARM64、LLVM objdump、Python PE/资源/常量解析；没有执行EXE、Wine或虚拟机。

## 下载与原件保存

所有新下载、解压和下载证据均在4T外盘的`reverse-engineering/originals/`或`evidence/`，每次创建独立时间目录。原0.134.0采集位于`official-acquisition-20261031T235700.049192Z/`，0.135.1、0.136.0分别另存；最新137为`official-acquisition-20261101T154517.001467Z/`。官方更新分块拼接gzip并读至EOF核CRC/ISIZE，解压EXE匹配各自官方大小/SHA；不替换原研究输入、用户安装包或存档。

完整资源RAR已复用用户原有4T文件，完成全包CRC与8个提取文件SHA复核，含7个MPQ；对应官方已验证HTTP块及末尾共289411072B一致，没有把本地整包SHA说成官方发布的SHA。包内139691008B EXE仍与历史Windows0.102.3 / f78e6fab完全相同。官网RAR提供旧版基础程序/资源，新版程序须取官方更新清单，不能仅下载RAR就称为最新版。详见[资源验收](reports/2026-11-01-resource-acquisition.md)。基础资源的[MPQ索引/独立读取器及DBC容器](reports/2026-11-01-resource-index-base.md)已验收29602命名块/1636167198B与154份DBC。实际31M2／410WMO及后继451资产已用于默认Elwynn查询world历史对照，仍不证明基础包等于新版全部资产；物理场景/VFS所有权、其它地图、列/玩法ID关联、动画／材质／音画与渲染继续待恢复。

程序、WASM、RAR、完整反编译及工具产物均为ignored本地研究资料，不进入Git。提交的是可复现脚本、独立实现和结论；封装优化继续使用各自固定版本和回归流程。

白名单扩展的只读保守性核对还确认：使用同一旧角色集合时，tick/command与1512统计research模块逐字节保持原SHA，证据`evidence/builder135-extension-review-20261101T040956.409250Z/`。新builder来源hash不追溯替代旧收据；新旧输入和原件身份继续按各自快照核对。

固定135新增[400帧／第四次选卡与Battle Shout组合](reports/2026-11-02-opening-battle-combat0135.md)：400受控帧／4select／5604stage／5606原件入口、0声明差异，98源／85 production；实际第379帧选择Battle Shout，随后完成6673施放、effect8与属性变化，最终level5／XP6／gold53。修复后fresh收据SHA `b5d9c546789401d738b43cc58cac1d7aeb117c94753ed4d63f60d923224520a7`，该限定投影已通过[400帧只读独审](reports/2026-11-02-opening-combat0135-400frame-independent-review.md)（receipt SHA `376b09cd9ce10da25396d815824432e48eb456dbb1aeaea9674db95d25aa6482`），核对24,443,084个已知叶；905包峰值及其未恢复的payload语义仍只观察。原件snapshot、独立预解析world与外部f32调度的范围保持明确，完整880／Windows执行／独立一局仍为0。

另有[raw451资源→world→opening→400帧](evidence/asset-combat400-owned-20261101T174254.757426Z/model400/receipt.json)纯modelselfcheck：67,281,330B、92源与资源前后不变，不读原件memory／WASM／预解析world，400帧／4select也达到level5／XP6／gold53；三项world SHA、四guardian实体／GUID／timer及None字节均核对。[35项终态衔接](evidence/asset-combat400-owned-20261101T174254.757426Z/projection-bridge.json)与差分组合一致；这层不新增原件case或完整880帧。

[Battle组件134组／171调用](reports/2026-11-02-battle-shout0135-independent-review.md)与[CAS codec两正例／26负例全拒绝](reports/2026-11-02-opening-combat0135-cas-codec-review.md)已分别通过各自范围独审。CAS保留6008条完整logical records（1,662,490,742B；unique blobs 83,331,346B），没有删阶段或字段；旧`171633.375141Z` decoder批与120／250 checkpoint保留，不与最终400计数相加。该400旧批当时的下一纯模型帧401为`pending_due_event:G2444`资源40秒到期；[资源组件64组](reports/2026-11-02-resource-spawn0135.md)单独差分0差异，未接入这批旧400；后继500使用独立新收据，不能倒填旧批。

固定135的[250帧守卫出生组合](reports/2026-11-02-opening-guardian-combat0135.md)完成250受控帧／3select／3503stage／3505原件调用、0差异，94源/84 production；跨20秒4守卫出生并继续50帧，U68地址保持None、timer所有者按GUID严格核payload。该限定投影已通过[最终只读独审](reports/2026-11-02-opening-combat0135-250frame-independent-review.md)（receipt SHA `556693d5bac9b86545dd89a57b042bdb54823e49d4f845b5547a3a978d7158c7`），仍是预解析world、原件snapshot及外部clock域；旧120收据保持原身份，不相加。

另有[raw451资产→world→opening→250帧](evidence/asset-combat250-owned-20261101T163850.979737Z/model250/receipt.json)的纯modelselfcheck：67,281,330B、91源前后不变，不读原memory/预解析world/WASM，250帧／3select至level4／XP3。复用同一world的[后继纯模型](evidence/asset-combat250-owned-20261101T163850.979737Z/continuation/receipt.json)继续至379帧／4select，第380帧因实际选到battle_shout停止；没有重抽卡。379是该旧模型的边界，当时原件差分到250；后继400验收另列，旧收据计数不改，完整880/native/一局仍为0。
