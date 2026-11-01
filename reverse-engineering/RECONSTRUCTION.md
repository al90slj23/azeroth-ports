# 独立重造的工作基线

目标是逐项拆清原作逻辑和数据，形成能够独立运行的游戏核心。按用户最新方向，**功能对齐持续跟随官方最新稳定版，每轮固定版本与SHA；本轮验证采用已取得的0.135.1**；0.135.1 / Web`0898d5e3`已经完成完整静态profile、函数/布局映射和局部原件差分；**0.134.0 / Web983346a7**保留已有规则/组合验证，Windows官方SHA各自固定。两版结果分开记录，既有0.134.0验证不会自动转记新版。此前0.126.0 / 3e72472a作为历史验证与复用参考保留，不再作为继续扩展的主目标。完整原件身份见[targets.json](targets.json)，迁移原则见[版本策略](VERSION_STRATEGY.md)。工具安装、原始游戏、WAT和原件函数测试模块均保存在本机忽略区；独立实现放在[reconstruction/](reconstruction/README.md)。

这里的“完成”需要覆盖行为、状态变化和结果，而不是只有函数地址、解码文本或一份大关系图。原作Rust变量名和源文件原文没有恢复；重造不以逐字找回这些标识符为验收条件。

## 固定0.135.1目标的迁移与验收

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
| 完整游戏 | 尚无独立完整一局验收；0.134.0局部组合另列 | 新版刷怪、施法、拾取、选卡应用、存档、UI和联机继续连接与验证。 |

基础资源属于另一层证据：[MPQ读取器/索引](reports/2026-11-01-resource-index-base.md)已对29602个命名块、1636167198B完成固定StormLib逐字节对照，154份DBC容器可独立读取。基础RAR包内程序仍是0.102.3，不能自动认定为0.135.1完整资产。上表后继451资源链已独立产生默认Elwynn查询world并与历史输出逐字相符；完整物理App/Once/Rc/VFS所有权、其它地图模式、最新全部资产等价、动画／材质／音画及渲染仍未完成。

[真实进场资源静态规格](reports/2026-11-01-entry-resources0135-static.md)及[独审](reports/2026-11-01-entry-resources0135-static-review.md)另核39函数、2DBC/7WDT/107ADT共116份170383346B，以及12区首层路径/开局调用契约。18条模型候选未配但未证明属于实际必需读取；该静态批不算原件运行。后继真实world/1089观察已完成一个实际read-set，未把116库存或453读入文件计为独立玩法差分。

## 当前切片之外的明确边界

- **独立真实进场**：默认开局16组/32入口及后继451资源→Elwynn查询world→开局的1历史case分别保留。查询world生产不读原memory；完整App/Once/Rc/VFS所有权、菜单/profile、其它地图模式、非空装备天赋、移动2328/full880及接旧主切片仍缺。[880上下文静态记录](evidence/full880-context0135-static-20261101T111231.254023Z/notes.md)保留历史边界；后继transport六方法和部分App投影已验，完整独立App/owner/调度仍缺。自然原App的8idle历史观察保持；后继真实菜单/移动已取得8running880，单独记录为原件观察。旧独立切片仍使用显式phase1，未因此获得自然开局能力。
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

**0.135.1当前主切片**仍为[14阶段独立切片](reports/2026-11-01-headless-tail0135.md)：8seed/1614帧/22607阶段/11选择/22615原件调用，67源含60core、16角色，0差异。旧072329/064308/061901冻结为历史；新默认开局16/32、placement13/13、451资源历史组合及其它组件/观测分别记录，不相加。独立组合新增bootstrap0、主切片帧0；自然原App观察另列，不当作独立实现。其它地图/完整物理world所有权、开局接主切片、活跃队列／全部技能AI／full880／存档UI网络和独立完整一局仍缺。详见[版本支持清单](reconstruction/version-support.json)。

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

当前独立切片连接14个单状态尾入口的已恢复/实际守卫域，保留6未知技能与2预算边界。后续补齐world资源实例／placement／合并缓存／所有权生产，连接已验默认开局与主切片，继续来源容器/keyed/proc、活跃尾队列／效果及未知技能，再扩终局存档/UI/联机；在完整一局及关键行为均有依据前不宣布重造完成。
