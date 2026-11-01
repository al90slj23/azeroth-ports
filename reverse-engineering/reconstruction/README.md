# 独立核心的可执行规格

本目录保存自己实现的规则代码，目标是逐步组成能独立运行的替代核心。**功能对齐目标固定为0.135.1 / 0898d5e3**，`derived_stats135`已完成新版原件差分；0.134.0 / 983346a7的局部实现与组合保留为固定研究基线，结果按版本与域分别记录，不转记为新版通过。各自确切范围见[版本支持清单](version-support.json)，不能直接视为新版全部行为。当前还不是可玩游戏，现有Mac/Android安装包继续保持原样。

现有纯Python入口运行限定平地切片：真实空profile构造→显式phase1→普通生成/施法/范围/idle915→死亡掉落/成长/自然选卡。当前[072329](../reports/2026-11-01-headless-effects0135.md)对照8seed/1614帧/11309阶段/11选择/11317调用0差异且[独审通过](../reports/2026-11-01-headless-effects0135-independent-review.md)。seed1/6各400帧、seed3到257帧，总6未知技能/2预算边界；旧064308和061901保留不相加，尚非完整880或独立一局。

- `core_spec/binary32.py`：精确有理数运算后按IEEE binary32 nearest-even逐步舍入；NaN载荷不保证保留。
- `core_spec/upgrade_values.py`：五种升级值计算，输入为明确的状态字段/原始浮点位，输出为binary32位。不会读取或执行原游戏。
- `core_spec/enemy_scaling.py`：普通/精英的两条生命成长曲线，保留运算顺序；不包含完整生成公式。
- `core_spec/radius.py`：原35684的log1p家族近似与半径软压缩，逐操作建模；不以语言标准数学函数替代近似。
- `core_spec/progression.py`：85387舍入、等级阈值及XP/pending数值投影；不包含原3231的属性/治疗/消息/选卡副作用。
- `core_spec/progression134.py`：新版85718阈值、120级上限、u32 XP/pending绕回和选卡资格守卫投影；phase3完整原4630的2197例四字段一致。本模块不包含候选/消息/治疗副作用，限定XP消费者组合另见`level_cycle134`。
- `core_spec/rng.py`：四字递推与32475区间采样，含拒绝重抽；固定135的1560 seed初始化另见`initial_state135`，全游戏随机时序尚未恢复。
- `core_spec/derived_stats.py`：22派生属性、当前HP、四套tag及32B实时效果；输出对象字段和移动更新决策，未实现真实modifier生成方。
- `core_spec/ability_state.py`：80B拥有能力、真实升级顺序、新tier0初始化与选卡控制投影；未实现后处理显式pending，未知新tier明确拒绝。
- `core_spec/combat.py`：命中基数/暴击、伤害加区/上限、HP/统计/死亡主字段；完整死亡XP/loot/RNG和触发仍未闭包。
- `core_spec/combat134.py`：新版424B单位状态、M加区/新T36B rawtag50/51/阶段系数、HP/有效伤害/死亡主字段的独立投影；保持`amount*(M+T)*P`的逐步f32顺序。不是完整施法、触发或死亡管线。
- `core_spec/incoming134.py`：新版玩家减伤/盾消费与barrier替换标量规则的前缀；所有未实现回调显式pending。139例非致死空状态的选定最终字段与完整原1063一致，盾耗尽、复活/死亡、完整施法未验收。
- `core_spec/binary32_sqrt.py`：用精确有理数和平方中点比较得到binary32最近偶数平方根，NaN载荷不保证；没有依赖host libm。
- `core_spec/pickups134.py`：56B记录、kind0追加/45闲置合并、模式0空claim的吸取/到期/XP投影；与完整原1417/2862对照345例，0差异。世界placement和消息/实体/其他kind等仍显式pending。
- 当前扩展`pickups134`支持kind1显式GUID/counter追加、真实收取guard外的idle外来记录，以及逐笔XP消费者边界；最新382例完整原件对照0差异，345例是fb74fdb历史基线。
- `core_spec/death_loot134.py`、`pickup_entity134.py`：普通死亡XP/金币的直接抽样，以及kind1消费者的额外随机角度抽样、counter/GUID投影；flagged/kind2和完整实体树/视觉仍pending。
- `core_spec/ordinary_pipeline134.py`：将上述规格接成受控普通单目标死亡→拾取→XP投影，367例×4阶段与原件一致。遇选卡或未恢复属性立即返回pending，升级后dirty状态阻止跨调用复用旧倍率；不是独立完整主循环。
- `core_spec/derived_stats134.py`：新版22派生字段、HP、辅助池、对象字段和速度更新决策；完整原1513的10569例对照0差异。真实modifier来源仍缺；每级刷新已在独立level_cycle组合另验，普通拾取控制器仍待接入，不能用API默认空值代替未知数据。
- `core_spec/candidates134.py`：kind0候选metadata、权重筛选、tier/kinds和四字RNG的独立投影；完整原2159的4126例0差异，103个职业kit新能力ID与114个owned升级ID实际出现。展示payload、kind1/2、实际reroll及XP→候选自然组合未验收。
- `core_spec/currency134.py`：kind1局内金币/累计、key1176和原base amount队列；完整原2862的1030例0差异，共1608入口调用含578warmup，覆盖记录移除/despawn和既有键更新。账号持久化、深树及网络交付/自然混合调度仍pending。
- `core_spec/ability_state134.py`：114定义的新能力80B记录初始化、28B额外字段与tier调整；完整原1073的2781例0差异，覆盖全部114×tier0..4及额外tier5 helper表项。必须显式提供modifier快照，未知producer拒绝；共享后处理、统计/收尾与其他pending队列尚未独立连接。
- `core_spec/level_cycle134.py`：强制显式来源快照，将XP消费、每级属性/升级治疗、下一阈值与kind0候选接成组合。1151状态序列/3450完整原4630入口调用0差异；尚未接拾取/金币/选卡应用控制器，也不算0.135.1验收。
- `core_spec/derived_stats135.py`：复用独立有序算术并显式映射新版字段，新增护甲上限G1572；完整原1512的10569例0差异。23派生词、HP/辅助字段/对象键/速度与移动队列已验，来源producer、已有树项更新、包字节和自然组合仍pending。
- `core_spec/loop135.py`：时钟推进和暂停tag7的独立投影；完整原880/1371的6558例（5400命令＋1158tick）0差异。tick只比较marker/时间和模拟时钟，不宣称其余调度状态一致；空队列/无单位/skip-spawn，fresh终态保存与完整调度仍pending。party聚合/胜利/Endless接口仅静态派生，未运行验收。
- `core_spec/candidates135.py`：本版114定义的kind0 metadata/RNG，完整原2159的4126例0差异；kind1/2、展示与真实producer仍pending。
- `core_spec/ability_state135.py`、`ability_upgrade135.py`：新定义指针/数值下的初始化与有序升级，完整1072分别2781/3629例通过；记录之外共享producer不自动计已恢复，少量历史doc标签在报告中单独映射。
- `core_spec/level_cycle135.py`：严格显式来源，XP逐级属性/20%治疗/阈值/候选，1151序列/3450原件调用0差异；本模块是消费者，死亡/拾取和选卡的限定组合另在`headless135`接入。
- `core_spec/selection_cycle135.py`：kind0 new/upgrade/gold→属性→收尾XP扫取→再生或phase1，660序列/1090完整1072调用通过。只比已独立定义的numeric player keys，其他原件keyed state全部另存为unmodeled，不假定全为cosmetic；kind1/2 metadata、aura/外观和真实producer仍pending。
- `core_spec/spawn135.py`及其独立math/data：12地图/148定义的选怪、衰减和普通/精英424B生成，三个原入口4021例0差异；位置/owner必须显式解析，Boss/特殊调度/terrain另待恢复。
- `core_spec/spawn_schedule135.py`、`spawn_position135.py`及geometry/data：普通947预算/最低密度→实际位置→单位记录的独立组合，1275帧＋305位置共1580例0差异，实际新记录9360。平地、静止/四轴heading、owner0与未来特殊deadlines明确；非轴atan2已由新motion模块另验；grid/pathfinding/fallback和其它事件仍pending。
- `core_spec/cast135.py`、`combat135.py`：25个tag0/execution0/2定义的目标、倍率/暴击、直接或延迟HP和额外84B的916自动冷却，1314序列/3626原入口调用通过；空proc且无致死语料，死亡消费者接口不代表loot已恢复。
- `core_spec/spawn_heading135.py`、`spawn_position_motion135.py`、`spawn_frame_motion135.py`：任意heading5068例通过，含此前1580重放和8个非轴输入；80处NaN仅分类接受，地形/寻路仍缺。
- `core_spec/spawn_boss135.py`、`spawn_boss_schedule135.py`、`spawn_elite135.py`：Boss871例/751次生成、精英549例/340次生成，各自完整原947调度域通过；全Boss AI、其它event/2376/地形仍pending。
- `core_spec/death_pickup135.py`：普通死亡续RNG→XP/coin→逆序混合奖励→逐级属性/候选，204组871阶段通过。原12组非空definitions失败证据不改，后由`proc_events135`在非致死context0域恢复并解释；不能把这项新验证转称致死proc通过。物理实体/包仍缺。
- `core_spec/incoming135.py`、`ai135.py`：有效护甲/受伤2107例、普通124melee的原416组1013步保留。远程/Boss/真实地形/致死复活及未解析反击来源仍拒绝；长期角度扩展见`ai_motion135`。
- `core_spec/owned_cast135.py`、`owned_prelude135.py`、`cast_events135.py`：1076职业近战→已学80B→G1256槽basic隔离fixture→延迟命中与逐有效hit自疗，639组5924阶段通过。旧basic只是测试标签，不能追溯称为真实racial；实际G1256身份由真实构造确认，真实racial及同状态致死/拾取/选卡另由下列模块验收。原916额外84B模型保留。
- `core_spec/initial_state135.py`及data：完整1560空376B selected-profile构造，最终055136严格151组通过；9职业starter/8种族racial/12区域、两个完整80B、HP/属性/RNG、预算/timer/flags和u64身份均验。G1256是racial，learned向量首记录才是class starter；初始CD均为0.5，不用Inf或fireball替换真实racial。返回phase0，上游账号/profile、App初始熵及完整进入仍未知，见[独审](../reports/2026-11-01-initial0135-independent-review.md)。
- `core_spec/ordinary_placement135.py`：pre-hit424B插值死亡XYZ，XP与coin分别做地图clamp/高度，完整1417/914的924组0差异，含移动目标及12地图。必须显式空terrain/grid/navigation，不能读取致死后duration0来猜原位置，见[独审](../reports/2026-11-01-ordinary-placement0135-independent-review.md)。
- `core_spec/racial_cast135.py`：真实G1256对应六个kind9 racial的完整922分支，720组（693成功/27游戏guard拒绝）0声明差异；live32、属性/盾/HP/三份attempt列表/真实80B严格比较。仅新7/8/9的+16未写词未知；war_stomp/escape_artist和1202显示/包仍缺，见[独审](../reports/2026-11-01-racial-cast0135-independent-review.md)。
- `core_spec/proc_events135.py`：kind27/zero16B gate，完整984/8157及非致死914共855组1004阶段，恢复并解释旧12组差异。要求context774显式整数0、nonfatal显式True；其它gate/producer、致死loot后的事件顺序与非空source的1076集成仍拒绝，见[报告](../reports/2026-11-01-proc-events0135.md)。
- `core_spec/ai_trig135.py`、`ai_motion135.py`：trig6726组/13452原函数调用，完整AI429组3423步；三条800帧轨迹角度跨2π，U396不取模/清零。中角上界421657408，超范围1814未知；长轨迹均无接触攻击，不能冒称持续受伤战斗。trig两处NaN按类别接受，AI全部424B严格，见[独审](../reports/2026-11-01-ai-motion0135-independent-review.md)。
- `core_spec/player_update135.py`、`ai_lifecycle135.py`：完整2088/921的285组444阶段0差异，恢复live到期/重算/再生及普通尸体稳定清理；完整live32/NPC424无mask。隔离测试用真实perception但CD=Inf且learned为空，不能当真实开局；periodic/其他来源/11426/物理1453和1202输出仍缺，见[独审](../reports/2026-11-01-gameplay-phase0135-independent-review.md)。
- `core_spec/movement_pause135.py`：35514/25472共享26200的有序移动快照；完整1371共396组1136阶段、604条221消息GUID/seq/stopflag、NPC字节与RNG通过。mode0暂停/恢复不是no-op，每个移动NPC都推进G2412；非空aux112/claim88及完整包几何未恢复，见[独审](../reports/2026-11-01-gameplay-phase0135-independent-review.md)。
- `core_spec/unit_records135.py`、`headless135.py`及`run_headless135.py`的**前阶段061901**：研究组合2088→1754→921→2862→947→1072，唯一HP/RNG归属、逐hit死亡placement、自然XP/选择暂停及恢复接入。8seed/1093帧/5473阶段/8select通过，63源含56份core/init冻结，逐阶段完整128槽无损delta/字节/SHA一致；24次旧槽复用保留192个非零未写字节。详见[独审062623](../reports/2026-11-01-headless0135-independent-review.md)，后继含3757的当前数据见下一项，次数不相加。
- `core_spec/area_effects135.py`：七个922 kind3/3757持续AoE定义，693/5495组件及[独审](../reports/2026-11-01-area-effects0135-independent-review.md)保留；历史064308接3757。当前headless072329以65源/58core/9入口接真实idle915，完整unit/area backing和counter/RNG相续；非空915/全3757仍缺。
- `core_spec/effect_system135.py`：时钟2364、延迟56B的35/36/37及255 pop后trap，500case/2121stage0diff（383正常117预期trap），完整56backing/424B严格。普通910、非空120和真实几何显式待续/拒绝；[组件报告](../reports/2026-11-01-effect-system0135.md)不等于完整915。主切片只接真实观察为空的域。
- `resource_spec/entry_resources135.py`：[进场资源静态契约](../reports/2026-11-01-entry-resources0135-static.md)，39函数、116资产/170383346B和12区首层路径核对；[静态独审](../reports/2026-11-01-entry-resources0135-static-review.md)通过，未执行实际VFS/world/1089，非新增玩法用例。
- `resource_spec/mpq.py`、`dbc.py`：不依赖原游戏或StormLib的MPQ读取与有界WDBC容器实现。基础包29602命名块/1636167198B对照0差异、154份DBC可读取；90例合成格式对照单列。基础资源不自动等于新版全部资产，尚无M2/BLP解释渲染。
- 原件函数对照器在 `../scripts/check_*_spec.py` 和 `../scripts/check_enemy_scaling.py`；生成的WASM、输入及结果仅写入被忽略的 `../evidence/`。

研究切片必须显式提供phase1解析、128个初始全零424B单位槽和128个初始全零88B范围槽；之后保留清理后的尾槽，不重新清空复用。真实1089/2328进入链仍在`SELF → __wenilla_data_base → /data`宿主资源访问处阻断，且还缺4个普通NPC和2个kind2开局对象的实际生产；手工phase1不代表这条链已完成。不宣称覆盖非零死亡时间U4复用；当前4次area过期均末槽删除，复用槽19B未写区全0，非平凡压缩和非零area未写复用也没有本批动态覆盖。真实分配器padding未证明恒定。

对象键未知单列：headless只严格比较numeric player keys22/28/34/716/717/1109/1176，其余完整原件keyed状态另存为unmodeled，不能假定都是cosmetic。1202 aura/外观键、1453治疗/account输出、完整物理包和source获得链仍缺。完整880/915及3757其余分支调度、全部技能/AI、真实地形资源、终局/存档/UI/联网也没有整局验收。

915已观测/接入的域单列：[071318](../reports/2026-11-01-effect-system0135-probe.md)真实插入915并保存三域/消息；[072329](../reports/2026-11-01-headless-effects0135.md)才用新独立模型重新产生预期。clock0、两Vec cap0 ptr8 len0、1644=1、2356=0、416tag0获限定验收；90472个inactive payload/ptr/facing词仅观察，未预测零或新增mask。非空56组件另验但未接headless；120/910、916/975/38007/2602/2573/49037、2376及前段/party/终态仍缺。

当前[独立复制运行](../evidence/headless-effects135-standalone-20261101T072549.178656Z/receipt.json)为59文件（58core+1CLI），无原件/WAT/SQLite/资源/Node/WABT，所有core实际导入均来自复制包。默认停0帧真实进场边界；显式研究输入下seed1/6各400帧、seed3到257帧。这是模型自运行，不新增原件差分。

```sh
# 纯独立运行，不读取原件；显式开关只提供研究phase1，不完成1089。
python3 reverse-engineering/reconstruction/run_headless135.py --seed 1 --frames 400 --research-resolved-entry
# 不给开关时保留真实phase0，并输出pending_real_phase_entry。
python3 reverse-engineering/reconstruction/run_headless135.py --seed 3 --frames 250

# 固定目标0.135.1的重新执行。
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
python3 reverse-engineering/scripts/check_effect_system135.py --phase full
python3 reverse-engineering/scripts/check_headless135.py --phase full

# 固定研究基线0.134.0的实际原件差分，不能转计0.135.1。
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
# 先pilot取得full_module_directory，再按报告运行full。
python3 reverse-engineering/scripts/check_new_ability134_full_spec.py --phase pilot

# 历史0.126.0的隔离数值对照。
python3 reverse-engineering/scripts/check_upgrade_spec.py
python3 reverse-engineering/scripts/check_enemy_scaling.py
python3 reverse-engineering/scripts/check_radius_spec.py
python3 reverse-engineering/scripts/check_progression_spec.py
python3 reverse-engineering/scripts/check_rng_spec.py
```

升级数值、敌人成长、半径等命令执行原件纯数值函数的隔离复制体，不启动完整游戏。这些复制体没有host imports、start、网络、时钟、图形或存档接口。升级模块保留函数索引，仅导出计算函数和固定内存，其他函数为trap；敌人成长模块只有两条无引用函数；半径模块保留单一helper和一页scratch内存。复制体均重解析并核对原体哈希，WABT验证后才交给Node。

固定0.135.1使用`build_full135_oracle.py`/`full135_host.mjs`：41角色逐body/签名guard，含3757/915，仅加export，保留原callee/malloc91941并拒绝878导入。[41角色保守性证明](../evidence/builder135-role41-review-20261101T072424.422022Z/review.json)仅重建旧8-role字节一致，无新增运行用例；角色数量与tick/切片通过均不代表完整一局。

固定0.134.0完整选卡与扣血工具另用`build_full134_oracle.py`：只修改export节，保留所有原内部指令和callee。`full134_host.mjs`复核固定原件、原导出前缀及全部非export节；878宿主导入均拒绝，应用入口不调用。它们确实实例化完整官方模块，但只以原分配器构造的合成状态调用指定内部函数。选卡779例与扣血454例均0差异，宿主实际调用0次；前者生产后处理仍pending，后者未独立实现完整死亡loot/RNG。详见[新版选卡](../reports/2026-11-01-selection0134-spec.md)与[新版扣血](../reports/2026-11-01-combat0134-spec.md)。

历史0.126.0：升级11560组、敌人成长24636组、半径helper/外层组合29041组、经验helper/重组30125组、RNG18144组均0差异。半径和XP外层为JS/f32重组，没有执行原934/3231；NaN类别比较不包含payload，非法档位/区间仅比较替代panic trap。边界及证据见[升级](../reports/2026-11-01-executable-spec.md)、[敌人成长](../reports/2026-11-01-world-progression.md)、[半径](../reports/2026-11-01-radius-spec.md)、[经验](../reports/2026-11-01-progression.md)、[RNG](../reports/2026-11-01-rng.md)。这些独立规则尚未组成可玩流程。

生产规格只依赖Python标准库。对照需要研究区已经安装并校验的Node和WABT，以及固定原始WASM；原始游戏文件不加入本目录或Git。全模块覆盖和完成标准见[重造工作基线](../RECONSTRUCTION.md)。

后续完整函数对照与早期微模块分开：`build_full_function_oracle.py`仅给原0.126.0增加批准函数导出，所有其他section逐字节保留；所有878个宿主导入设为拒绝，应用start不调用。属性8495、完整选卡5、完整扣血32，以及暂停域完整XP1954份对照，验证范围各自列在报告。这些工具仍固定旧SHA，不能给新版强行套用旧函数索引；新版有单独profile。
