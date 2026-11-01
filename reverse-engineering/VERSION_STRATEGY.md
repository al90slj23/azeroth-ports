# 版本与平台基线

核对日期：2026-11-01（Asia/Taipei）。官方入口为 [wow.aethus.pl](https://wow.aethus.pl/)；`azerothsurvivors.io`自称非官方导航站，不以其版本说明作为原件身份。

**按用户方向，功能对齐采用本次已取得并固定SHA的官方0.135.1 / Web0898d5e3。Windows与Web原件均已核验；独立默认开局已在解析world输入上完成差分，旧主切片保持原范围。完整asset→world生产、开局接主切片、完整调度和独立一局尚未闭合。0.134.0保留固定局部结果；0.126.0仅保留历史验证与回归参考。**

## 目标与固定参照

| 角色 | 版本/身份 | 用法 |
|---|---|---|
| 最新Windows功能目标 | 官方更新EXE 0.135.1，147797504B，SHA `71e5f176…bc59249` | 官方大小/SHA与gzip CRC/ISIZE通过；未执行EXE，语义迁移待验。 |
| 最新Web功能目标 | Web0.135.1/0898d5e3，90959080B，SHA `c62c85f5…0dc96e2` | 共享52角色guard；主切片仍082927的8/1614/22607/11/22615、67源60core16角色。另有独立开局16/32与M2／WMO／查询／位置组件；完整world、开局接主切片、880和一局仍缺。 |
| 历史规则和差分参照 | Web 0.126.0 / 3e72472a，WASM SHA `06705937…b147c` | 保留所有既有规格、输入和证据作迁移/回归；固定版本工具继续拒绝其他原件，不再作主目标扩展。 |
| 固定 Windows 原生研究基线 | 官方更新 EXE 0.134.0，147793408B，SHA `ed7dc687…1a3f6` | 核对原生离线发行、平台行为和同源游戏规则；每个原生地址重新定位。 |
| 固定同版WASM研究基线 | Web 0.134.0 / 983346a7，90953762B，SHA `2e86455a…73d52` | 已建立若干局部独立实现/原件差分；不代表完整游戏实现，也不代表0.135.1验收。 |

完整SHA与来源在[targets.json](targets.json)和相应报告。Windows版本/大小/SHA匹配[官方更新清单](https://wow.aethus.pl/exe/latest.json)；WASM身份是从本次HTTPS下载和内嵌菜单branding确认，未取得另行发布的官方WASM SHA。相同版本号不代表不同平台的二进制、布局或所有行为必然相同。

现有Mac/Android安装包没有随研究快照升级。旧Windows0.102.3仍保留为历史参考，偏移不能套到其他版本；Web差分不冒称原生EXE执行。

## 更新版本如何继续

最终功能对齐应选择明确的目标版本；研究期间不跟随“latest”浮动覆盖输入。保留已有固定基线，为新版本建立独立SHA/数据目录和差分清单。相同规则复用独立实现及语料，新功能或行为变化作为同一项目的增量模块推进。引擎、协议、资源格式若发生实质变化，要重新验证受影响模块；不是把所有已有成果作废。

此前0.134.0更新说明包含增强萨满/天赋重做、新饰品以及Ice Barrier上限变化。因此不能只因升级系数相同，就把0.126.0的整套行为标为0.134.0已支持。

本次又发现0.135.1，官方说明为修复0.135.0角色面板报错、缺少本局数值。更新说明只能指引排查，不能证明其他逻辑必然未改。manifest、EXE和Web各自身份已保存，见[新版采集报告](reports/2026-11-01-official-0135-acquisition.md)；接着核对代码/数据差异，相同模块复用独立实现及既有输入，变化模块补规格和差分。新版本作为同一项目的增量迁移，无需重新立项。研究输入始终锁定版本与SHA，不能在一次实验中被浮动latest替换。

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

本轮独立world组件包括[query959/1858与新position96/96、30源闭包联合独审](reports/2026-11-01-world-consumers0135-independent-review.md)、[真实31M2／raster114/1477最终独审](reports/2026-11-01-world-raster0135-independent-review.md)，以及[实际410WMO碰撞425/830](reports/2026-11-01-wmo-geometry0135.md)（[独审通过](reports/2026-11-01-wmo-geometry0135-independent-review.md)）。[1744／1821组件27/116独审](reports/2026-11-01-opening-entities0135-independent-review.md)通过；[整条默认开局16/32](reports/2026-11-01-opening0135.md)冻结39源、六vector及1248包／16start逐字相符，[独审通过](reports/2026-11-01-opening0135-independent-review.md)。world仍为已解析snapshot输入，完整instances／placement／transform／secondary merge／cache／nav／VFS／所有权生产、渲染／动画以及开局接旧主切片未完成；本轮新bootstrap0、主切片帧0。

没有直接body匹配的函数也不能立即判定规则变化：call索引、静态地址、编译布局可能改变字节。需在语义、常量、输入输出与具体副作用层继续核对。当前仍以[全模块清单](RECONSTRUCTION.md)记录未知项，不将旧版验证次数移作新版验收。

当前[独立复制运行](evidence/headless-tail135-standalone-20261101T083836.389587Z/receipt.json)61文件=60core+CLI，默认0帧停真实进场边界，显式研究输入下seed1/6各400、seed3到257；纯模型自跑不新增原件case。新开局模块尚未接该CLI，旧phase1边界保持。活跃916/975 execution11/2602/2573/2376、915其余类型、前段/party/完整880、完整world／菜单profile／其它地图模式／非空装备天赋、全部技能AI／存档UI网络与独立完整一局仍缺。

## Windows与WASM的分工

Windows原生版提供实际离线发行的程序、平台接口和资源组织。WASM同样是编译后的真实游戏核心；结构化控制流、完整指令解码和受控函数导出让规则恢复与原件差分更容易。两者应互证。此前的HTML/JS启动桥调查不代表只在分析浏览器界面；已有规则来自WASM内的真实计算和状态写入。

本次0.134.0 EXE有Rust/Bevy、wgpu/winit及Win32正面证据，确认是原生程序，见[静态拆分报告](reports/2026-11-01-official-windows-0134-static.md)。这是新增的重要原生基线，同时继续保留WASM为规则拆解与可执行对照入口。

macOS可直接用Ghidra/REA和PE解析器静态分析x86-64 Windows程序，无需先运行Windows目标。本次实际使用项目内Ghidra12.1.4/JDK21 ARM64、LLVM objdump、Python PE/资源/常量解析；没有执行EXE、Wine或虚拟机。

## 下载与原件保存

所有新下载和解压原件均保存在4T外盘的`reverse-engineering/originals/`，每次采集创建独立时间目录。原0.134.0采集位于`official-acquisition-20261031T235700.049192Z/`：三个官方更新分块拼成gzip流，解压CRC/ISIZE通过，得到匹配官方SHA的EXE。0.135.1另存，保留原研究输入。

完整资源RAR已复用用户原有4T文件，完成全包CRC与8个提取文件SHA复核，含7个MPQ；对应官方已验证HTTP块及末尾共289411072B一致，没有把本地整包SHA说成官方发布的SHA。包内139691008B EXE仍与历史Windows0.102.3 / f78e6fab完全相同。官网RAR提供旧版基础程序/资源，新版程序须取官方更新清单，不能仅下载RAR就称为最新版。详见[资源验收](reports/2026-11-01-resource-acquisition.md)。基础资源的[MPQ索引/独立读取器及DBC容器](reports/2026-11-01-resource-index-base.md)已验收29602命名块/1636167198B与154份DBC。实际31M2／410WMO另完成碰撞投影，仍不证明基础包等于新版全部资产；完整场景加载、列/玩法ID关联、动画／材质／音画与渲染继续待恢复。

程序、WASM、RAR、完整反编译及工具产物均为ignored本地研究资料，不进入Git。提交的是可复现脚本、独立实现和结论；封装优化继续使用各自固定版本和回归流程。

白名单扩展的只读保守性核对还确认：使用同一旧角色集合时，tick/command与1512统计research模块逐字节保持原SHA，证据`evidence/builder135-extension-review-20261101T040956.409250Z/`。新builder来源hash不追溯替代旧收据；新旧输入和原件身份继续按各自快照核对。
