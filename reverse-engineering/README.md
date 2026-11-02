# REA 逆向研究

官方元数据于 **2026-11-02T10:24:12Z** 再核仍为 **0.139.0**，首页stamp `f339dd20e0fe`。已完成[官方Windows／Web一致获取与实际9B构建身份](reports/2026-11-02-official0139-acquisition-identity.md)：两端均为 `f79c5e2b4`，Windows150,595,584B／官方SHA匹配，Web92,511,151B／本地SHA固定；获取前后元数据逐字一致。[139完整静态索引与增量清单](reports/2026-11-02-engine0139-incremental.md)已固定177101函数／882导入、30/30主要入口身份；本轮核对143行技能／职业／种族／地图声明一致，19个入口仍有编译或结构差异，不能据此判行为等价。首次下载与工具失败均保留，139其他行为迁移另行验证，**不将旧版通过转记139**。现有安装包与存档未替换。

最新139的[限定非致死伤害80组／125完整913调用](reports/2026-11-02-combat0139.md)已重新执行新版原件，0声明差异，[异作者独审通过](reports/2026-11-02-combat0139-independent-review.md)。新版真实单位stride为432、导入882；完整单位字节与声明的HP／累计伤害／RNG等比较通过。合成Game／空items、spells、1972 proc队列／无context的边界明确：不代表完整Game、自然构造、死亡、原生Windows或完整一局。Pilot4组／5调用另存，不加入正式80／125。

139的[属性重算10569组／10569完整1542调用](reports/2026-11-02-stats0139.md)亦已重新执行新版原件，359346个声明值0差异，[异作者独审通过](reports/2026-11-02-stats0139-independent-review.md)。七组来源、当前139表、NaN分类及负零均按本体重核；1537条速度队列只核数量，不称包字节已恢复。完整BTree／Game、自然producer与全局流程仍未知，12次pilot不计入正式批。

139的[默认空profile构造162次完整1600](reports/2026-11-02-initial-state0139.md)也已完成新原件差分和[独立复核](reports/2026-11-02-initial-state0139-independent-review.md)：81324个已知字节、40条完整226包0差异；338580字节保留None，其中实际非零未反填。此域使用明确借用的flat V128查询输入，Game2592未完整预测，cached6786仅静态、opening1108未执行、未进入phase1；研究pilot与此前162批不加算。真实139 world／opening另行观察，不能当作独立开局或完整游戏通过。

139已取得[修正后的真实world／1108上下文v2](reports/2026-11-02-entry-world0139-context-v2.md)，并经[独立只读复核](reports/2026-11-02-entry-world0139-context-v2-independent-review.md)通过受控观察gate：2945完整返回36B、显式40B输出与两侧16B保护区合法，两份新memory分别为111MB／177MB，phase0→1与4NPC／2pickup／69boundary等原件状态已保存。旧16B输出区批次[明确不接受](reports/2026-11-02-entry-world0139-context-independent-review.md)，旧源码与快照字节均保留，未据越界直接推定堆破坏。v2仍是researchApp与selected376受控输入，且tag255／inactiveA5与先前全零profile构造域有差别：该v2观察批自身没有独立开局model case；后继完整1108验收另记，不能把本观察当完整自然App或独立开局验收。

139的[四只初始普通敌人生产](reports/2026-11-02-npc-spawn0139.md)完成16组／64次完整5719与[独审](reports/2026-11-02-npc-spawn0139-independent-review.md)：真实1600作为16次setup，0快照恢复，64条新169消息／432B记录已知字节一致；31056个未知字节保留None。位置由显式SomeXYZ输入，不能称自然刷怪或完整1108。

139的[受击与历史前缀](reports/2026-11-02-incoming0139-prefix.md)99组／164次完整1076，经[独审](reports/2026-11-02-incoming0139-prefix-independent-review.md)核对当前分类424、护盾736／740、modifier54按当前雷盾等级3%及历史记录。后继[护盾清理→1173 Aura→HP／历史](reports/2026-11-02-incoming-aura0139.md)另有36组／39次入口（31次1076＋8次直接1173），[独审](reports/2026-11-02-incoming-aura0139-independent-review.md)核对48个tag-only Aura与66个条件更新字段；1173未调用1542。两域分别验收，真实83304／1600只作setup，不加入组件覆盖。正reserve溢出、非空保留来源、回调、致死与复活仍有缺口。

139的[原始451资源→独立查询world](reports/2026-11-02-world0139.md)已从本轮原始资源生产5355768B地形／导航／二级高度，与合法v2原件观察完全一致；新3368组／6671次原件查询入口尝试亦0差异，其中6670正常返回、1次预期越界终止。[异作者独审](reports/2026-11-02-world0139-independent-review.md)独立重建9份ADT地形并重算全批查询。导航／二级高度几何生产未另写第二套pipeline，复核范围为源码／读取审计与v2全字节一致；原件查询使用合法v2快照，独立模型不读快照。完整Rc／cache／App／渲染／游戏流程仍未验收。

刷怪位置v1的80组原件输出虽一致，[独审明确拒绝其源码精度差异](reports/2026-11-02-world-position0139-independent-review.md)，旧10件作者文件与原件80批保持原样。另立的[位置v2](reports/2026-11-02-world-position0139-v2.md)重新执行85次原件（63次8740＋22次13563），[异作者独审通过](reports/2026-11-02-world-position0139-v2-independent-review.md)：13563前12次trial使用f32乘法／加法／sqrt，8740保留50441的f64中间值hypot；5个实地图反例都由原件支持v2、拒绝旧算式，RNG相同但旧XYZ不同。旧80结果未转计为通过，v2期待来自独立raw139世界，原件侧仍明确使用合法v2快照。冗余validator准备的45秒超时与其未预登记PID限制保留；本轮Node重新compile，旧validator收据只对应完全相同的module字节，不代替新行为差分。

[空account2945／开场150包](reports/2026-11-02-opening-profile0139.md)另有89次新原件入口（18次2945＋71次18062）与[异作者独审](reports/2026-11-02-opening-profile0139-independent-review.md)：合法40B输出720字节与完整UTF8载荷12329字节完全一致，含中文／emoji／容量边界。30个实际写入字节与10个原有padding／tail字节区分清楚；指针及stack padding只观察。6786 seed LCG和完整1108阶段清单仍是静态证据，此批不验收自然account／App／localization producer。

[自然四敌人组合](reports/2026-11-02-natural-npc0139.md)完成22组／88次完整5719(None)并经[异作者独审](reports/2026-11-02-natural-npc0139-independent-review.md)：同一RNG下逐只交织8740位置采样与5719朝向／抖动，全部XYZ／169包／已知字节一致；50466个None字节不反填。首组保留实际constructorRNG，经独立LCG→PCG推得一致，其余21组为明确受控RNG／counter；原件侧22次合法v2恢复，不称本轮重新执行1600／6786／1108或自然App。

[顺劈斩922](reports/2026-11-02-cast0139.md)完成110组／184次完整原件调用，经[异作者独审](reports/2026-11-02-cast0139-independent-review.md)独立Fraction舍入与排序／RNG重算：1002672个单位字节、14720个owned字节与157条完整306包9858B完全一致，包中744个有序target IDs直接复核。当前优先计时器为380／分类424；旧372原型造成36处HP差异的失败批完整保留，不计入通过。phase0仍可选目标／耗暴击RNG／发施法包，只有913跳伤害；不能把整cast改为phase早退。此域限定普通目标、空proc与非致死，592／HP169仅观察，不代表owned调度／死亡／完整战斗。

[开局物件1886／符文13563→1446](reports/2026-11-02-opening-actor0139.md)36组／76次目标入口，经[异作者独审](reports/2026-11-02-opening-actor0139-independent-review.md)核对完整169包、坐标限幅118、朝向／四元数和记录56：7076已知字节一致，4572个None保留。真实2945／1600各36次只作setup；这是明确的借用平地查询输入，非真实地图／完整1108验收。49个新指针word仅观察，其余196796相对Game字节严格复算。

[同Game自然NPC→受控玩家动作→顺劈首击](reports/2026-11-02-npc-cast0139.md)8组／32次完整5719＋20次完整922，经[异作者独审](reports/2026-11-02-npc-cast0139-independent-review.md)全链重算：58824已知／31032 None、原件7740未知字节恒定、19条完整306、RNG／累计／owned80／集合及连续Game继承一致。独审直接读None-aware记录，作者A5／5A载体只是模型自检；显式移位／phase1与4个0.1伤害倍率用例不等于自然AI／输入或默认致死。原作者未在终态绑定stdout／runtime散列，独审仅绑定as-read字节，限制保留不回填。

[经验球／金币1446生产与45门槛合并](reports/2026-11-02-death-pickups0139.md)另有43次完整原件并经[异作者独审](reports/2026-11-02-death-pickups0139-independent-review.md)：40条完整169共5052B、3次merge、17996已知／8884 None及RNG／geometry一致；超过19的经验视觉scale为.9，旧43批5处差异与2次pilot均保留不加计。此域是XP／coin生成，不是完整死亡或经验拾取；runtime内容由comparison内联绑定，独立JSON的hash只有独审as-read记录。

[默认第二击死亡与经验／金币](reports/2026-11-02-death0139.md)14组／56次完整5719＋28次完整922已通过[异作者独审](reports/2026-11-02-death0139-independent-review.md)：18次死亡、18次XP、8次coin；35056已知NPC字节与13328 None、1820已知pickup字节与2436 None、RNG／f64累计及53条已知有序消息共4190B一致。真实G2056=0使913跳过994，36367是NPC名称解析而非删记录；四槽保留。完整592／HP169流、正回血和moving221未验收。

[完整默认开局1108](reports/2026-11-02-opening0139.md)16seed经[异作者独审](reports/2026-11-02-opening0139-independent-review.md)：新2945／1600Game→完整1108，四NPC／两符文／2或3时间窗／四special／69边界、RNG／counter85与1216条完整消息129792B一致。31984个vector已知字节、18704 None及每例556B已知Game；112新指针word只观察，其余41024相对Game字节严格守恒。原件仍借合法v2post1108初始化资源上下文，独立模型只使用raw构造world；新目标Game与旧Game分开。自然App／Rc／externref／设备输入未还原。

[首次成长／真实三卡／新技能选择](reports/2026-11-02-growth0139.md)24组fixture（21个不同输入）、24次4677＋18次1093经[异作者独审](reports/2026-11-02-growth0139-independent-review.md)：19次真实phase2三卡、57个候选、6720个owned字节、1518项属性、319项已知key及432已知／144 None的live32一致。fresh1600／真实locale83304各24次仅setup、无snapshot；本批为空world／首次new卡tier0..4，不含已有技能upgrade／gold／完整UI消息。

[死亡→经验球／金币拾取](reports/2026-11-02-collection0139.md)18组经[异作者独审](reports/2026-11-02-collection0139-independent-review.md)：72次5719＋36次922＋48次2890，7条正常死亡链与11个显式组件输入均保留4NPC；18条完整221、34条170共1081B、204项玩家字段一致。5552已知／2904 None保留，8456B从实际输入仅做已证明的标记写入与整56B移位后完全一致；82944B NPC与704B claims守恒。经验仍低于首次门槛5，非升级组合；marker2原版实际trap及旧decoder／预批保留，不计成功。

[完整开局→保留实际世界→首次升级选卡](reports/2026-11-02-growth-world0139.md)11组／32次目标入口经[异作者独审](reports/2026-11-02-growth-world0139-independent-review.md)：新2945／1600→完整1108→显式经验→11次4677／10次1093，10组真实三卡并回phase1。四NPC、两Rune、时间窗、特殊点和69边界均保留；26364／25613对本域静止或死亡NPC／空aux／空claims无动作。836条完整opening包、101376B全部背景守恒、63920已知／37456 None与240已知／80 None的live32一致。两个dead_mask只是显式位掩码控制，实际NPC marker为1；显式XP不等于真实死亡拾取已接升级。

[同Game完整开局→真实死亡经验→首次选卡→续击](reports/2026-11-02-opening-collection0139.md)3seed／47次目标入口通过[异作者独审](reports/2026-11-02-opening-collection0139-independent-review.md)：3×1108、21×922、20×2890、3×1093；2945／1600各3次仅setup。由实际掉落累计5XP升level2、真实三卡、选首new回phase1，seed42保留实际两个owned与live12再攻击活NPC；未直接给经验。全部开局物件保留，228条完整opening包24336B，后继60条已知有序消息3117B；10668个NPC与884个拾取未知字节严格继承，另4480B整56B移位完全一致。旧续击runner缓存旧Vec地址导致9差异，失败批保留；最终重新读取Game1660，并核actualowned2／exec!=11／7项emptyhit来源。

本组合的独立模型读取先前独立生产的canonical world，不在本批重做raw451资源生产；原件借合法v2post1108资源上下文，再新建Game。初始accounting／kill／gold／sequence为显式检查输入；玩家移位、直接调用与时钟是受控调度。该首级逻辑闭环不等于自然输入／AI／owned1238或主884整帧，不等于新技能自动施放或完整消息流。

已冻结作者报告保留执行时的pending状态，最终独审与版本注册说明实际接受范围。当前139有14809组限定fixture／18788次目标入口（18787正常返回／1预期越界），只是实验清单，不是完整覆盖率。setup／pilot／拒绝批／静态study不相加；空来源hit-events单独仍是静态与模型自检。已有cleave升级19组作者批待独审；正在恢复真实Human perception种族技能、1238自动调度、2123与live12到期，不能禁用racial来推进时钟。主循环884／Windows原生／完整一局仍为0。

固定138的[属性计算10569组](reports/2026-11-02-stats0138.md)、[非致死伤害80组／125调用](reports/2026-11-02-combat0138-independent-review.md)、[默认构造162次](reports/2026-11-02-initial-state0138.md)及其独审保留各自窄域；[13入口迁移守卫](reports/2026-11-02-flow0138-migration.md)仍是静态证据。它们均不等于138／139连续流程或Windows原生验收。

本轮固定135的[移动→战斗→真实符文拾取](reports/2026-11-02-opening-moving-rune0135.md)完成新460帧／4选卡／44次完整968输入／6488阶段／6490原件入口，0声明差异，[独审通过](reports/2026-11-02-opening-moving-rune0135-independent-review.md)。第444帧（raw索引443）消费实际刷出的kind5符文，停止移动后继续16帧；恢复请求133，但当时满血266，故只证明cap、移除与通知链，不称非零回血增量。117源／100production、snapshot／独立预解析world／部分类型App和外部clock边界明确。

[移动2328的38组／完整968本地输入33组](reports/2026-11-02-player-motion0135.md)和[校正确认199的88组](reports/2026-11-02-player-correction0135.md)均各自独审通过。真实键盘／摇杆生产、自然App／完整880、远端同步仍未接通；ACK组件尚未作为连续流程动作接线。135结果不转记138，Windows原生执行与独立完整一局均为0。

固定135新增[同状态战斗至失败结算](reports/2026-11-02-opening-fatal0135.md)：921帧／7选卡／44次控制运动／12945阶段／12947原件入口，声明字段0差异，[独立只读复核通过](reports/2026-11-02-opening-fatal0135-independent-review.md)。history48容器、已知字节与实际字符串、事件维护的七项统计、非平地停止、defeat JSON与致死后的五阶段尾续接入同一状态；1条普通27457移动221和10条45845停止221按实际wire grammar区分，原始包全保留。原件快照、预解析world、部分类型App与外部clock等边界不变，**仍不称完整游戏或139验收**。

[raw451→独立世界→同状态死亡](reports/2026-11-02-raw-fatal0135.md)另已完成：451份原始资源／67,281,330B，独立模型921帧／7选卡／44次控制运动，115项阶段与已列终态owner组合一致，[只读独审通过](reports/2026-11-02-raw-fatal0135-independent-review.md)。共113份core字节不变，12946份逐阶段摘要与known／None字节均核；这是两模型路径的组合，**新增原件case0**。模型不使用预解析world，按冻结源码／provider与路径hash证明读取边界；作者没有可追溯的OS级读取审计收据，独审记录自己的read guard。真实App／完整880／Windows原生与完整一局仍未验收。

历史[静止玩家750帧](reports/2026-11-02-opening-player-sources0135.md)、[raw451→750模型入口](reports/2026-11-02-raw-physical7500135.md)、[raw451→移动460模型入口](reports/2026-11-02-raw-moving-rune0135.md)及其各自收据保留范围，不相加。来源163组、死亡40组、recap103组是先行组件验证，后继连续整合另用新收据。

与 [封装优化](../ports/README.md) 并行，研究原作实际发布的程序、资源与计算逻辑。现有安装包继续由 `android/`、`macos/` 构建，实验文件放在本区；当前没有恢复完整原作源码。

固定135新增[400帧／第四次选卡与Battle Shout组合](reports/2026-11-02-opening-battle-combat0135.md)：400受控帧／4select／5604stage／5606原件入口、0声明差异，98源／85 production；实际第379帧选择Battle Shout，随后完成6673施放、effect8与属性变化，最终level5／XP6／gold53。修复后fresh收据SHA `b5d9c546789401d738b43cc58cac1d7aeb117c94753ed4d63f60d923224520a7`，该限定投影已通过[400帧只读独审](reports/2026-11-02-opening-combat0135-400frame-independent-review.md)（receipt SHA `376b09cd9ce10da25396d815824432e48eb456dbb1aeaea9674db95d25aa6482`），核对24,443,084个已知叶；905包峰值及其未恢复的payload语义仍只观察。原件snapshot、独立预解析world与外部f32调度的范围保持明确，完整880／Windows执行／独立一局仍为0。

另有[raw451资源→world→opening→400帧](evidence/asset-combat400-owned-20261101T174254.757426Z/model400/receipt.json)纯modelselfcheck：67,281,330B、92源与资源前后不变，不读原件memory／WASM／预解析world，400帧／4select也达到level5／XP6／gold53；三项world SHA、四guardian实体／GUID／timer及None字节均核对。[35项终态衔接](evidence/asset-combat400-owned-20261101T174254.757426Z/projection-bridge.json)与差分组合一致；这层不新增原件case或完整880帧。

[Battle组件134组／171调用](reports/2026-11-02-battle-shout0135-independent-review.md)与[CAS codec两正例／26负例全拒绝](reports/2026-11-02-opening-combat0135-cas-codec-review.md)已分别通过各自范围独审。CAS保留6008条完整logical records（1,662,490,742B；unique blobs 83,331,346B），没有删阶段或字段；旧`171633.375141Z` decoder批与120／250 checkpoint保留，不与最终400计数相加。该400旧批当时的下一纯模型帧401为`pending_due_event:G2444`资源40秒到期；[资源组件64组](reports/2026-11-02-resource-spawn0135.md)单独差分0差异，未接入这批旧400；后继500使用独立新收据，不能倒填旧批。

固定135的[250帧守卫出生组合](reports/2026-11-02-opening-guardian-combat0135.md)完成250受控帧／3select／3503stage／3505原件调用、0差异，94源/84 production；跨20秒4守卫出生并继续50帧，U68地址保持None、timer所有者按GUID严格核payload。该限定投影已通过[最终只读独审](reports/2026-11-02-opening-combat0135-250frame-independent-review.md)（receipt SHA `556693d5bac9b86545dd89a57b042bdb54823e49d4f845b5547a3a978d7158c7`），仍是预解析world、原件snapshot及外部clock域；旧120收据保持原身份，不相加。

另有[raw451资产→world→opening→250帧](evidence/asset-combat250-owned-20261101T163850.979737Z/model250/receipt.json)的纯modelselfcheck：67,281,330B、91源前后不变，不读原memory/预解析world/WASM，250帧／3select至level4／XP3。复用同一world的[后继纯模型](evidence/asset-combat250-owned-20261101T163850.979737Z/continuation/receipt.json)继续至379帧／4select，第380帧因实际选到battle_shout停止；没有重抽卡。379是该旧模型的边界，当时原件差分到250；后继400验收另列，旧收据计数不改，完整880/native/一局仍为0。

最终目标是拆清全部逻辑与数据，形成能够独立重造的核心。功能目标持续跟随官方最新稳定版；每轮检查后固定版本/SHA。**此前固定参照0.137.0 / `d171b8f9f`已完成[完整静态profile](reports/2026-11-02-wasm0137-profile.md)与[非致死伤害80组/125调用0差异](reports/2026-11-02-combat0137.md)，局部动态[限定数值域独审通过](reports/2026-11-02-combat0137-independent-review.md)，完整游戏/native运行仍为0**；0.136.0 / `fe24fb74c`保留静态profile与候选映射，动态验收0；开局组合动态实验仍锁定0.135.1 / `90898d5e3`。旧`0898d5e3`为历史截短alias，收据不覆写，见[先前身份采集状态](reports/2026-11-01-latest-version-state.md)与[版本策略](VERSION_STRATEGY.md)。

此前metadata核对截至 **2026-11-01T16:51:40Z**，官方manifest仍为同一137 EXE SHA、HTML stamp仍为`c628fd68823e`；仅复查清单/页面，未重取大二进制，见[核对收据](evidence/official-latest137-closecheck-20261101T165135.413048Z/receipt.json)。

固定135的[历史14阶段独立切片](reports/2026-11-01-headless-tail0135.md)：8seed/1614帧/22607阶段/11选择/22615原件调用，67源含60core、16角色，0差异；其6未知技能/2预算边界、显式phase1与初始zero槽保留为旧批范围。后继真实开局/战斗/升级/选卡另出135收据，不能倒填旧批，也不转记136/137通过。旧072329/11309、064308/9695、061901/5473及0.134.0/0.126.0结果各自保留，不相加；详见[覆盖清单](RECONSTRUCTION.md)。

新[opening→combat→XP/首次选卡组合](reports/2026-11-01-opening-combat0135.md)固定135 human warrior／seed0／navigation False：120受控帧、1select、1681stage、1683原件入口0差异，90源/80 production。真实1089的phase1、4NPC/2kind2/4special/2window/69boundary/0companion及实际capacity保留，未知字节None不补零；level2选择实际index0 thunder_clap后续33帧。独立预解析world、原件snapshot与外部clock调度明确分开；不是完整880/native/一局，旧headless、frame及death-pickup回归不与新case相加。 该限定投影已通过[只读独审](reports/2026-11-02-opening-combat0135-independent-review.md)，receipt SHA `2b768595711ff9f5daea0fcd718c4e963b8d2d02b652823285444000e2e96d2d`；原packet payload语义仍只观察。

另一个[raw451资产独立入口](reports/2026-11-01-opening-combat0135.md)实际读取67,281,330B／9tiles，87源不变且无closure逃逸；不读原memory、预解析world或WASM，从world/opening走完120帧／1select至level2／XP6／gold7，三个world SHA与既有query产物一致。它是独立生产层的补充证据，不新增原件case或完整880帧。

新增[独立默认开局](reports/2026-11-01-opening0135.md)完成16组／32次完整6730缓存命中构造与1089、0差异，[独审通过](reports/2026-11-01-opening0135-independent-review.md)；以已解析真实world输入接通附属对象、4NPC、2kind2、事件窗口与69个边界对象。它与旧14阶段切片尚未整合。M2／WMO碰撞、候选／导航producer及world查询消费者分别验收；后继资产查询world组合不改变这些原批身份。

后继[独立资产组合](reports/2026-11-01-asset-world0135.md)从451文件/67,281,330B重建默认Elwynn查询world并继续开局，37源冻结；terrain4,022,968B、nav78,400B、secondary1,254,400B、78包/8,410B及RNG/phase1/counter87与**1历史原件case**一致，[整体独审通过](reports/2026-11-01-asset-world0135-independent-review.md)。生产不读原memory；历史checker另读原snapshot，0新增原件调用/案例或主切片帧。物理App/Once/Rc/VFS、其它地图模式与完整一局仍缺。

另有[自然原App/Metal观察](reports/2026-11-01-full-app0135-probe.md)（[观察独审通过](reports/2026-11-01-full-app0135-independent-review.md)）：官方构造产生真实App，已显示正常中文角色选择页，8次idle880完整返回；999次HTTP全部200、0 page error，Game tag2仍在菜单、未进入一局。CSP阻止presence外发，保留真实联网尝试；前期SwiftShader失败与首Metal的observer/font边界不倒改。它是原程序观察，新增独立gameplay帧0，不代表独立App/880已经实现。

本轮[真实菜单→运行态Game观察](reports/2026-11-01-game-entry0135-probe.md)已通过实际点击/W输入，603次完整880返回，其中8次running、7次clock推进；2418素材全部成功、0page error，全量1,378,877,440B coherent memory已核SHA，[独审通过](reports/2026-11-01-game-entry0135-independent-review.md)。这是原件观察，新增独立case/主切片帧0。真实默认Warrior的cleave execution5、输入/所有权/真实容量交接和完整独立一局仍缺，不能把原版进场等同独立实现。

此前0.126.0已恢复主循环主干、9职业/113能力定义、选卡/施法/伤害、12区域及账号存档主干，并建立若干独立模型。它们保留为历史验证和新版迁移参考，不能直接计为0.134.0已支持；[核心还原图](CORE_MAP.md)明确区分两者。

HP对象更新经主机发送、客人解码、事件通道和注册系统到客户端字段写入已静态追通，见[事件投递](reports/2026-11-01-ecs-delivery.md)、[伤害计算](reports/2026-11-01-damage-core.md)和[合作同步](reports/2026-11-01-coop-sync.md)。该静态路径和离线codec尚未经过真实跨端联机验收。

用户提供的 [bbylw/rea-cn](https://github.com/bbylw/rea-cn) 是中文文档站，真实工具是 [morluto/rea](https://github.com/morluto/rea) 的 npm 包 `rea-agents`。这里固定 **REA 6.8.0 + Node 22.23.4**，使用 CLI 和项目内的持久 MCP 会话，不要求注册全局 MCP 或重启客户端。工具、运行时及分析器安装不会进入游戏 APK。

## 已实际运行

### latest与固定研究分工

- 固定0.138.0：[完整profile](reports/2026-11-02-wasm0138-profile.md)和[限定非致死伤害80组/125完整调用及独审](reports/2026-11-02-combat0138-independent-review.md)已完成，完整流程／native／一局未验收；不转记135/137结果。
- 固定先前固定0.137.0：[175327函数完整profile/RO索引](reports/2026-11-02-wasm0137-profile.md)与[新独立非致死伤害913：80组/125完整调用0差异](reports/2026-11-02-combat0137.md)已完成，11源/0host；[限定数值域独审通过](reports/2026-11-02-combat0137-independent-review.md)。Unit432字段按137重映射，完整death/proc/Windows ABI及运行/fullgame仍缺，135/136次数不转记。
- 固定0.136.0：[全量WAT/RO SQLite与12入口候选](reports/2026-11-01-wasm0136-profile.md)已完成；静态同形及地址/table slot迁移不等于运行通过。
- 固定0.135.1：既有和进行中的独立资源→opening→combat→XP/选卡实验继续锁定原SHA；52-role与各私有builder仍按各自版本准入。

### 固定0.135.1动态研究与基础资源

- 固定0.135.1：[完整WASM profile](reports/2026-11-01-wasm0135-profile.md)覆盖175317个defined函数、824549条直接调用；全量函数header/body范围和28471个data payload哈希读回通过。这是静态导航基础，不等于所有逻辑已恢复。
- 固定0.135.1：[初批映射](reports/2026-11-01-migration0135.md)保留，当前52角色各自body/签名guard；[52角色保守性证明](evidence/builder135-role52-review-20261101T083845.125766Z/review.json)重建旧9-role模块字节一致，0新增运行case。主Node878导入全拒绝/总32MiB；单块allocate从1升至4MiB用于完整ADT，总上限未变。
- 固定0.135.1：[完整原1512属性差分](reports/2026-11-01-stats0135-spec.md)10569例、0字段差异；比较23派生词、HP、4辅助字段、3对象键、速度和队列数量，新增G1572护甲上限已恢复。独立只读复核通过；真实producer、已有树项更新、包字节和自然组合仍待接入。
- 固定0.135.1：[暂停命令与tick时钟投影](reports/2026-11-01-game-loop0135.md)在完整原1371/880中重做6558例（5400命令＋1158tick），0差异。比较暂停phase及上次时间/模拟时钟字段；tick其余phase和完整调度未独立比较。状态为空队列/无单位并走原skip-spawn守卫，fresh终局保存、完整刷怪与多人终态仍pending。
- 固定0.135.1：[114能力/9职业重新提取](reports/2026-11-01-catalogue0135.md)确认kit不变，但rockbiter与stormstrike的伤害/冷却/范围有实际平衡变化；新版并非只改UI。所有新pointer均由本版指令和data重建。
- 固定0.135.1：[kind0候选4126例](reports/2026-11-01-candidates0135-spec.md)、[新能力初始化2781例](reports/2026-11-01-new-ability0135-spec.md)、[有序升级3629例](reports/2026-11-01-selection0135-spec.md)均重新执行完整原2159/1072，0声明字段差异。前者只验metadata/RNG/控制，后两者覆盖完整80B记录与限定控制；kind1/2、真实producer和完整UI/世界副作用仍pending。
- 固定0.135.1：[XP逐级成长组合1151序列/3450调用](reports/2026-11-01-level-cycle0135.md)完成每级属性→治疗→阈值→候选；[选卡收尾660序列/1090调用](reports/2026-11-01-selection-cycle0135.md)接通new/upgrade/gold→属性→XP扫取→kind0再生或phase1，均0声明字段差异。七组来源快照必须显式；选卡未建模的keyed state完整另存，不能视为全是显示字段，完整1072状态等价未宣称。
- 固定0.135.1：[选怪/衰减/普通与精英生成4021例](reports/2026-11-01-spawn0135-spec.md)与三个真实原入口0差异，覆盖12地图/148定义及424B记录和RNG；实际成功生成1211例。位置/owner是明确已解析输入，完整947位置调度另列，Boss/特殊调度、真实terrain仍未完成。
- 固定0.135.1：[完整947普通帧→8751位置→5736单位](reports/2026-11-01-spawn-frame0135.md)1580例（1275帧＋305位置）0差异，实际自然创建9360份单位记录；这是组合内记录数，不算额外9360用例。限定flat terrain、静止/四轴heading、owner0，其他event/Boss deadlines未来；此前8个非轴heading已由[任意运动扩展5068例](reports/2026-11-01-spawn-motion0135.md)补齐；grid/pathfinding/fallback仍未验收，5068包含旧1580重放。
- 固定0.135.1：[额外84B计时施法/直接施法/延迟命中1314序列、3626调用](reports/2026-11-01-cast0135-spec.md)0未声明差异。实际25个effect-tag0、execution-kind0/2定义，比较目标、HP、RNG、待命中与冷却；空proc且无致死语料，其余执行/效果、死亡loot与完整技能行为仍pending。
- 固定0.135.1：[已学80B主自动施法639组/5924阶段](reports/2026-11-01-owned-cast0135.md)0差异，包含职业近战、25定义、逐hit自疗与延迟命中；与916额外84B系统分开。旧basic80是G1256槽中的effect0隔离fixture，不是1560真实racial；真实racial由下列独立批和headless另验。[可选接口默认回归](reports/2026-11-01-default-extension0135-regression.md)原样重放639组及5068组生成，不计新增覆盖。
- 固定0.135.1：[Boss871例](reports/2026-11-01-spawn-boss0135.md)、[精英549例](reports/2026-11-01-spawn-elite0135.md)各自完整原件调度域通过，实际751次Boss/340次精英生成；真实terrain、其它event/2376、完整AI与全调度仍待恢复。
- 固定0.135.1：[普通死亡/混合拾取204组871阶段](reports/2026-11-01-death-pickup0135.md)0声明差异，376次死亡、136组进入候选。旧12组非空definitions失败证据保留，[新855组/1004阶段](reports/2026-11-01-proc-events0135.md)在kind27/zero16B gate、显式非致死context0域解释并重验通过；致死post-proc和其它gate仍未知。
- 固定0.135.1：[有效护甲/受伤2107例](reports/2026-11-01-incoming0135.md)、[普通近战AI416组1013步](reports/2026-11-01-ai0135.md)在限定域0差异，后者覆盖124定义与完整424B记录；远程/Boss AI、反击producer、真实地形、死亡复活仍缺。
- 固定0.135.1：[真实空profile构造151组](reports/2026-11-01-initial0135-independent-review.md)来自最终055136收据，恢复class starter/真实G1256 racial、属性/HP/RNG、预算/timer和phase0；上游profile/App熵与独立资源进入未恢复；后继真实账号/world/1089原件观察另列。[死亡placement924](reports/2026-11-01-ordinary-placement0135.md)覆盖12地图和pre-hit移动插值；[六种racial720](reports/2026-11-01-racial-cast0135.md)验完整922的live32/属性/HP/盾和三份attempt ledger。
- 固定0.135.1：[trig6726/长期AI429组3423步](reports/2026-11-01-ai-motion0135.md)补中角归约和跨2π轨迹；三条800帧轨迹无接触攻击，极大角1814、远程/Boss/真实地形仍缺。[玩家更新/尸体285组444阶段](reports/2026-11-01-player-update0135.md)、[移动暂停396组1136阶段/604条221消息](reports/2026-11-01-movement-pause0135.md)通过，见[两辅助批独审](reports/2026-11-01-gameplay-phase0135-independent-review.md)；暂停/恢复会逐移动NPC推进序号。
- 固定0.135.1：[headless061901](reports/2026-11-01-headless0135.md)有8次自然选择；seed3选卡后继续145个原件对照帧至250，另7个在未支持技能前停。63源含56份core/init，完整128槽无损delta独立复原，24次旧槽复用保留192非零未写字节。只有7个numeric keys已比，其它keyed state全部另存；该旧批phase1与初始zeroed128槽为显式研究输入，当时1089被SELF/data阻断；后继真实开局观察另列，不倒记为旧模型支持。
- 固定0.135.1：[持续AoE693/5495组件](reports/2026-11-01-area-effects0135-independent-review.md)保留；当前[14阶段独立切片](reports/2026-11-01-headless-tail0135.md)：8seed/1614帧/22607阶段/11选择/22615原件调用，67源含60core、16角色，0差异。完整128槽无损delta/字节/SHA与7个numeric keys对照；额外inactive payload/指针只观察，不预测零。旧阶段按各自快照保留。
- 915：[500组/2121非空delayed56组件](reports/2026-11-01-effect-system0135.md)仍分383正常/117预期255 pop后trap；主切片接idle域。[Boss矩形390](reports/2026-11-01-effect-geometry0135.md)另分277正常/113SELF拒绝前缀；[真实浏览器DBC实验](reports/2026-11-01-browser-resources0135.md)已走通3组完整命中，但完整容器/proc尾部仍缺；history的后继独立组件与真实DBC组合另列，旧113个prefix分类不倒改。
- 新批分别经过[生成模块](reports/2026-11-01-spawn135-independent-review.md)、[死亡/受伤/AI](reports/2026-11-01-gameplay135-independent-review.md)及[主施法](reports/2026-11-01-owned-cast0135-independent-review.md)独立只读复核；未执行原件的复算不另计新增原件案例。旧批冻结列出的源码集合，新主施法补入包入口共33源，旧证据完整性不追溯扩大。
- 基础资源：[独立MPQ读取器与索引](reports/2026-11-01-resource-index-base.md)对29602个命名块/1636167198B与固定StormLib逐字节一致；154份DBC已按容器读出。基础RAR仍关联旧0.102.3，不自动作为新版完整资产；尚无M2/BLP渲染器或完整资源管线。

- [NPC/880静态清单](reports/2026-11-01-npc-effect-producer0135-static.md)保留148normal/60boss/290原始动作声明，计数不等于已验行为。14个真实尾阶段只在限定域接入；活跃916/975 execution11/2602/2573/2376、915其余类型、前段/party/完整880、其它地图及物理world所有权、开局与主切片整合、未知技能/AI/存档/UI/联机及完整独立一局仍未验收。
- [真实进场资源静态规格](reports/2026-11-01-entry-resources0135-static.md)核对39函数、116份已有资产/170383346B和12区首层路径；[独立静态复核](reports/2026-11-01-entry-resources0135-static-review.md)通过；该静态批未执行VFS/world/1089，不新增玩法用例，后继原件真实进入另列。
- [五阶段组件573/944](reports/2026-11-01-frame-systems0135.md)、[真实胜利终态416/832及416构造](reports/2026-11-01-terminal-transition0135.md)、[107完整ADT/18413调用](reports/2026-11-01-terrain0135.md)、[真实Boss矩形390](reports/2026-11-01-effect-geometry0135.md)分别验收，不与主切片相加。[真实浏览器资源链](reports/2026-11-01-browser-resources0135.md)另以原生SELF/XHR完成3组phase1命中/15已恢复投影；17资源绑定允许、861拒绝、128MiB，区别于纯Node878全拒绝/32MiB。来源容器/keyed/proc完整尾部仍缺；history后继组件单列。 [浏览器独审](reports/2026-11-01-browser-resources0135-independent-review.md)通过，未重跑原件。
- [受伤history组件](reports/2026-11-01-incoming-history0135.md)完成164组/924次完整1073、0声明字段差异，[独审通过](reports/2026-11-01-incoming-history0135-independent-review.md)；限无单位/sourceGUID0/spell0 fallback、空proc/非致死或minimum-one。后继[真实DBC history组合](reports/2026-11-01-browser-history0135.md)9fresh/37次1073同样0声明字段差异，冷加载、完整姓名/图标路径与环形搬移另验，[组合独审通过](reports/2026-11-01-browser-history0135-independent-review.md)。完整来源容器/keyed/proc仍未知，未接headless。
- [真实世界与开局观察](reports/2026-11-01-entry-world0135-probe.md)在1个显式空selected-profile下执行原2902→6959→6730→1089，真实非平地Rc同状态phase0→1、4NPC/2kind2；453MPQ/83,632,785B、561GET全部200，4整memory/319,029,248B，[独审通过](reports/2026-11-01-entry-world0135-probe-independent-review.md)。这是历史原件观察、独立模型case0；后继独立开局不倒记为该批覆盖。宿主24允许/854拒绝、256MiB，与history/资源browser17允许/861拒绝、128MiB分开保留。
- [world查询959组/1858调用](reports/2026-11-01-world-query0135.md)与[新位置96组/96调用、30源闭包](reports/2026-11-01-world-position0135.md)通过[联合独审](reports/2026-11-01-world-consumers0135-independent-review.md)：真实高度／secondary及受控nearest、8751／13516完整回退、原字节nav／距离图和RNG均按声明域验证。它们读取已解析snapshot，尚非world producer；旧21源位置批保留，不与新96例相加。
- [M2碰撞／变换／高度候选／导航生产114组/1477调用](reports/2026-11-01-world-raster0135.md)覆盖实际31份M2，[最终100905独审](reports/2026-11-01-world-raster0135-independent-review.md)通过；[WMO碰撞425组/830调用](reports/2026-11-01-wmo-geometry0135.md)覆盖实际readset的23root／387group共410文件，[独审通过](reports/2026-11-01-wmo-geometry0135-independent-review.md)。均为fresh实例、32MiB／878deny；碰撞解析不包含材质、动画或渲染。

- [ADT placement13组/13原件调用](reports/2026-11-01-world-placements0135.md)恢复9实际ADT/4受控域的两组44B记录；三阶段实例筛选另为静态规则。[最终cache生产](reports/2026-11-01-world-cache0135.md)恢复ground、墙格后四邻可达性与严格secondary maxmerge，[静态独审通过](reports/2026-11-01-world-cache0135-independent-review.md)；451资源历史组合由[整体独审](reports/2026-11-01-asset-world0135-independent-review.md)另验，不能把静态/本地14契约计为新原件case。
- [1744／1821组件27组/116调用](reports/2026-11-01-opening-entities0135-independent-review.md)独审通过；后继[完整默认开局16组/32入口](reports/2026-11-01-opening0135.md)冻结39源，六vector、1248包／16条start逐字相符，[独审通过](reports/2026-11-01-opening0135-independent-review.md)。每局2附属、4NPC、2kind2、4special、2或3窗口、69边界，counter10→87；已解析world仍是输入边界，未接旧主切片。
- snapshot查询／位置／开局仍使用独立256MiB／878deny与栈1048576；M2／WMO fresh域32MiB／878deny。共享52role和各实验准入保持，所有计数不相加。本轮451资源纯模型CLI是另一条无原件执行的生产链；物理App/Rc/VFS所有权、菜单/profile、其它地图模式、非空装备天赋、旧切片整合和独立一局仍未知。
- 真实14尾阶段[080624观测](evidence/full0135-oracle-20261101T080624.993012Z/main-tail135-probe-receipt.json)为3038帧/42550快照/18选择/42558调用，6预算、seed3第353帧与seed5第285帧进入phase4；这是原件观测，不是独立模型验收，不与当前1614帧相加。 [观测独审](reports/2026-11-01-main-tail0135-probe-independent-review.md)通过；2521个execution11快照不计新模型能力。

- [76B transport六方法](reports/2026-11-01-transport0135.md)在43组/220次完整原件调用中0差异，[独审通过](reports/2026-11-01-transport0135-independent-review.md)。quiet flags/timer域、fresh32MiB/878deny、实际宿主0；flag日志/时钟、完整owner生命周期、receive→ECS及真实网络未验。
- [空history/真实地址熵](reports/2026-11-01-app-history0135.md)24组/96入口、[独审通过](reports/2026-11-01-app-history0135-independent-review.md)：20个空12B头完整生成/析构，entropy仅已知408B投影，另384B地址词opaque；四map128B是typed-state静态规则，不是完整4253差分。
- [App5168部分构造](reports/2026-11-01-app-state0135.md)32组静态重组/10源闭包，[独审通过](reports/2026-11-01-app-state0135-independent-review.md)，0新WASM调用；默认730已知/4438None，显式三块live-copy后1182/3986。[既有真实cast投影](reports/2026-11-01-app-state0135-capture.md)另以33B输入独立预测697B，全部730已知相同、[独审通过](reports/2026-11-01-app-state0135-capture-independent-review.md)，未把第一次观察的8idle返回或GPU panic算成投影验收。
- [完整880上下文静态记录](evidence/full880-context0135-static-20261101T111231.254023Z/notes.md)保留历史前置依据；后继自然原App、8idle及真实菜单→8running880观察分开保存；独立合法App/完整880生产与完整一局仍未恢复。

### 固定0.134.0的局部结果

- 固定研究基线0.134.0：Windows更新EXE已按官方大小/SHA验收；Web同版快照已取得。原生PE身份、五表及两函数已重新定位，257条LLVM/Ghidra指令字节独立一致，未执行EXE。用户原有4T资源RAR已通过[完整CRC与提取文件哈希验收](reports/2026-11-01-resource-acquisition.md)，8文件含7个MPQ已可用，独立索引/读取器另验，实际游戏加载和渲染仍pending。包内EXE仍旧0.102.3，更新程序另取官方清单。
- 固定0.134.0的[完整WASM profile](reports/2026-11-01-wasm0134-profile.md)已完成验证、完整WAT和独立SQLite索引，覆盖175316个defined函数与824546条直接调用。它提供新版定位入口，不等于恢复全部游戏逻辑。
- 新版[114能力/9职业目录](reports/2026-11-01-catalogue0134.md)已从原件初始内存提取，并与旧版逐字段核对；新增stormstrike/rockbiter、移除call_of_flame，stoneform参数变化。定义计数不代表全部效果已实现。
- 新版独立实现对照：[升级原25368](reports/2026-11-01-upgrade0134-spec.md)11560例、[完整选卡原1073](reports/2026-11-01-selection0134-spec.md)779例、[完整扣血原914](reports/2026-11-01-combat0134-spec.md)454例均0差异。后两者保留完整原件内部callee、仅增加研究导出；所有878宿主导入拒绝且实际调用0次，未启动完整游戏。选卡比较80B+5标量，扣血比较HP/有效统计/死亡主字段；完整后处理、触发与掉落仍未实现。
- 新版[选卡→拥有记录→施法→扣血](reports/2026-11-01-selection0134-chain.md)已重新定位；[实际伤害链](reports/2026-11-01-combat0134-chain.md)确认单位改为424B，并新增按技能ID和目标状态累加的36B记录。新`combat134`独立实现该加区，旧`combat.py`仍只作历史参考。各模型的版本范围见[支持清单](reconstruction/version-support.json)。
- 新版[拾取XP→等级→候选入口](reports/2026-11-01-progression0134-chain.md)已定位，新版自然上限为120级；独立`progression134`与[完整新4630的2197例对照](reports/2026-11-01-progression0134-spec.md)0差异。phase3只由原末尾守卫跳过2159，属性/消息/治疗原callee仍执行；只验4字段，不称完整成长/候选生成已实现。
- 新版[玩家受伤/护盾规则](reports/2026-11-01-incoming0134-chain.md)保留完整1063、IceBarrier相关922及CFG依据；[139例完整原1063非致死字段对照](reports/2026-11-01-incoming0134-spec.md)0差异。独立`incoming134`仍是显式pending的标量前缀，限定空辅助状态/不耗尽总盾；不代表复活、死亡或完整IceBarrier已实现。
- 新版[死亡→经验合并→延时拾取](reports/2026-11-01-death-xp0134-chain.md)补齐静态主干；独立`pickups134`与[完整1417/2862的345例对照](reports/2026-11-01-pickups0134-spec.md)0差异，覆盖45闲置上限、原始56B记录、到达时间和倒序派发。另一次原件914→2862→4630组合观测增加XP2；它不属于独立差分或完整游戏验收。
- 后续[普通死亡组合验证](reports/2026-11-01-ordinary-pipeline0134.md)已把伤害、经验/金币请求、kind1额外RNG、混合拾取和XP规格接起来：最新拾取382例、组合367例×4阶段快照，0差异。模型逐笔停止于选卡/未恢复属性边界；4个组合终态保留stats_dirty。基线345与新382是不同版本回归，不能相加称新覆盖。
- 新版[完整1513属性数值投影](reports/2026-11-01-stats0134-spec.md)完成10569例、0差异；确认race1 XP、调整上限和辅助池clamp的新变化。22输出、HP/辅助池/对象字段及移动决策已对照，真实producer仍缺；每级属性/治疗/候选已在下面独立XP消费者组合验收，尚未接入普通死亡/混合拾取控制器。
- 新版[kind0候选metadata](reports/2026-11-01-candidates0134-spec.md)与完整原2159的4126例对照0差异，比较候选ID/tier/kinds/权重筛选结果、四字RNG及3个控制字段；103个职业kit新能力ID和114个owned升级ID实际出现。kind1/2、展示payload、世界/通知、实际reroll及拾取→候选自然调度仍未完成，XP消费者组合另列。
- 新版[金币收取](reports/2026-11-01-currency0134-spec.md)与完整原2862的1030例对照0差异，另含578次warmup，共1608次原入口调用；局内金币/累计、key1176、队列、记录移除和despawn已对照。账号转移/持久化、网络交付及自然死亡→混合拾取完整调度仍pending。
- 新版[新能力初始化](reports/2026-11-01-new-ability0134-spec.md)与完整原1073的2781例对照0差异，覆盖114定义×tier0..4、额外tier5 helper表项及显式modifier快照；未知modifier producer明确拒绝。80B记录和限定入口/收尾控制投影已验，共享后处理、统计刷新及完整选择流程尚未接入。
- 固定0.134.0的[XP→每级属性/治疗→候选组合](reports/2026-11-01-level-cycle0134.md)完成1151个状态序列、3450次完整原4630入口调用，0字段差异；来源快照强制显式，cause0和治疗半减守卫均保留。它尚未接入拾取/金币/选卡应用控制器，也不算0.135.1验收。

### 历史0.126.0与工具记录

- 以下0.126.0结果是历史已验证参考；正按新版profile逐项迁移，不继续把旧版当主目标扩展。
- 原版网页核心 **0.126.0 / 3e72472a**：REA 已静态解析七个原版 JS 文件并保留完整 Evidence 和摘要。动态导入、WASM 内部行为与部分语义仍未知，不能把关系图称为完整源码。
- 首轮完整WASM解码：官方WABT验证并解码得到约1.3GB WAT；最初保留八个完整函数，关联原件范围和哈希，并使用REA Evidence库校验记录，定位 `presence` 发送实现。原版REA大小限制保持不变，历史快照见[WASM报告](reports/2026-11-01-wasm-deep.md)，后续函数与逻辑见核心还原图。
- 升级数值起点：找到五组分档系数、按状态计算的函数25242和调用者1065的字段写入，详见[升级数值报告](reports/2026-11-01-upgrade-values.md)；后续已独立追到实际伤害消费者。
- 后续伤害追踪：934中能力倍率进入命中基数和暴击，再调用933实际扣敌人HP、累计有效伤害并触发死亡状态；1107处理玩家减伤、盾和生命。随后已确认1065更新实际拥有的技能记录，由22136读取并送入施法，见[能力报告](reports/2026-11-01-abilities.md)。
- 主循环及世界规则：[阶段/计时/暂停](reports/2026-11-01-game-loop.md)、[地图/敌人/刷怪/经验](reports/2026-11-01-world-progression.md)、[账号存档与RSE1](reports/2026-11-01-save-schema.md)已形成可读静态规格，保留完整函数和未覆盖项。
- 独立可执行规格：[升级值](reports/2026-11-01-executable-spec.md)11560组、[两条生命成长曲线](reports/2026-11-01-world-progression.md)24636组、[半径helper及外层组合](reports/2026-11-01-radius-spec.md)29041组对照均0差异。这里执行了隔离原件数值函数；半径外层为重组，没有执行原934。完整游戏未启动，有限样本不代表全部输入或对局通过。
- 后续独立规格：[四字RNG/区间拒绝重抽](reports/2026-11-01-rng.md)18144组返回/状态一致；[经验舍入helper及XP投影](reports/2026-11-01-progression.md)30125组对照0差异，其中5482组为重组，未执行原3231。
- 技能和属性继续细分：[113能力的12kind/14tag与Fireball延迟命中链](reports/2026-11-01-cast-dispatch.md)、[9职业/8种族和真实属性重算](reports/2026-11-01-derived-stats.md)均保留具体入口/原始分派；未形成完整施法或属性替代实现。
- 历史可执行模型继续保留：[属性重算](reports/2026-11-01-stats-spec.md)完成原1573及原内部callee8495例；[选卡应用](reports/2026-11-01-card-apply.md)包括2345卡+1初始化片段及5例完整原1065；[战斗投影](reports/2026-11-01-combat-spec.md)包括9153片段及32例完整原933。完整模块研究副本只增导出、拒绝所有宿主调用，没有调用应用start；这些实验均属0.126.0。
- 后续联机追踪：已区分WebSocket、中继、按peer确认层和应用层，找到主机/客人工厂及HP结果的实际封包/接收通路。纯离线工具覆盖8/11种中继标签、19/25种应用标签，以及opcode169值更新子集；未实现变体明确拒绝。
- 内嵌 Lua：逐字节提取 API 源模板和角色面板，共50个命名函数、22种消息前缀；仅作语法编译，未执行目标。它们是辅助提取结果，详见 [Lua 报告](reports/2026-11-01-embedded-lua.md)。
- 原生 Windows 参考 **0.102.3 / f78e6fab**：REA 已读取 PE 导入表并检查 Rust 元数据；未发现 `.dep-v0` 依赖表，只读到编译器路径线索。它与当前封装核心版本不同，不能直接套用偏移或规则。
- Ghidra 12.1.4/JDK21 已接入，REA doctor九项通过；上次原生全量分析会话因用户重启电脑中断，尚不能宣称完成。遗留响应含 `provider_timeout`，配置期限为1800秒；这不能证明分析连续运行了30分钟或必然会超时。详见 [提供方安装记录](reports/2026-11-01-native-setup.md)。
- 旧原生定向分析：另用项目内Ghidra辅助脚本得到五个候选函数输出，其中两个完整解码函数支持系数与字段写入结论；一个存在错误控制流，已排除。此路线不冒称原版REA完整分析，详见 [原生函数报告](reports/2026-11-01-native-focused.md)。
- 历史起点见 [首轮分析报告](reports/2026-11-01-initial-rea.md)；后续工作见 [研究问题](QUESTIONS.md)。

## 使用

在仓库根目录运行，需要已有 npm 和 Python 3.11+：

这些脚本已在本机 macOS 验证；其他分析主机尚未验收。

```sh
# 只安装到本研究区 .toolchain/；不注册客户端、不替换系统 Node。
python3 reverse-engineering/scripts/rea.py bootstrap
python3 reverse-engineering/scripts/rea.py --version

# 需要原有已验证官方快照；先校验原始 WASM 和每个 JS 哈希。
python3 reverse-engineering/scripts/analyze_web.py

# 显式指定已建档的旧原生参考；也可填本机 local.sources.json。
python3 reverse-engineering/scripts/analyze_native.py --exe /path/to/original/AzerothSurvivors.exe

# 本地辅助工具：完整当前 WASM 解码、指定函数 Evidence 与内嵌 Lua 提取。
python3 reverse-engineering/scripts/wasm_setup.py
python3 reverse-engineering/scripts/wasm_focus.py
python3 reverse-engineering/scripts/extract_embedded_lua.py

# 可选原生分析提供方；固定 macOS ARM64 工具，只安装到 .toolchain/。
python3 reverse-engineering/scripts/setup_native.py
python3 reverse-engineering/scripts/decompile_native_focus.py --exe /path/to/original/AzerothSurvivors.exe --timeout 180
```

`analyze_web.py` 将七个逐字节相同的原文件复制到新建证据目录，声明选取范围后交给 REA；不会递归分析工具目录、大型游戏数据或用户存档。每次运行生成独立 `evidence/<UTC时间>-web/`，包含原文件哈希、完整 `application.json` 和 `summary.json`，后续查询复用完整 Evidence。原生脚本同样只读，并校验独立版本的大小与 SHA-256。

更多命令可通过 `python3 reverse-engineering/scripts/rea.py --help` 查看。`rea_native_session.py` 通过标准输入 JSON Lines 驱动一份 REA MCP 进程，保留每次请求与响应；它也不会向 Codex 注册全局 MCP。原生工具诊断通过不保证大型目标的完整自动分析会完成。

## 当前工具边界

| 目标 | 状态与下一步 |
|---|---|
| 原版 JS 启动层、资源路径、存档／插件桥 | 已跑通 REA 静态分析；动态值须进一步追踪或运行观测。 |
| 固定0.137.0 / 90,941,108B WASM | 完整175327函数profile/RO索引及非致死damage913的80组/125完整调用0差异，实际build `d171b8f9f`；[限定数值域独审通过](reports/2026-11-02-combat0137-independent-review.md)，完整death/proc/native运行/fullgame未验收，旧版结果不转入。 |
| 固定0.136.0 / 90,927,420B WASM | 完整静态profile与12入口候选、实际build `fe24fb74c`已核；动态验收0。 |
| 固定动态研究0.135.1 / 90,959,080B WASM | 082927历史14尾8/1614/22607/11/22615等收据各自保留，后继真实开局/战斗/升级/选卡组合另记。451资源查询world、组件与原件观察分别验收；完整物理world/App/880和独立一局未通过。 |
| 固定0.134.0 / 90,953,762B WASM | 完整验证/解码/独立索引，多个规则投影已做限定域原件差分；完整游戏未实现。REA原版大小限制未修改，本地扩展单列。 |
| 历史0.126.0 / 90,116,970B WASM | 保留完整WAT和已验证局部模型作迁移/回归参考；WAT不是原始Rust源码。 |
| 原生 Windows EXE 的导入表／Rust 元数据 | 已运行无目标执行的 REA 检查；元数据不是函数实现或源码。 |
| 原生函数、伪代码、调用关系 | 两个完整解码函数支持旧版系数与字段写入结论；其余三个候选不能等同为可靠行为还原。完整REA分析尚未完成。 |
| 真实战斗数值 | 已追到一条完整命中与敌人HP/死亡，以及玩家受伤主干；反伤、全部技能和逐帧一致性尚未恢复。 |
| 独立重建 | 历史0.126.0已有升级、成长、半径、RNG、经验、属性、选卡与战斗投影模型；现按0.135.1逐项迁移，0.134.0局部组合与结果分开保留；尚不能独立完成一局。 |
| 合作同步 | 已追通HP结果到客户端对象字段写入的静态路径；同一事件通道、注册表和系统回调已闭合。真实送达、渲染和全部权限/异常仍待验证。 |
| 模型／特效 | 基础MPQ／154份DBC、实际31份M2碰撞及410份WMO碰撞投影各有组件证据；最新资产完备性、动画、材质、特效与实际渲染仍未完成。 |

依据固定发行包中的 `dist/wasm/WabtRelease.js`、匹配工作流及 [官方 WASM 指南](https://github.com/morluto/rea/blob/main/docs/wasm-artifacts.md)。说明文档 main 可能领先发行包，执行以本地 6.8.0 的 `--help` 和实际结果为准。

## 文件安排

- `toolchain.json`：工具版本、包完整性和能力限制；`.toolchain/` 保存本地工具。
- `targets.json`：明确区分网页核心与旧 Windows 原生基线；`local.sources.json` 只保存本机文件位置，不提交。
- `scripts/`：固定版本启动器和可复现分析入口。
- `reports/`：可进入 Git 的精简结论，保留 Evidence ID、范围及未知项。
- `RECONSTRUCTION.md`、`reconstruction/`：全模块覆盖/验收清单和独立规则实现。
- `VERSION_STRATEGY.md`：latest137目标、固定136静态/135动态研究及0.134.0/0.126.0历史参照的分工和迁移策略。
- `evidence/`：原始报告与只读输入副本，仅本机保留；`originals/`、`work/` 也不提交。

研究结果接入正式封装时，固定原始 SHA-256、记录精确补丁和回退方式，并运行对应回归。单机规则实验与官方合作同步分别验收；显示数字的变化不能当作真实伤害／生命值修改成功。
