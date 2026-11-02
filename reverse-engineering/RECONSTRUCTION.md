# 独立重造的工作基线

新增[固定139独立运行入口](reconstruction/RUNNING139.md)：直接读取451原始资源／67,281,330B，重新构造world后运行开局和自然战斗；不加载EXE／WASM／原件内存或预解析world。seed0／50各110步并选实际Thunder，seed111在真实Demo2卡停86步。93源码／392边、全部资源和3world全hash，以及311条状态对历史原件的声明投影均经[异作者只读复核](reports/2026-11-03-headless0139-independent-review.md)。这层新增原件case为0，独立无界面入口的生产能力与原件函数差分计数分开；完整14／884、渲染与完整一局继续实现。

官方于 **2026-11-02T14:31:18Z** 再核最新稳定版仍为 **0.139.1 / `b89633f9b`**。新版[非致死伤害80组／125次完整913](reports/2026-11-02-combat0139-1.md)已经fresh原件差分并通过[异作者独审](reports/2026-11-02-combat0139-1-independent-review.md)：55296B完整432单位记录／HP／f64累计与RNG一致，80份fixture含79个不同输入；其余8KB Game／统计／客户端包只观察，非自然App或完整Game。[增量静态30入口／143声明字段](reports/2026-11-02-engine0139-1-incremental.md)也通过[有限范围独审](reports/2026-11-02-engine0139-1-incremental-independent-review.md)：15规范化结构相同、15仍不同；882导入一致，JS仅17条有差异的生成注释去除后其余字节相同，另9条原样保留。静态对应不转化为行为通过；新1391只登记80／125，旧139实验继续固定原件。安装包与存档未替换。

固定139基线：此前官方元数据于 **2026-11-02T12:23:53Z** 核对为 **0.139.0**，首页stamp `f339dd20e0fe`。已完成[官方Windows／Web一致获取与实际9B构建身份](reports/2026-11-02-official0139-acquisition-identity.md)：两端均为 `f79c5e2b4`，Windows150,595,584B／官方SHA匹配，Web92,511,151B／本地SHA固定；获取前后元数据逐字一致。[139完整静态索引与增量清单](reports/2026-11-02-engine0139-incremental.md)已固定177101函数／882导入、30/30主要入口身份；本轮核对143行技能／职业／种族／地图声明一致，19个入口仍有编译或结构差异，不能据此判行为等价。首次下载与工具失败均保留，139其他行为迁移另行验证，**不将旧版通过转记139**。现有安装包与存档未替换。

固定139的[限定非致死伤害80组／125完整913调用](reports/2026-11-02-combat0139.md)已重新执行新版原件，0声明差异，[异作者独审通过](reports/2026-11-02-combat0139-independent-review.md)。新版真实单位stride为432、导入882；完整单位字节与声明的HP／累计伤害／RNG等比较通过。合成Game／空items、spells、1972 proc队列／无context的边界明确：不代表完整Game、自然构造、死亡、原生Windows或完整一局。Pilot4组／5调用另存，不加入正式80／125。

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

[已有顺劈技能的有序升级／new与upgrade路由](reports/2026-11-02-select-upgrade0139.md)19fixture（18个不同输入）／57目标入口经[异作者独审](reports/2026-11-02-select-upgrade0139-independent-review.md)：真实appseed完整1108→显式XP5→实际三卡→1093，18次upgrade／1次new，无改卡／重抽。17个真实可达的首轮cleave组合全含（tier0两种、tier1..3各三、tier4六种有序pair），逐kind的rank／value／count／damage尾乘及4640B owned记录、1311项属性、285项key、57份raw树一致；180576B背景守恒，live456已知／152 None保留。五表逐字静态绑定，动态只含本域0／1／2表；其它技能／重复／饱和升级与gold仍未知。错误搜索了不存在的第18键的16384次纯模型输入搜索已保留，原件执行0，不计覆盖。

[真实自动玩家更新／Human perception与到期](reports/2026-11-02-player-update0139.md)5cadence／155次完整2123经[异作者独审](reports/2026-11-02-player-update0139-independent-review.md)：保留4活NPC／两Rune和全部背景，真实1238调度5次perception，damage1.03→1.18；1秒1020保护及14.5秒种族效果到期，并核0.1累计的实际冷却边界。72键×160快照共11520项、3680属性、owned25600B／racial12800B及15条完整self306／308／309共240B一致。live19840B物理重放仅20B新scratch观察后仍None，其余19820B独算；Aura为48×16B，每次1173新owner未写payload保留None。401760B Game继承／355725B非入口字段／491040B背景严格守恒。此为初始中心、满血、learned无近目标的组件域；未禁racial或清NPC，也不等于AI／受伤再生或主884整帧。5次1108／4677／1093前段按已比较目标另计15，2945／1600各5次是setup；effects静态支持报告不重复算155。

[Windows／WASM的114技能声明直接结构对应](reports/2026-11-02-native0139-ability-layout.md)另有新静态证据：原生120B／WASM88B记录、64／32位fatptr和字段顺序不同，ID／默认名／图标／kind列表／effect12／numeric40／exec／school全部一致。不能把WASM偏移直接套到Windows，也不据此验收native伤害函数、Game／Unit ABI或行为；新增动态case为0。

[真实四敌人AI追击→自然近战受伤](reports/2026-11-02-enemy-ai0139.md)3cadence／92次完整925经[异作者独审](reports/2026-11-02-enemy-ai0139-independent-review.md)：不移动或清除NPC，首次925真正生成并保留78400项BFS路径，三份完整cost map逐项一致；79条本域可直达路线／2976次射线采样、83条移动221及52次自然1076受伤／330包均独算。全部135条新包6637B、158976B NPC物理重放、230736B Game非入口字段及132480B其它背景守恒；HP实际下降，无补满血或禁racial。history18972已知／15396 None保留，容量4／8／16／32与恰10秒保留已验，环绕／搬迁／超过10秒清理未覆盖。只接受925独立调度域；与2123、正回血、减速、死亡清除、后续刷怪及主884尚未串联。

[雷霆一击单目标18组](reports/2026-11-02-thunder-clap0139.md)与[自然App seed多目标／暴击9组](reports/2026-11-02-thunder-clap-world0139.md)两批共119次完整922经[联合异作者独审](reports/2026-11-02-thunder-clap0139-independent-review.md)：147次伤害、23次普通死亡、14次自然正暴击、51次多目标／最多3目标及372次减速字段写入一致。半径10／暴击率.05不改、NPC原位置保留；显式玩家近身／中点与时钟仍是受控输入。exec2经27754选目标、10490生成mask0有序目标清单，逐目标913伤害后同步2189减速；未向1775／3755入队。205632B NPC及28000B既有pickup物理重放、308448B Game入口继承均核；仅116条已知launch／reward包5946B有序子序列恢复，另外317条592／169及额外统计owner语义未知。此域是直接施法组件，不代表1238冷却调度、AI减速／到期或2123／主884联合。

[实际雷霆减速→AI续行／到期](reports/2026-11-02-enemy-ai-status0139.md)4fresh／144完整925＋4次真实922生产经[异作者独审](reports/2026-11-02-enemy-ai-status0139-independent-review.md)：3秒前一ULP的新运动速度2.625，恰3秒／后一ULP恢复5.25，已存在运动段保持原时长。8份完整78400项BFS、102条完整925消息4856B、1次live12有效接触保护及其后5次实际受伤一致；保留原4NPC／2owned／racial／live／Aura。producer6912B及AI248832B NPC物理重放、373248B Game入口继承均核。四个显式时钟／玩家位置域仍非2123／1238自动调度或完整884，路径仍是可直达域。

[主循环计时前缀](reports/2026-11-02-frame-clock0139.md)484组／500步经[异作者独审](reports/2026-11-02-frame-clock0139-independent-review.md)，接受原884连续100B指令＋原10B locals与4B返回尾的微模块域。首次tag／f64差分0..0.1限制／f32舍入、815非NaN位级值、2负零、109／76次NaN分类及64000B canary一致；域外hash仅保存500个比较标志，没有原hash pair回读。两处2352加法分别受2588／2587布局控制，均仅静态；25纯算式自检不算原分支执行。500片段调用新增完整原函数入口0。

[主884阶段顺序](reports/2026-11-02-mainloop0139-schedule-static.md)另静态定位唯一连续14阶段及其guard，其他路径／App所有权仍未知。[Windows当前两段函数](reports/2026-11-02-native0139-upgrade-functions.md)1123B／257指令由LLVM与Ghidra逐字节对应，其中513B升级值函数与当前25511五kind结构静态关联，partial owned字段相差4B；610B另一候选仅待进一步检查。未运行EXE或这些原件函数，后续x86机器码仿真另立新批，不能把静态对应当Windows玩法通过。

[参数保真的正回血／吸血v3](reports/2026-11-02-healing-hurtactor0139-v3.md)fresh5＋4经[异作者独审](reports/2026-11-02-healing-hurtactor0139-v3-independent-review.md)：9份实际NPC GUID及显式1076三参(1,0,0)由冻结输入供模型与原件同源消费，数值与输入均匹配。42次完整2123／9次1076／32次922验证27次正再生、28次正Leech、42伤害事件、8暴击及9次死亡；HP／最大值封顶／key22和28、共享G960／G1016与f64来源累计、83份语义账本／66条Vec48 name／icon／total投影一致。hurt域16356B NPC未知字节保持原物理值。入参5的0是category0下明确受控未消费值，并非925动态消息队列index的复制；内部1466描述符参数只静态核对。完整incoming历史／分类／回调及2077物理key／catalog／buckets仍未覆盖。

[v2数值观察](reports/2026-11-02-healing-hurtactor0139-v2.md)保留，但[独审因实参不一致明确拒绝](reports/2026-11-02-healing-hurtactor0139-v2-independent-review.md)，未把数值巧合当通过。旧作者11件、归档、失败批和全部收据保持原样；v3采用新checker／runner／builder及新原件批，三个共享core不变，不将旧v2再加算。

[普通刷怪952的前40秒域](reports/2026-11-02-spawn-schedule0139.md)3fresh／1080入口与[独审](reports/2026-11-02-spawn-schedule0139-independent-review.md)已通过：实际初始budget3自然产生47新NPC及47条完整169共8413B，并跨30秒解锁产生2个definition1敌人。保留原开局全部物件，仅驱动clock；最久37.5秒、静止且无战斗。density-fill与55距离回收分支均未执行，不以谓词检查代替分支验证。冻v1源码的2424／2440变量及pending标签颠倒：真实2424为60秒多形波次，2440为240秒普通精英；两者在本批均未进入，正确角色已在注册与只读勘误另记。40／60／240秒及Boss仍待恢复。

[近身自动施法1238／2123](reports/2026-11-02-player-autocast0139.md)4fresh／96正式目标与[独审](reports/2026-11-02-player-autocast0139-independent-review.md)已通过：48次完整1238＋48次2123，验证普攻4次含3自然暴击、顺劈4次、雷霆3次、种族1次、正吸血10次、正再生24次及5死亡含3移动死亡。29前缀／warmup／925／1076 setup另列；已知37条包1587B仅是实际64条2593B的有序子集。真实NPC位置、HP、racial与owned均保留；显式玩家位置／XP5前段不称自然完整流程。basic的913末参1用于抑制spell damage包，owned为0，继承Game908另计。

[Windows513B升级值指令仿真及WASM25511配对](reports/2026-11-02-native-upgrade0139.md)2150组与[独审](reports/2026-11-02-native-upgrade0139-independent-review.md)已通过：实际x86_64机器码在macARM的Unicorn2.1.4中执行2150次，另有2150次完整WASM25511；同一2150逻辑fixture只计一次。114声明／五种kind／tier0..4与局部owner布局已核；60组含NaN输入，记录输出全部+0，不是60个NaN输出。页面保护比较保留为captured标志与源码证据，不称保存了全部原始before／after字节对。首轮SIGILL与pilot均保留并排除，未启动Windows应用、Wine或VM，不证明native伤害／AI／主循环。

[连续自动战斗与尸体清理v2](reports/2026-11-02-player-enemy0139-v2-independent-review.md)通过异作者独审：3fresh／360个2123→925组件步，共720正式目标、15前缀setup另列。9次自然AI受伤、103正再生／10正Leech、25伤害、12死亡与清除，以及7普攻／9顺劈／3雷霆／3种族均核。168条已知消息7571B仅是实际223条9572B的有序子集，925后缀完整恢复。此批从显式XP5／已选Thunder开始，未执行2890、952或主884其余阶段，不当作自然首次升级或完整帧。

[死亡保留与同帧消息顺序v2](reports/2026-11-02-enemy-ai-dead0139-v2-independent-review.md)11fresh／146完整925独审通过：144隔离入口＋2真实同帧probe，23回收／73完整925包2578B。死亡后elapsed<=1.2保留，>1.2才稳定432B移除，capacity／stale tail照原保留；queued170先于motion221／attack330。378来源setup含120前序组件对只算来源，非新增完整包序覆盖。[旧360失败](reports/2026-11-02-player-enemy0139-v1-rejected.md)和AIdead v1源均原样保留且不接受组合；v2使用新代码、新原件和新独审，不倒填旧通过。

[真实40秒资源调度v2](reports/2026-11-02-spawn-schedule0139-v2-independent-review.md)4fresh／3119完整952另验通过：132新NPC及4个资源，覆盖kind3／4／5；源仅驱动clock，37物理检查点保留所有初始对象与未知字节。此批仍静止／无战斗／<60秒；2424为wave60、2440为elite240，旧v1标签勘误保留。正killcost、density填充、far回收、60Rune／波次／windows到期及Boss另批，不能由本批推定通过。

[首60秒完整刷怪调度v3](reports/2026-11-02-spawn-schedule0139-v3-independent-review.md)4fresh／4096完整952独审通过：自然seed0／1／5／8分别走首波shape0..3，166普通预算＋18波次NPC，50上限实际拒绝170预算请求／7波次请求，shape1的5个charge字段与2*distance+12路径值一致。另有4个40秒资源及4个60秒Rune；192条完整169＋4条150、56物理检查点及145152B完整Game核对。Rune的+12是caller残留heap表达式，逻辑保留16B None，4条preRunePickupBase+176原始表达式另核，不反填为游戏数值。此域仍静止／无战斗；正killcost／移动死槽／density正分支／far回收／windows到期／Boss180／elite240及完整952仍未知。

[运动暂停／恢复](reports/2026-11-02-world-pause0139-independent-review.md)8fresh／42目标（12×26364、15×35988、15×25613）独审通过，32来源setup与11 cleanup分列。真实1108→925四移动NPC及受控aux／comp保留原运动记录；gather40、f32插值、cap5／9／18和158条完整221共5490B一致。整段Game108864B／actor与背景148368B守恒；helper只写sequence与消息，phase来自明确外层控制，未执行完整2181／1093。

[受控终局49961](reports/2026-11-02-terminal0139-independent-review.md)5fresh／10完整目标独审通过：实际movingNPC、显式field400及phase／endless／UTF8 hero输入，12完整221／232共236B与2条完整victory JSON466B、capacity272一致。自然Boss→400尚未恢复，不能把受控phase5当完成游戏。[延迟施法队列38553](reports/2026-11-02-frame-deadline0139-independent-review.md)另有58fixture／124完整目标独审，187完整306共5582B；队列来自受控32B输入，天然producer仍未知。

[0.139.1属性重算1542](reports/2026-11-02-stats0139-1-independent-review.md)新增10,569份新期待与10,569完整原件调用，经异作者只读独算359,346声明值全部一致。当前9职业／8种族14modifier、9完整函数body及allocator93365重绑；只沿用历史输入和未改独立数学模型，不沿用旧输出或验收。七组属性来源仍为显式fixture，1537条移动消息只比数量；NaN仅分类，27,394,848B raw Game为观察，完整Game／自然来源／Windows／整局不在范围。最新1391累计10649fixture／10694正式入口，与固定139分开。

[战斗来源刷怪v4](reports/2026-11-02-spawn-combat0139-independent-review.md)6fresh／18完整952通过异作者独审，319来源setup另列。真实1／2／4死亡及再次击杀产生正killcost，18次衰减／3次正追赶／6个密度补怪，24条完整169共4296B及实际level2字段34一致；50上限不把尸体当活怪，完整物理槽和stale tail保留。两移动来源含120前置2123→925组件对，只提供数值源；目标952替代925，不能视作主884正常整帧顺序。远距回收、Boss180／elite240与windows到期仍未知。

[自然首次升级／选卡／续战v2](reports/2026-11-02-natural-growth0139-v2-independent-review.md)已通过不同作者只读独审：6fresh／588组件步（旧三组fresh重跑282步、新四阶段三组306步），2123／925／2890各588完整调用、952共306、1093共4，合2074目标入口；18开局setup另列。真实单cleave／XP0／原站位开局，通过伤害死亡→拾取→6次升级与实际夹顶治疗→真实首卡→Thunder tier0／2续战，保持20600／1020与非空live／Aura、真实受伤和完整物理槽。新四阶段从首步即运行952，造25NPC／174正killcost状态；seed111真实demo卡明确停phase2，没有重抽。

1093→4603选卡立即拾取分支已修正：kind0且marker非0无条件消费、marker0检查post1542半径，56B正向稳定前移后raw u32合计，仅一次XP倍率／86979舍入再在phase2调用4677，随后才恢复。实际额外3球／raw4→award5一致；若又产生pending选择仍明确Pending。旧首批273差异、错误2890初判、旧v1有限观察和独参live12／schema失败均保留，旧10件不倒填通过。

686已知包35090B仅为859原件包43315B的有序子集；外部clock和UI选择、原件resource-only上下文、共享ledger语义投影及known／None均有范围限制。完整2077堆、其它十阶段／884真实调度、20秒Guardian／幼狼／挫志怒吼／二次升级及完整一局继续补齐。

[普通Kobold／幼狼](reports/2026-11-03-ordinary-family0139-independent-review.md)4fresh／56目标（4×952、40×925、12×913）经异作者独审：实际30.1秒受控刷怪产生7NPC，两Wolf与两无Wolf对照全部保留。23次接触的真实英文归因、8次Leech、4死亡与1.0保留／1.25稳定回收，以及154已知包9277B在170原包9801B中的顺序匹配。两个72B定义分别读取XP56／cost60；两者恰均1，不能泛化其它敌人。受控clock跳转及玩家跟随实际目标不等于自然30秒；Demo／Thunder伤害来源未由本批动态验收。

[挫志怒吼1160](reports/2026-11-03-demo-shout0139-independent-review.md)16fresh／146目标（80×922、66×925）经异作者独审，80setup另列。tier0／2、14米边界、重复、41命中／1暴击／2真实死亡、39weakness应用、9接触中1次active-live12保护及6秒Aura到期均独算。922→2189→21553／4593的弱化双槽与到期包序已绑定；55已知cast包1668B仍只是139原包5703B子集，48条AI包2297B则全序一致。该组件批实际最多1目标，中点样例为0，不称多目标或1238自动冷却通过；同seed111自然5目标续战另批等待复核。

已冻结作者报告保留执行时的pending状态，独审与版本登记记录最终接受范围。固定139累计17158份完整原件函数域fixture／33334次正式WASM目标入口（33333正常／1预期越界）；2150次Native仿真与484组／500计时片段分列。最新1391仍为10649fixture／10694正式入口。自然Demo／第二候选、20秒Guardian与raw资源独立入口继续复核／接线；完整884、Windows应用与独立完整一局仍为0，实验数不表示完成率。

固定138的[属性计算10569组](reports/2026-11-02-stats0138.md)、[非致死伤害80组／125调用](reports/2026-11-02-combat0138-independent-review.md)、[默认构造162次](reports/2026-11-02-initial-state0138.md)及其独审保留各自窄域；[13入口迁移守卫](reports/2026-11-02-flow0138-migration.md)仍是静态证据。它们均不等于138／139连续流程或Windows原生验收。

本轮固定135的[移动→战斗→真实符文拾取](reports/2026-11-02-opening-moving-rune0135.md)完成新460帧／4选卡／44次完整968输入／6488阶段／6490原件入口，0声明差异，[独审通过](reports/2026-11-02-opening-moving-rune0135-independent-review.md)。第444帧（raw索引443）消费实际刷出的kind5符文，停止移动后继续16帧；恢复请求133，但当时满血266，故只证明cap、移除与通知链，不称非零回血增量。117源／100production、snapshot／独立预解析world／部分类型App和外部clock边界明确。

[移动2328的38组／完整968本地输入33组](reports/2026-11-02-player-motion0135.md)和[校正确认199的88组](reports/2026-11-02-player-correction0135.md)均各自独审通过。真实键盘／摇杆生产、自然App／完整880、远端同步仍未接通；ACK组件尚未作为连续流程动作接线。135结果不转记138，Windows原生执行与独立完整一局均为0。

固定135新增[同状态战斗至失败结算](reports/2026-11-02-opening-fatal0135.md)：921帧／7选卡／44次控制运动／12945阶段／12947原件入口，声明字段0差异，[独立只读复核通过](reports/2026-11-02-opening-fatal0135-independent-review.md)。history48容器、已知字节与实际字符串、事件维护的七项统计、非平地停止、defeat JSON与致死后的五阶段尾续接入同一状态；1条普通27457移动221和10条45845停止221按实际wire grammar区分，原始包全保留。原件快照、预解析world、部分类型App与外部clock等边界不变，**仍不称完整游戏或139验收**。

[raw451→独立世界→同状态死亡](reports/2026-11-02-raw-fatal0135.md)另已完成：451份原始资源／67,281,330B，独立模型921帧／7选卡／44次控制运动，115项阶段与已列终态owner组合一致，[只读独审通过](reports/2026-11-02-raw-fatal0135-independent-review.md)。共113份core字节不变，12946份逐阶段摘要与known／None字节均核；这是两模型路径的组合，**新增原件case0**。模型不使用预解析world，按冻结源码／provider与路径hash证明读取边界；作者没有可追溯的OS级读取审计收据，独审记录自己的read guard。真实App／完整880／Windows原生与完整一局仍未验收。

历史[静止玩家750帧](reports/2026-11-02-opening-player-sources0135.md)、[raw451→750模型入口](reports/2026-11-02-raw-physical7500135.md)、[raw451→移动460模型入口](reports/2026-11-02-raw-moving-rune0135.md)及其各自收据保留范围，不相加。来源163组、死亡40组、recap103组是先行组件验证，后继连续整合另用新收据。

目标是逐项拆清原作逻辑和数据，形成能够独立运行的游戏核心。功能目标持续跟随官方最新稳定版，每轮固定版本与SHA：**固定0.137.0 / `d171b8f9f`已有完整静态profile与非致死伤害80组/125调用0差异；固定0.136.0 / `fe24fb74c`仅静态profile/迁移候选，动态验收0**。持续动态组合研究保持**固定0.135.1 / `90898d5e3`**及原SHA，旧`0898d5e3`为历史截短alias，旧收据和输入不覆写；0.134.0 / 983346a7与0.126.0 / 3e72472a继续作各自固定历史参照。任何旧通过均不自动转记新版。完整身份及分工见[targets.json](targets.json)、[先前身份采集状态](reports/2026-11-01-latest-version-state.md)与[版本策略](VERSION_STRATEGY.md)。工具、原件与分析产物留在本机忽略区；独立实现放在[reconstruction/](reconstruction/README.md)。

此前metadata核对截至 **2026-11-01T16:51:40Z**，官方manifest仍为同一137 EXE SHA、HTML stamp仍为`c628fd68823e`；仅复查清单/页面，未重取大二进制，见[核对收据](evidence/official-latest137-closecheck-20261101T165135.413048Z/receipt.json)。

固定135新增[400帧／第四次选卡与Battle Shout组合](reports/2026-11-02-opening-battle-combat0135.md)：400受控帧／4select／5604stage／5606原件入口、0声明差异，98源／85 production；实际第379帧选择Battle Shout，随后完成6673施放、effect8与属性变化，最终level5／XP6／gold53。修复后fresh收据SHA `b5d9c546789401d738b43cc58cac1d7aeb117c94753ed4d63f60d923224520a7`，该限定投影已通过[400帧只读独审](reports/2026-11-02-opening-combat0135-400frame-independent-review.md)（receipt SHA `376b09cd9ce10da25396d815824432e48eb456dbb1aeaea9674db95d25aa6482`），核对24,443,084个已知叶；905包峰值及其未恢复的payload语义仍只观察。原件snapshot、独立预解析world与外部f32调度的范围保持明确，完整880／Windows执行／独立一局仍为0。

另有[raw451资源→world→opening→400帧](evidence/asset-combat400-owned-20261101T174254.757426Z/model400/receipt.json)纯modelselfcheck：67,281,330B、92源与资源前后不变，不读原件memory／WASM／预解析world，400帧／4select也达到level5／XP6／gold53；三项world SHA、四guardian实体／GUID／timer及None字节均核对。[35项终态衔接](evidence/asset-combat400-owned-20261101T174254.757426Z/projection-bridge.json)与差分组合一致；这层不新增原件case或完整880帧。

[Battle组件134组／171调用](reports/2026-11-02-battle-shout0135-independent-review.md)与[CAS codec两正例／26负例全拒绝](reports/2026-11-02-opening-combat0135-cas-codec-review.md)已分别通过各自范围独审。CAS保留6008条完整logical records（1,662,490,742B；unique blobs 83,331,346B），没有删阶段或字段；旧`171633.375141Z` decoder批与120／250 checkpoint保留，不与最终400计数相加。该400旧批当时的下一纯模型帧401为`pending_due_event:G2444`资源40秒到期；[资源组件64组](reports/2026-11-02-resource-spawn0135.md)单独差分0差异，未接入这批旧400；后继500使用独立新收据，不能倒填旧批。

固定135的[250帧守卫出生组合](reports/2026-11-02-opening-guardian-combat0135.md)完成250受控帧／3select／3503stage／3505原件调用、0差异，94源/84 production；跨20秒4守卫出生并继续50帧，U68地址保持None、timer所有者按GUID严格核payload。该限定投影已通过[最终只读独审](reports/2026-11-02-opening-combat0135-250frame-independent-review.md)（receipt SHA `556693d5bac9b86545dd89a57b042bdb54823e49d4f845b5547a3a978d7158c7`），仍是预解析world、原件snapshot及外部clock域；旧120收据保持原身份，不相加。

另有[raw451资产→world→opening→250帧](evidence/asset-combat250-owned-20261101T163850.979737Z/model250/receipt.json)的纯modelselfcheck：67,281,330B、91源前后不变，不读原memory/预解析world/WASM，250帧／3select至level4／XP3。复用同一world的[后继纯模型](evidence/asset-combat250-owned-20261101T163850.979737Z/continuation/receipt.json)继续至379帧／4select，第380帧因实际选到battle_shout停止；没有重抽卡。379是该旧模型的边界，当时原件差分到250；后继400验收另列，旧收据计数不改，完整880/native/一局仍为0。

这里的“完成”需要覆盖行为、状态变化和结果，而不是只有函数地址、解码文本或一份大关系图。原作Rust变量名和源文件原文没有恢复；重造不以逐字找回这些标识符为验收条件。

## latest准入与固定版本研究

| 版本域 | 当前事实 | 验收边界 |
|---|---|---|
| 固定0.138.0 | [完整profile](reports/2026-11-02-wasm0138-profile.md)；[非致死913：80组/125调用](reports/2026-11-02-combat0138-independent-review.md)；[完整1512属性10569组／10569调用及独审](reports/2026-11-02-stats0138.md) | 两个限定组件分别验收；13入口迁移仍为静态守卫，135/137结果不转计。新版完整流程／Windows运行／独立一局为0。 |
| latest138默认构造 | [162次fresh完整1571、40完整226及独审](reports/2026-11-02-initial-state0138.md) | 空profile／borrowedflatquery，502B known，未知byte不补0；不是Rc/cache/App／phase1。 |
| fixed135玩家移动 | [直接2328的38组与完整968本地33组](reports/2026-11-02-player-motion0135.md)，两批独审通过 | 默认Elwynn／phase1／mode0；自然设备输入、primary辅助面／其它地图、自然App及远端模式待恢复。 |
| fixed135校正ACK | [88组完整968(opcode199)及独审](reports/2026-11-02-player-correction0135.md)，28clear／60retain | packedGUID消费、tag1与unsigned确认序号；真实pending贯穿连续战斗、非规范输入、mode1未知。 |
| fixed135敌人来源 | [163次完整1073及独审](reports/2026-11-02-incoming-source0135.md) | 148英语NPC名／raw分类→history组件；registry/proc与同状态死亡未知。 |
| fixed135死亡与recap | [40例死亡组件](reports/2026-11-02-player-death0135.md)及[103例1367](reports/2026-11-02-player-death-recap0135.md)分别独审 | 空地形组件；真实world stop、有序AI drain、计数／hero／history所有者与连续终局待接。 |
| fixed135移动拾取闭环 | [新460帧／4选／44motion／6488阶段／6490入口及独审](reports/2026-11-02-opening-moving-rune0135.md) | 同状态消费真实kind5并续16帧；HP满266，恢复请求133被cap；不是自然App／完整880／原生／一局。 |
| 固定先前固定0.137.0 | [175327函数完整profile/RO索引](reports/2026-11-02-wasm0137-profile.md)；[资源1420新90例/90调用与独审](reports/2026-11-02-resource-pickup0137-independent-review.md)，36源、完整56B/169/Gguard；[非致死/no-proc damage913：80组/125完整调用0差异](reports/2026-11-02-combat0137.md)，11源、全432B记录/f64/RNG | [限定数值域独审通过](reports/2026-11-02-combat0137-independent-review.md)；完整death/proc/137开局/Windows ABI及运行/一局未验收。12个原生NPC声明仅静态互证，135/136结果不外推。 |
| 固定0.136.0静态迁移 | [175319函数完整profile/RO索引、12入口候选和引用审查](reports/2026-11-01-wasm0136-profile.md)；实际9字节build `fe24fb74c` | 动态case0；候选同形与callee/数据等价分开验证。 |
| 固定0.135.1动态研究 | 既有与进行中的独立资源、opening、combat、XP/选卡实验保持原始SHA；实际build `90898d5e3` | 下表计数仍属于各自冻结135收据；新组合另记，不倒填历史或转记136/137。 |

固定135的[新opening→combat→XP/首次选卡组合](reports/2026-11-01-opening-combat0135.md)为单human warrior／seed0／navigation False：120帧、1select、1681stage、1683原件入口0差异，90源含80 production。真实1089产生phase1，4NPC/2kind2/4special/2window/69boundary/0companion和实际capacity保留，None未知字节不清零；level2实际index0选择thunder_clap后续33帧。模型用预解析独立world，原件从合法snapshot恢复，时间是外部显式受控调度；不代表完整880、native执行或完整一局。旧headless8/1614/22607/11、frame573/944、death-pickup204回归各自独立保留，不与新case求和。 该限定投影已通过[只读独审](reports/2026-11-02-opening-combat0135-independent-review.md)，receipt SHA `2b768595711ff9f5daea0fcd718c4e963b8d2d02b652823285444000e2e96d2d`；原packet payload语义仍只观察。

同版[raw资产独立入口](reports/2026-11-01-opening-combat0135.md)另以451文件／67,281,330B、9tiles直接生产world/opening并推进120帧／1select；87源前后相同，无production closure逃逸，原memory／预解析world／WASM读取均false。三个world产物SHA与已验证query产物一致，最终level2／XP6／gold7。此收据为独立入口层，不增加原件差分case或完整880计数。

[符文消费130组／244调用](reports/2026-11-02-resource-consumer0135.md)、[混合拾取60组／61调用](reports/2026-11-02-mixed-pickup0135.md)及[逐帧到期38组／56完整2088](reports/2026-11-02-resource-player0135.md)分别独审通过；恢复资源效果、同一RNG下逆序奖励、完整live32／Aura48和速度归还。三批计数各自独立。后继[0／8／1020共存61组／119调用](reports/2026-11-02-self-buffs0135.md)与[完整live producer109组](reports/2026-11-02-live-owner0135.md)均获异作者独审；保留kind12、完整inactive尾与partial append来源，额外回血由typed passive13经完整1512生产。此处组件计数保持独立；后继controlled移动近身拾取见moving460，自然输入设备仍未恢复。

## 固定0.135.1动态研究的迁移与验收

| 范围 | 当前证据 | 下一步 |
|---|---|---|
| 静态profile | [完整WABT/WAT/SQLite](reports/2026-11-01-wasm0135-profile.md)，175317个defined函数/824549条直接调用，完整函数范围和data payload读回通过 | 结构覆盖不代表全部逻辑已恢复；间接调用和运行时顺序需单独验收。 |
| 函数与布局 | [14个既有角色及3个新增入口](reports/2026-11-01-migration0135.md)有本版body/签名guard；malloc91941，等级/HP/派生区重排，G1572为护甲上限 | 静态映射不直接计作原件运行验证；有效护甲27375/玩家受伤1073和AI921已在下行按限定域另验。 |
| 受控原件入口 | 主Node及本轮M2／WMO fresh域32MiB／878deny；snapshot query／position／opening独立256MiB／878deny，正常返回栈1048576；均仅增export、保留callee | 共享52role不变，snapshot9role与私有4／2role各实验准入，不是覆盖比例。历史resource browser128MiB／17allow、world browser256MiB／24allow分别保留。 |
| 真实空profile构造 | [最终055136的151组与独立复核](reports/2026-11-01-initial0135-independent-review.md)：完整1560输出的starter80、racial80、属性/HP/RNG、预算/计时器/flags及u64身份0差异 | 输入为显式空376B selected-profile，返回真实phase0；上游角色profile、初始App熵、非空装备天赋和独立phase进入未闭合；真实账号/world/1089的后继观察另列。G1256是racial，class starter在learned80向量中。 |
| 属性1512 | [10569例完整原件差分](reports/2026-11-01-stats0135-spec.md)，23派生word、HP、4辅助字段、3对象键、速度/序号和队列数0差异；只读复核通过 | 真实来源producer、已有树项更新与包字节仍未验收；每级成长和选卡收尾的限定组合在下行另验。 |
| tick与暂停命令 | [完整原880/1371的6558例](reports/2026-11-01-game-loop0135.md)，5400暂停命令＋1158tick，0差异；20个静态函数/34条guard另列 | 只独立比较暂停phase、上次时间/marker和模拟时钟；无单位/空队列/skip-spawn域。tick其他phase、完整调度、fresh终局保存及party/victory/Endless仍未运行验收。 |
| 能力目录 | [114能力/9职业](reports/2026-11-01-catalogue0135.md)按本版指令/data重提；rockbiter/stormstrike平衡变化真实存在 | 表和kit不是全部执行效果/解锁/天赋producer验收。 |
| 候选与记录应用 | [候选2159：4126例](reports/2026-11-01-candidates0135-spec.md)、[初始化1072：2781例](reports/2026-11-01-new-ability0135-spec.md)、[有序升级1072：3629例](reports/2026-11-01-selection0135-spec.md)，均0声明差异 | kind0 metadata/RNG与80B记录为各自域；kind1/2、展示payload、真实来源和全后处理未知。 |
| XP消费者组合 | [完整4630：1151序列/3450调用](reports/2026-11-01-level-cycle0135.md)，逐级属性→治疗→阈值→kind0候选 | 死亡/拾取producer及同状态选卡现已在下行受控切片连接；完整自然调度仍未完成。 |
| 选卡收尾组合 | [完整1072：660序列/1090调用](reports/2026-11-01-selection-cycle0135.md)，new/upgrade/gold→属性→4600 XP扫取→下一kind0或phase1，0声明差异 | 只比7个已建模numeric player keys；其它原件keyed state完整另存，不能假定全部cosmetic。kind1/2 metadata、1202 aura/外观producer与全部消息仍pending。 |
| 普通/精英生成基础 | [原20272/26361/5736共4021例](reports/2026-11-01-spawn0135-spec.md)，真实148定义/12地图、424B写入、两次RNG和GUID，0差异，1211例实际生成 | 位置/owner为解析输入；普通947/位置生产在下一行另验，Boss/特殊波次、terrain/AI与完整自然调度未完成。 |
| 普通刷怪帧与位置 | [完整947/8751：1580例](reports/2026-11-01-spawn-frame0135.md)，1275普通帧＋305位置；实际9360新单位，0差异；[任意heading扩展5068例](reports/2026-11-01-spawn-motion0135.md)补齐此前8个非轴输入 | 仍限定平地/owner0；grid/pathfinding/fallback及完整调度缺失。5068含重放先前1580，不相加为新覆盖；80处NaN只比较分类。 |
| Boss与精英调度 | [Boss871例](reports/2026-11-01-spawn-boss0135.md)：751次实际生成，60定义/全部timer payload、最终Boss附加和无尽；[精英549例](reports/2026-11-01-spawn-elite0135.md)：340次实际生成，难度配对与deadline | 两批各自平地、owner0和隔离的其它timer守卫；不是Boss/精英AI或全部947事件已完成。[事件2424/2376未知](reports/2026-11-01-spawn-events0135-pending.md)单列。 |
| 额外计时施法与命中 | [完整查询/922/916/1754：1314序列/3626调用](reports/2026-11-01-cast0135-spec.md)，25个tag0、execution0/2定义；目标/HP/RNG/延迟/冷却0未声明差异 | 916消费额外84B计时记录，不能代替已学80B主路径；本份语料空proc、无致死，只验其声明字段。 |
| 已学技能主自动施法 | [完整1076/1754：639组/5924阶段](reports/2026-11-01-owned-cast0135.md)，职业近战→已学80B→G1256槽basic隔离fixture→延迟命中，4923次有效命中自疗，0差异 | 支持25个effect0/execution0/2、空item/definitions/proc。旧basic是fixture标签，不能追溯称为真实racial验收；真实G1256由构造151、racial720及下行同状态切片另验，完整880仍缺。 |
| 死亡与混合拾取消费者 | [204组/871阶段](reports/2026-11-01-death-pickup0135.md)，376次普通死亡、136组进入候选phase2；XP/coin续RNG、逆序奖励和最新倍率0声明差异 | 原12组非空definitions失败证据保留；其原因现由下行855批非致死context0事件规则解释，不能转称致死proc已通过。同1076/拾取/选择的限定空proc组合见headless。 |
| 死亡位置与掉落placement | [完整1417/914：924组](reports/2026-11-01-ordinary-placement0135.md)及[独立复核](reports/2026-11-01-ordinary-placement0135-independent-review.md)：12地图、移动前/中/后插值、XP/coin分别clamp及高度，完整56B和RNG/计数0差异 | 使用pre-hit424B，不能从致死后duration0反推坐标。真实地形/grid/navigation、非普通死亡和物理对象/包仍缺。 |
| 六种racial self-buff | [完整922：720组](reports/2026-11-01-racial-cast0135-independent-review.md)，真实G1256的80B、6个kind9定义、live32/属性/HP/盾/三份attempt ledger，0声明差异 | 只允许新7/8/9记录的+16未写词未知；war_stomp/escape_artist、aura/display keys和包未恢复。真实racial调度组合另见headless。 |
| 非空definition事件 | [完整984/8157及914：855组/1004阶段](reports/2026-11-01-proc-events0135.md)及[独立复核](reports/2026-11-01-proc135-independent-review.md)，kind27/zero16B gate恢复，解释并重新验过旧12组差异 | 限显式非致死、context774整数0；致死loot与post-proc顺序、其他gate/producer仍拒绝，不把非空definitions传成空来源来冒称headless支持。 |
| 玩家受伤与长期近战AI | [27375/1073：2107例](reports/2026-11-01-incoming0135.md)；原416/1013保留，新增[trig6726、完整921共429组/3423步](reports/2026-11-01-ai-motion0135-independent-review.md)，含3条800帧角度跨2π轨迹 | 普通124melee、本地owner、平地/空producer、非致死域。中角上界421657408，极大角1814未恢复；3条长轨迹没有接触攻击，不能称80秒持续受伤。远程/Boss/真实地形/死亡复活仍缺。 |
| 玩家更新与尸体清理 | [完整2088/921：285组/444阶段](reports/2026-11-01-player-update0135.md)及[独立复核](reports/2026-11-01-gameplay-phase0135-independent-review.md)，到期过滤/重算/再生、年轻尸体保留和39635稳定清理，0差异 | 该隔离批使用真实perception racial但CD=Inf、learned为空，不能当真实开局调度。periodic/非空来源/11426及物理1453/1202输出仍缺。 |
| 暂停/恢复移动消息 | [完整1371→35514/25472→26200：396组/1136阶段](reports/2026-11-01-movement-pause0135.md)及[独立复核](reports/2026-11-01-gameplay-phase0135-independent-review.md)，604条221消息GUID/序号/stopflag与完整NPC字节通过 | 暂停不是no-op；按稳定顺序逐移动NPC递增G2412。非空112B辅助motion/88B claims、非平地几何与完整包编码仍缺；自然选卡暂停另由headless同状态验。 |
| 前阶段同状态切片061901 | [最终061901及独审062623](reports/2026-11-01-headless0135-independent-review.md)：8seed、1093帧、5473阶段、8次自然升级选择，0差异；1560生产的真实racial/HP/RNG与2088→1754→921→2862→947→1072连续共享 | seed3第105帧选卡后继续145个原件对照帧至250；其余7个选卡后下一模型帧明确pending_selected_ability。phase1显式研究解析、128槽初始zero storage；不是1089真入口、全880或完整一局。完整尾槽保留/24次复用均验，7个numeric keys之外的key状态单列未知。 |
| 持续AoE组件 | [area693组/5495阶段](reports/2026-11-01-area-effects0135.md)及[独审](reports/2026-11-01-area-effects0135-independent-review.md)：七个922 kind3定义与3757限定分支通过 | 组件32个单位word投影不是全424B；其在后继headless中的完整记录另验，915/3757其它来源及全部AoE仍缺。 |
| 历史含范围技能切片064308 | [8seed/1614帧/9695阶段/11select](reports/2026-11-01-headless-area0135.md)及[独审](reports/2026-11-01-headless-area0135-independent-review.md)保留 | 当时未执行/观察915；后继072329另列，旧统计不相加。 |
| 历史含idle915切片072329 | [8/1614/11309/11/11317](reports/2026-11-01-headless-effects0135.md)，65源/58core/9入口与旧独审保留 | 后继082927单列；不转记新尾阶段或相加。 |
| 915时钟/延迟组件 | [完整915：500组/2121阶段](reports/2026-11-01-effect-system0135.md)及[独审](reports/2026-11-01-effect-system0135-independent-review.md)，383正常+117预期raw255 pop后trap，17源/5边界/0差异 | 完整56/backing与424B严格；本组件不实现普通910/120，三Boss矩形另列。非空56未接主切片，physicalpayload保留但codec未知。 |
| 当前14阶段独立切片082927 | [14阶段独立切片](reports/2026-11-01-headless-tail0135.md)：8seed/1614帧/22607阶段/11选择/22615原件调用，67源含60core、16角色，0差异，[独审](reports/2026-11-01-headless-tail0135-independent-review.md)通过 | 6未知技能/2预算，phase1/初始zero槽明确；14单状态尾入口不是完整880/前段/party/整局。 |
| 五个尾阶段组件 | [573组/944入口](reports/2026-11-01-frame-systems0135.md)及[独审](reports/2026-11-01-frame-systems0135-independent-review.md)；975无execution11、38007完整非空队列/306、2602 expiry/idle及精确pending、2573守卫、49037假谓词 | 23预期原件异常分列；975守卫在入口执行时检查，终止选卡可含11后下一帧pending，活跃资源/secondary/claim不伪装空。 |
| 真正胜利终态 | [416组/832次49037+416真实1560](reports/2026-11-01-terminal-transition0135.md)及[独审](reports/2026-11-01-terminal-transition0135-independent-review.md)，315真终态，完整232/221/victory通知及构造226 | 平地有限运动/默认英文标签；phase5胜利组件不等于observer中phase4死亡或完整终局存档。 |
| 真实地形高度 | [107完整ADT/18413原件调用](reports/2026-11-01-terrain0135.md)及[独审](reports/2026-11-01-terrain0135-independent-review.md)，27392MCNK/3971840顶点，0差异 | 该批只验145XYZ+洞/三角采样；后继资产链已接默认Elwynn查询world，264B其余字段、物理所有权/其它地图/渲染仍未知。 |
| 真实Boss矩形120B | [390组/2883快照](reports/2026-11-01-effect-geometry0135.md)及[独审](reports/2026-11-01-effect-geometry0135-independent-review.md)，真2785→910→915，277正常+113SELF拒绝前缀 | 三raw9/type0/shape2、4B scratch未知；正常命中完整尾部独立模型仍缺，旧prefix不倒改。 |
| 浏览器真实DBC资源 | [3fresh实例/15已恢复投影](reports/2026-11-01-browser-resources0135.md)，原SELF/XHR解析Spell/SpellIcon并正常返回；含2组cold915加载 | 单独embedding17允许/861拒绝、128MiB；原件执行成功≠完整新独立模型。旧批不还原history；后继history组件另列，来源容器/keyed/proc完整尾部仍缺。[原资源批独审通过](reports/2026-11-01-browser-resources0135-independent-review.md)。 |
| 受伤48B history组件 | [完整1073的164组/924入口](reports/2026-11-01-incoming-history0135.md)及[独审](reports/2026-11-01-incoming-history0135-independent-review.md)，声明字段0差异；环形裁剪/扩容/UTF8切片/旧padding严格 | sourceGUID0/无单位/spell0英语fallback，空proc，非致死或minimum-one；来源匹配/heal生产/完整1073仍缺。 |
| 真实DBC与history组合 | [9fresh/37次完整1073](reports/2026-11-01-browser-history0135.md)及[独审](reports/2026-11-01-browser-history0135-independent-review.md)，冷加载真实Spell/SpellIcon、完整name/icon与环形history声明字段0差异 | sourceGUID0/category1/2/三Spell、17允许861拒绝/128MiB。完整来源容器/keyed/proc未知，未接headless。 |
| world高度／nearest查询消费者 | [959输入/1858完整调用](reports/2026-11-01-world-query0135.md)及[联合独审](reports/2026-11-01-world-consumers0135-independent-review.md)，899真实高度点与60受控nearest，0差异 | snapshot已解析world输入；79本地nav replay新增原件调用0。world producer与其它地图未由此恢复。 |
| 真实world位置消费者 | [新96输入/96完整8751／13516调用](reports/2026-11-01-world-position0135.md)及[联合独审](reports/2026-11-01-world-consumers0135-independent-review.md)，30源闭包、XYZ/RNG与G不变域通过 | 58真实world／38受控几何，最近格只取Z、完整回退与nav原字节。旧21源批保留，新旧96不相加；未接旧主切片。 |
| M2碰撞／变换／候选与导航producer | [最终100905的114组/1477调用](reports/2026-11-01-world-raster0135.md)及[独审](reports/2026-11-01-world-raster0135-independent-review.md)，实际31M2、完整18572／12375／9328，0差异 | 该组件ground／placement为声明输入；后继placement/cache链补默认Elwynn查询world，未恢复其它地图、物理所有权、动画／材质／渲染。 |
| WMO碰撞producer | [425输入/830完整1510／4464调用](reports/2026-11-01-wmo-geometry0135.md)，实际readset全部410文件＝23root＋387group，0差异；[独审通过](reports/2026-11-01-wmo-geometry0135-independent-review.md) | 只验碰撞投影／flags过滤／u32输出索引；不是完整160B解析对象、9513/VFS组装、全部WMO或渲染／动画。 |
| ADT placement | [13组/13完整1446](reports/2026-11-01-world-placements0135.md)及[独审](reports/2026-11-01-world-placements0135-independent-review.md)：9实际/4受控，两组44B名字与scalar逐字一致 | navM2/navWMO/secondaryWMO筛选是另列静态规则；不是全6730/VFS原件差分。 |
| 默认Elwynn cache生产 | [独立ground/nav/secondary](reports/2026-11-01-world-cache0135.md)与[cache静态独审](reports/2026-11-01-world-cache0135-independent-review.md)；14本地契约，0新原件case | ground78400格；墙3150→四邻可达性5404blocked，1224候选→460finite；仅nonflat/no-primary路径。 |
| 451资产→查询world→开局 | [37源完整组合](reports/2026-11-01-asset-world0135.md)及[整体独审](reports/2026-11-01-asset-world0135-independent-review.md)：terrain4022968B/nav78400B/secondary1254400B，开局known2118B/78包8410B/start/RNG等，0差异 | 1历史原件case，0新增原件调用/案例/bootstrap/主切片帧；生产不读snapshot。物理App/Rc/VFS、其它地图模式、1370B未写/未用记录、接旧主切片仍缺。 |
| 开局1744／1821组件 | [27组/116完整入口与独审](reports/2026-11-01-opening-entities0135-independent-review.md)，附属88B、actor角度／GUID／169、旧padding严格 | 实验自身不包含完整1089；内联windows／special／boundary由下行整条开局差分验证，不倒记116调用。 |
| 独立默认开局 | [16组/32完整6730缓存构造→1089](reports/2026-11-01-opening0135.md)，39源、六vector、1248新增包／16start，0差异；[独审通过](reports/2026-11-01-opening0135-independent-review.md) | 已解析Elwynn world是输入；每局2附属／4NPC／2kind2／4special／2或3窗口／69边界、counter10→87。未接旧主切片，未覆盖完整物理Game／菜单profile／其它maps/modes／非空装备天赋。 |
| 原件真实world与1089观察 | [1例2902→6959→6730→1089](reports/2026-11-01-entry-world0135-probe.md)及[独审](reports/2026-11-01-entry-world0135-probe-independent-review.md)：同非平地Rc，phase0→1、4NPC/2kind2；453MPQ/561GET全部200、4memory319029248B | 历史原件观察、独立模型case0；后继开局单列，未倒改该批。24允许854拒绝/256MiB；后继独立组合不新增该原件bootstrap或主切片帧。 |
| 14stage原件观测 | [080624](evidence/full0135-oracle-20261101T080624.993012Z/main-tail135-probe-receipt.json)：3038帧/42550快照/18选择/42558调用，6预算、seed3=353/seed5=285进入phase4 | [观测独审通过](reports/2026-11-01-main-tail0135-probe-independent-review.md)，0新增独立帧；2521个execution11快照不计模型支持，与其他层不相加。 |
| transport六方法 | [43组/220完整原件调用](reports/2026-11-01-transport0135.md)及[独审](reports/2026-11-01-transport0135-independent-review.md)，10源、quiet域、实际宿主0 | ring/vector/88B深clone已恢复；日志/时钟分支、完整Rc owner、receive→ECS及真实联网未知，不等于完整App。 |
| 空history与真实地址熵 | [24组/96入口](reports/2026-11-01-app-history0135.md)及[独审](reports/2026-11-01-app-history0135-independent-review.md)，完整240B头/析构、entropy已知408B | 另384B地址词opaque；四map128B使用显式seed的typed-state静态规则，非完整4253差分。 |
| App5168静态构造投影 | [32组静态重组/10源](reports/2026-11-01-app-state0135.md)及[独审](reports/2026-11-01-app-state0135-independent-review.md)，0新WASM调用，730已知/4438None；显式live-copy后1182/3986 | 不是完整合法App；旧7源依赖遗漏与补正历史保留，32组只动态覆盖4936 select条件0。 |
| 真实cast部分投影 | [730B对照](reports/2026-11-01-app-state0135-capture.md)及[独审](reports/2026-11-01-app-state0135-capture-independent-review.md)，33B明确输入→697B独立预测，4438None，0差异 | 复用首SwiftShader原观察，0新原件调用/案例；8idle与GPU panic不算投影验收，不推断全部App/owner合法性。 |
| 自然原App/Metal观察 | [官方构造、中文角色选择页及8次完整idle880返回](reports/2026-11-01-full-app0135-probe.md)（[观察独审通过](reports/2026-11-01-full-app0135-independent-review.md)），999HTTP均200、0 page error | 原件观察，Game tag2未开局、0独立gameplay帧。CSP拦presence外发；早期SwiftShader真实GPU失败、首Metal研究observer达1M事件上限throw及字体404均保留，独立App/full880仍未恢复。 |
| 自然UI→运行态Game | [603完整返回/8running/7clock推进](reports/2026-11-01-game-entry0135-probe.md)与[独审](reports/2026-11-01-game-entry0135-independent-review.md)：真实点击/W、2418素材、0page error、1,378,877,440B coherent memory；实际7units/2pickups | 原件观察、0独立case/主切片帧。首running已是1089后续状态；Start命令tag仍未定位。独立输入/所有权/容量交接、cleave exec5和完整一局仍缺。 |
| 资源生产135 | [64例完整1417/947组件与独审](reports/2026-11-02-resource-spawn0135-independent-review.md)；G2444已接下行500，物理56B/+4/共享RNG/counter/169严格对照 | 资源3..5近身消费者、自然85秒再生/cap2连续域未验；组件与组合计数不相加。 |
| 真实开局资源战斗500 | [1case/500frames/4select/7004stage/7006入口0差异与独审](reports/2026-11-02-opening-resource-combat0135-independent-review.md)，99源/86production；raw451另跑500并经44项终态衔接 | 原件snapshot/外调度与独立预解析world明确；纯模型600/5不是差分，60秒G2424/G2448仍待接，非全880/native/一局。 |
| 完整游戏 | 尚无独立完整一局验收；0.134.0局部组合另列 | 新版刷怪、施法、拾取、选卡应用、存档、UI和联机继续连接与验证。 |

基础资源属于另一层证据：[MPQ读取器/索引](reports/2026-11-01-resource-index-base.md)已对29602个命名块、1636167198B完成固定StormLib逐字节对照，154份DBC容器可独立读取。基础RAR包内程序仍是0.102.3，不能自动认定为0.135.1完整资产。上表后继451资源链已独立产生默认Elwynn查询world并与历史输出逐字相符；完整物理App/Once/Rc/VFS所有权、其它地图模式、最新全部资产等价、动画／材质／音画及渲染仍未完成。

[真实进场资源静态规格](reports/2026-11-01-entry-resources0135-static.md)及[独审](reports/2026-11-01-entry-resources0135-static-review.md)另核39函数、2DBC/7WDT/107ADT共116份170383346B，以及12区首层路径/开局调用契约。18条模型候选未配但未证明属于实际必需读取；该静态批不算原件运行。后继真实world/1089观察已完成一个实际read-set，未把116库存或453读入文件计为独立玩法差分。

## 当前切片之外的明确边界

- **独立真实进场**：默认开局16组/32入口及后继451资源→Elwynn查询world→开局的1历史case分别保留。查询world生产不读原memory；完整App/Once/Rc/VFS所有权、菜单/profile、其它地图模式、非空装备天赋、自然输入生产／完整880仍缺；后继移动38／full33和moving460各自另验。[880上下文静态记录](evidence/full880-context0135-static-20261101T111231.254023Z/notes.md)保留历史边界；后继transport六方法和部分App投影已验，完整独立App/owner/调度仍缺。自然原App的8idle历史观察保持；后继真实菜单/移动已取得8running880，单独记录为原件观察。旧独立切片仍使用显式phase1，未因此获得自然开局能力。
- **研究输入与内存**：phase1及128个初始zeroed424B/88B槽仍显式。[当前独审](reports/2026-11-01-headless-tail0135-independent-review.md)复原1226927104B单位与254645248B范围backing；52次单位复用保留416非零字节，area19B复用全0，非平凡压缩/allocator padding恒定未证明。
- **对象键与物理输出**：headless严格比较numeric player keys22/28/34/716/717/1109/1176，其余原件keyed状态全部另存为unmodeled，不能归为纯显示。1202 aura/外观键、1453治疗/account输出、完整消息字节/交付与所有producer仍分别待还原。
- **全部游戏流程**：14个真实尾阶段只在限定域接入；活跃916/975 execution11/2602/2573/2376、915其余类型、前段/party/完整880、其它地图及物理world所有权、开局接主切片、全部技能/AI/存档/UI/联机与独立完整一局仍未验收。真胜利终态、history、默认开局与world原件观察分层记录，均不等于完整游戏。
- **915当前边界**：主切片仍只接idle域；500delayed56和390Boss矩形分别有独审，非空56/120/ordinary910未接自然headless。浏览器3组正常命中保留完整rawG/backing；history后继164/924与9/37组件另验，完整来源容器/key22/28/proc仍未知；旧probe和072329保持历史身份。

## 固定0.134.0研究基线的覆盖状态

| 范围 | 当前证据 | 下一步 |
|---|---|---|
| 官方原件 | 固定0.134.0 Windows更新EXE通过官方大小/SHA；同版Web完成身份提取和[完整WAT/独立索引](reports/2026-11-01-wasm0134-profile.md)；用户原有4T RAR经[CRC/提取哈希验收](reports/2026-11-01-resource-acquisition.md)，8文件含7个MPQ可用 | 包内旧0.102.3 EXE与更新程序分别建档；0.135.1语义迁移、实际资源加载和消费者关联仍pending，基础MPQ索引/读取另已验证。 |
| 原生同源核对 | 本版PE重新定位五表、两原生函数；五路升级结构与历史规格相符 | 继续在当前原生消费者中核对行为；Web结果不冒称原生执行结果。 |
| 目录与差异 | [114能力、9职业的新表](reports/2026-11-01-catalogue0134.md)；新增stormstrike/rockbiter、移除call_of_flame，stoneform参数变化 | 新定义/职业kit不等于所有技能、天赋行为已实现。 |
| 升级数值 | [新原25368的11560例对照，0差异](reports/2026-11-01-upgrade0134-spec.md)，现有独立数值模型可复用 | 四个逐字节匹配的其他helper尚待新版上下文与执行验收。 |
| 选卡与施法状态链 | [16完整新函数、29条guard](reports/2026-11-01-selection0134-chain.md)；[完整新1073的779例](reports/2026-11-01-selection0134-spec.md)，及[新能力初始化2781例](reports/2026-11-01-new-ability0134-spec.md)，均0差异 | 新初始化覆盖114定义×tier0..4、额外tier5 helper表项及显式modifier快照；未知producer拒绝。共享后处理、属性刷新与完整选择控制仍待接入；两份语料不合并计覆盖。 |
| kind0候选生成 | [完整原2159与独立metadata模型4126例，0差异](reports/2026-11-01-candidates0134-spec.md)；103个职业kit新能力ID、114个owned升级ID实际出现，四字RNG及3控制字段一致 | 仅metadata域；XP消费者到候选在下面level_cycle中另验，展示payload、world/通知、kind1/2、实际reroll及拾取自然调度仍pending。 |
| 敌人扣血 | [424B单位、36B新加区与55条guard](reports/2026-11-01-combat0134-chain.md)；[独立combat134与完整新914的454例，0差异](reports/2026-11-01-combat0134-spec.md) | 缺完整触发/掉落/死亡RNG；玩家incoming1063与IceBarrier另行恢复。 |
| 经验与成长 | [12完整函数/28条guard](reports/2026-11-01-progression0134-chain.md)，确认120级上限；[独立progression134与完整新4630的2197例，0差异](reports/2026-11-01-progression0134-spec.md) | phase3这份报告只验level/XP/pending/phase；每级属性/治疗/2159投影现另作level_cycle组合，完整地图拾取/消息/自然调度仍缺。 |
| 玩家受伤/护盾 | [9完整函数/33段guard与barrier CFG](reports/2026-11-01-incoming0134-chain.md)；[完整新1063的139例非致死字段对照，0差异](reports/2026-11-01-incoming0134-spec.md) | 独立模型仍是显式pending的前缀；盾耗尽、复活/死亡、反击/事件、完整IceBarrier施法未执行验收。 |
| 死亡与经验拾取 | [25完整函数/31条guard/15窗口](reports/2026-11-01-death-xp0134-chain.md)；[最新拾取382例、普通死亡组合367例×4阶段，均0差异](reports/2026-11-01-ordinary-pipeline0134.md) | flag0普通单目标/空辅助状态/已解析平地placement；金币消费者RNG已组合验证。可收取外来kind、地图/完整调度、候选及属性刷新仍有明确pending。 |
| 金币收取 | [完整原2862与独立currency134的1030例，0差异](reports/2026-11-01-currency0134-spec.md)；含578次warmup共1608入口调用，比较局内金币/累计、key1176、队列、记录和despawn | 空claim/aux、规范marker域；账号转移/持久化、wire/网络交付、混合XP/金币自然调度与深树均未验收。 |
| 属性重算 | [完整原1513与新独立模型10569例，0差异](reports/2026-11-01-stats0134-spec.md)；22派生字段、HP/4辅助池/3对象字段/速度与队列已对照 | 数值输入来源、已有树项更新/包字节/整场调度未验收；每级刷新在独立level_cycle组合另验，未接普通拾取控制器。 |
| XP消费者组合 | [完整原4630的1151状态序列/3450入口调用](reports/2026-11-01-level-cycle0134.md)，逐级属性→20%治疗/半减→下一阈值→kind0候选，0差异；只读复核通过 | 强制显式来源快照；未接拾取/金币/选卡应用控制器，物理队列/消息/world和0.135.1迁移仍pending。 |
| 其他独立模型 | 下表所列模型有0.126.0依据；未自动计入0.134.0完成度，逐项范围见[版本支持清单](reconstruction/version-support.json) | 刷怪、施法基数/暴击、存档、UI与协议继续迁移和连接。 |
| 完整游戏 | 尚无新版或旧版的独立完整一局验收 | 按状态→生成→施法→伤害/死亡→经验→选卡拼出闭环。 |

## 历史已验证覆盖（0.126.0）

下表不以已分析函数占比估算完成百分比。完整WASM已解码属于结构覆盖；只有补齐对应规则、独立实现和结果对照，才算达到可重造的层级。

| 模块 | 当前有依据的内容 | 独立实现/验证 | 尚需补齐 |
|---|---|---|---|
| 原件与版本身份 | 完整WASM/原JS哈希、完整WAT、函数范围、直接/尾调用与内存指令索引 | 可复现索引与REA Evidence提取 | 持续维护版本差异；旧Windows地址不能混用。 |
| 开局、主循环和状态机 | 计时夹取、阶段0..5、单人暂停/选卡、多人全局/个人状态切换及有条件调用顺序 | [19个完整函数、25条guard、11处分支对应](reports/2026-11-01-game-loop.md) | 输入采样、全部命令/迁移、初始构造、完整调度与运行时序。 |
| 职业和能力定义 | 9职业、113能力的静态表；103个职业kit唯一ID及10个额外定义 | [原始内存重建和字段消费者](reports/2026-11-01-abilities.md) | 所有字段、解锁条件、职业特殊被动；声明表不等于全部技能行为。 |
| 技能升级 | 五种数值算法、分档表、真实选卡→拥有技能向量→施法读取链；80B记录独立应用 | [数值11560组](reports/2026-11-01-executable-spec.md)；[升级片段2345卡+1初始化、完整1065五例](reports/2026-11-01-card-apply.md) | 新版等价验证；候选生成、权重、刷新、非零新技能tier及全部升级副作用。 |
| 自动施法、目标与命中 | 圆形命中链；113能力→12执行kind/14效果tag；Fireball→按距离预定到期→1819→933 | [能力](reports/2026-11-01-abilities.md)、[12类分派与延迟命中](reports/2026-11-01-cast-dispatch.md)；[半径helper与组合29041组对照，0差异](reports/2026-11-01-radius-spec.md) | 逐类完整规则、碰撞/弹道显示、等距离排序、触发顺序；未执行原934。 |
| 伤害、治疗与防护 | 命中基数/暴击、条件加区、HP扣减/统计/死亡主字段的独立投影；玩家受伤静态主干 | [9153原片段及32例完整原933对照](reports/2026-11-01-combat-spec.md) | 新版等价验证；DoT、治疗/吸血/反伤、完整死亡loot/RNG推进、宠物与触发闭包。 |
| 属性、增益和装备 | 9职业/8种族、四套tag、限时/32B效果支配、22派生字段、当前HP/移动更新独立模型 | [完整原1573及原callee8495例对照](reports/2026-11-01-stats-spec.md) | 新版数据/字段迁移；全部modifier产生方、装备词条/天赋ID、调度及外部消息交付。 |
| 地图、敌人和波次 | 12区域、148条普通/精英定义（108/40）、60条Boss时间表；持续刷怪预算/权重/上限、Boss调度及生成数值主干 | [静态规则及两个成长函数24636组原件对照，0差异](reports/2026-11-01-world-progression.md) | 完整位置算法、精英/特殊波次、阶段AI、区域事件；幂/衰减/RNG辅助函数仍待独立恢复。 |
| 拾取、经验和成长 | 死亡→kind0拾取→XP/等级/pending；阈值、绕回、99级及开卡guard | [原helper及重组](reports/2026-11-01-progression.md)；另完整原3231暂停域1954份四字段对照 | 新版等价验证；完整拾取/掉落、胜利奖励、持久解锁及2098候选生成。 |
| 随机状态和采样 | 32475的4word递推、高23位区间浮点采样、上端点拒绝重抽与错误时序 | [18144份原体对照，返回与状态0差异](reports/2026-11-01-rng.md) | seed/熵初始化、其他整数/高24位采样及全系统随机调用顺序。 |
| 单位移动和空间查询 | 圆形查询、插值位置、单位状态筛选已定位部分实现 | 局部静态证据 | 导航、障碍、地形高度、碰撞、路径缓存和跨端平滑。 |
| 对象消息到ECS | 解码→SessionEvent→同一通道→注册键→已注册系统→按GUID写Fields | 47指令guard、5结构分支、原件vtable/元素表对应 | 全部消息分支与运行时序/显示验收。 |
| 合作传输和协议 | WebSocket/中继/peer确认层；一条HP结果静态闭合 | 8/11中继、19/25应用变体离线codec；37字面样本 | 其他变体、完整权限、重连/重排/重复、版本协商和新核心互操作。 |
| 存档和账号进度 | 368B账号结构、24正常tag/旧unlock别名、角色与未知行；一条地图解锁→RSE1→存储→读回链 | [33个完整函数、43条guard；仅合成模型自检](reports/2026-11-01-save-schema.md) | 全部字段含义/解析限制、迁移/备份、导入导出及原件差分；尚无独立完整存档模型。 |
| UI、输入、中文和插件 | 现有封装补丁；两块内嵌Lua、50命名函数、22消息前缀 | 原件模板提取和局部接口还原 | 全部UI脚本/事件、键鼠/触控、菜单、提示、中文内容来源与独立UI。 |
| 模型、地图和音画资源 | M2/BLP/WMO及DBC入口；基础MPQ命名块索引/独立读取与154份DBC容器已另验 | 尚无独立完整资源管线，格式验证不等于新版全部资产已验 | 实际加载、列/ID关联、动画/特效/材质/声音与渲染。 |
| 可玩流程与跨平台 | 现有App仍使用原核心；研究代码独立保存 | 尚未形成替代核心 | 独立完成一局、覆盖职业/地图/进度，并验收Mac/Android/Windows对应行为。 |

模块继续细分，已确认表项数只表示该张表的数据覆盖，不表示同数量技能/敌人的全部行为已经恢复。新结论写入专门报告，保留原始版本、字节范围、Evidence和未覆盖分支。

## 从规则到重造的验收层级

1. **定位**：有原件版本、确切函数/数据范围和消费者，不能仅靠UI文案或名称猜测。
2. **规格**：明确输入、输出、状态字段、数值位宽、舍入顺序、随机源、分支和副作用。
3. **独立实现**：生产逻辑不调用原版WASM；原件只用于提取、研究和对照。
4. **差分验证**：有独立输入和原件结果，逐项比较。隔离函数验证只覆盖该函数，不能代表完整对局已通过。
5. **流程验收**：固定输入/种子完成相应流程，核对事件顺序、存档往返和跨端结果。

原件函数微模块的执行与静态分析分开记录。微模块必须验证复制体身份、无宿主导入、无应用入口，并明确替代的panic/分配等依赖；不能把手写模型与自身往返当成原版验证。

## 当前独立实现

**0.135.1历史平地主切片**为[14阶段独立切片](reports/2026-11-01-headless-tail0135.md)：8seed/1614帧/22607阶段/11选择/22615原件调用，67源含60core、16角色，0差异。旧072329/064308/061901冻结为历史；新默认开局16/32、placement13/13、451资源历史组合及其它组件/观测分别记录，不相加。该旧批独立组合新增bootstrap0、主切片帧0；后继真实开局连续500另列于本文开头，自然原App观察另列，不当作独立实现。其它地图/完整物理world所有权、开局接主切片、活跃队列／全部技能AI／full880／存档UI网络和独立完整一局仍缺。详见[版本支持清单](reconstruction/version-support.json)。

`core_spec.binary32`用精确有理数计算和逐步binary32舍入。**0.134.0已验证范围**包括升级值、有序拥有记录、伤害/受伤投影、经验与拾取、限定普通死亡组合、属性数值、kind0候选metadata、金币收取和新能力初始化；各自例数、输入域和未实现项见上表与[版本支持清单](reconstruction/version-support.json)，不同层级的计数不合并为完整游戏覆盖。完整原模块对照保留内部callee；未调用应用start，所有878宿主导入拒绝且实际调用0次。另有`level_cycle134`把XP消费者、每级属性/治疗与kind0候选接成限定组合，但仍未接普通死亡/混合拾取、金币、选卡应用或自然主循环。

以下是**0.126.0历史规格与对照**，不能把其次数转记为新版结果：

| 规格 | 对照范围 | 数量/结果 |
|---|---|---|
| `upgrade_values` | 原25242完整620B函数体与五组表，其余函数trap占位 | 11550份有效位模式一致，10份非法档位同类trap。 |
| `enemy_scaling` | 原95640/95641各46B纯函数体 | 24636份，0差异；其中2983份只比较NaN类别。 |
| `radius` | 原35684完整364B helper，以及JS/f32重组的934外层 | helper24514份、外层4527份，0差异；未执行原934，NaN只比较类别。 |
| `progression` | 原85387完整68B舍入helper；阈值/XP/开卡guard重组 | helper24643份、重组5482份，0差异；未执行原3231，仍缺属性/通知等副作用。 |
| `rng` | 原32475完整399B区间采样器；保留索引和panic trap占位 | 18144份返回与4word状态一致，含7075份替代panic trap；seed初始化未执行。 |
| `derived_stats` | 原1573完整函数及真实原分配器/BTree/队列callee | 8495份，0字段差异、0宿主调用；modifier实际生产方尚缺。 |
| `ability_state` | 原1065连续原片段和完整原1065有限样例 | 2345卡+1初始化片段、5份完整调用通过；生产后处理仍显式pending。 |
| `combat` | 原933/934连续片段及完整原933有限样例 | 9153片段、32份完整933核心字段一致；完整死亡loot/RNG仍未实现。 |

```sh
# 纯独立研究运行，不读取原件；去掉显式开关会停在pending_real_phase_entry。
python3 reverse-engineering/reconstruction/run_headless135.py --seed 1 --frames 400 --research-resolved-entry

# 固定目标0.135.1，独立产生新版原件结果。
python3 reverse-engineering/scripts/wasm135_profile.py --deadline-seconds 900
python3 reverse-engineering/scripts/check_stats135_full_spec.py
python3 reverse-engineering/scripts/check_loop135_spec.py --phase full
python3 reverse-engineering/scripts/check_candidates135_full_spec.py --phase full
python3 reverse-engineering/scripts/check_new_ability135_full_spec.py --phase pilot
python3 reverse-engineering/scripts/check_selection135_full_spec.py --phase full
python3 reverse-engineering/scripts/check_level_cycle135.py --phase full
python3 reverse-engineering/scripts/check_selection_cycle135.py --phase full
python3 reverse-engineering/scripts/check_spawn135_spec.py --phase full
python3 reverse-engineering/scripts/check_spawn_frame135.py --phase full
python3 reverse-engineering/scripts/check_cast135_full_spec.py --phase full
python3 reverse-engineering/scripts/check_spawn_motion135.py --phase full
python3 reverse-engineering/scripts/check_spawn_boss135.py --phase full
python3 reverse-engineering/scripts/check_spawn_elite135.py --phase full
python3 reverse-engineering/scripts/check_incoming135_spec.py --phase full
python3 reverse-engineering/scripts/check_ai135_spec.py --phase full
python3 reverse-engineering/scripts/check_death_pickup135.py --phase full
python3 reverse-engineering/scripts/check_owned_cast135.py --phase full
python3 reverse-engineering/scripts/check_initial135.py --phase full
python3 reverse-engineering/scripts/check_ordinary_placement135.py --phase full
python3 reverse-engineering/scripts/check_racial_cast135.py --phase full
python3 reverse-engineering/scripts/check_proc135.py --phase full
python3 reverse-engineering/scripts/check_ai_motion135.py --phase full
python3 reverse-engineering/scripts/check_player_update135.py --phase full
python3 reverse-engineering/scripts/check_movement_pause135.py --phase full
python3 reverse-engineering/scripts/check_headless135.py --phase full

# 独立world组件与显式world输入上的开局，均不新增headless帧。
python3 reverse-engineering/scripts/check_world_query135.py --phase full
python3 reverse-engineering/scripts/check_world_position135.py --phase full
python3 reverse-engineering/scripts/check_world_raster135.py --phase full
python3 reverse-engineering/scripts/check_wmo_geometry135.py --phase full
python3 reverse-engineering/scripts/check_opening_entities135.py --phase full
python3 reverse-engineering/scripts/check_opening135.py --phase full

# 固定研究基线0.134.0；需要对应原件及本机证据输入，不能转计0.135.1。
python3 reverse-engineering/scripts/check_upgrade134_spec.py
python3 reverse-engineering/scripts/check_selection134_full_spec.py
python3 reverse-engineering/scripts/check_combat134_full_spec.py
python3 reverse-engineering/scripts/check_progression134_full_spec.py
python3 reverse-engineering/scripts/check_incoming134_nonfatal_spec.py
python3 reverse-engineering/scripts/check_pickups134_full_spec.py
python3 reverse-engineering/scripts/check_ordinary_pipeline134.py
python3 reverse-engineering/scripts/check_stats134_full_spec.py
python3 reverse-engineering/scripts/check_level_cycle134.py --phase full
python3 reverse-engineering/scripts/check_candidates134_full_spec.py
python3 reverse-engineering/scripts/check_currency134_full_spec.py
# 先pilot获取full_module_directory，再按报告运行full。
python3 reverse-engineering/scripts/check_new_ability134_full_spec.py --phase pilot

# 历史0.126.0，保留回归入口。
python3 reverse-engineering/scripts/check_upgrade_spec.py
python3 reverse-engineering/scripts/check_enemy_scaling.py
python3 reverse-engineering/scripts/check_radius_spec.py
python3 reverse-engineering/scripts/check_progression_spec.py
python3 reverse-engineering/scripts/check_rng_spec.py
python3 reverse-engineering/scripts/check_full_progression_spec.py
python3 reverse-engineering/scripts/check_ability_state.py
python3 reverse-engineering/scripts/check_full_card_apply.py
python3 reverse-engineering/scripts/check_combat_spec.py
python3 reverse-engineering/scripts/check_combat_full_spec.py
```

上述不同验证层分开记录：无宿主导入的微模块、承载原连续片段的合成wrapper、仅新增导出的完整原模块。完整模块所有878个宿主导入均拒绝调用，应用start未调用，真实内部callee按所述fixture运行。这些旧函数实验没有启动完整游戏或访问网络/存档；后继自然原App浏览器观察是另域，有真实presence联网尝试被CSP阻止。0.126.0实验次数不转记0.134.0验收。有限输入的一致不等于穷举证明，NaN不承诺载荷一致，替代panic的范围各自列明。

已解析world的连续受控投影已推进到750帧，挫志怒吼及到期链由新原件采集和独审证明；历史raw资产入口650帧保持原范围。后继完整live／Aura／origin接线另批验证，不把组件通过直接当作自然移动拾取通过。后继moving460已验证受控完整968→位置→真实kind5近身消费，保留自然输入／校正ACK连续接线边界；下一实际阻断是纯模型920之后的致死受伤、死亡／复活和失败recap，后续Boss／终局仍需原件验证；完整world/App／880所有权、全部来源／技能／AI、存档／UI／渲染／音频／联机和138迁移仍未完成。在完整一局及关键行为均有依据前不宣布重造完成。
