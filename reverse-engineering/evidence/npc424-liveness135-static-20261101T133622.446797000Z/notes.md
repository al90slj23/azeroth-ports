# Opening NPC424 → headless：未写字节的实际读取条件

此结论只描述当前独立headless/cast/combat/AI组合的代码与已声明constructor写集，不宣称已覆盖原件完整880所有消费者。未改模型，未导入或执行模型／游戏，未读snapshot，未用观测padding或零补未写字节。

[静态读集与14份来源冻结](static-readset.json) SHA `3d81f8c54a4c2fbb4d1f610334c944afcd7e7ac4f114cb4be3e7d285be3d2657`；[可重跑检查](check_readset.py)只用AST读取常量并计算字节交集。

## 确定结论

`opening_npc_pickups135.NPC_WRITTEN_RANGES`为`(0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139)`。其补集为`[4,8),[12,16),[20,40),[44,64),[68,112),[248,280),[419,424)`，共129B。

`headless135._cast_state:148`先要求完整hex→bytes424；`decode_spatial→decode_unit`再无条件解包完整语义对象。但这些字段与129B未写域的交集**只有12B：U4与Q32**。其余117B并未被该decoder读取；完整bytes／hex的要求是一项表示约束，不能据此推断117B在当前算术中活跃。

默认opening通过`spawn135.py:136-138`写marker0，kind40／kind64／elite244均为-1。这些tag正好使下表两个未写字段在当前普通活NPC算法中不需要读取。未写并不意味着零，也不意味着之后永远不活跃。

| 未写字段 | eager读取与校验 | 真正语义消费条件 | 当前默认opening |
|---|---|---|---|
| U4 `death_time_4_bits`，4..7 | `unit_records135.py:39`经FLOAT_FIELDS解包；`combat134.UnitState.__post_init__:95-98`要求u32；`area_effects135._cast_finite:132-135`要求finite | 当前cast／914算术没有读取旧死亡时间。`combat134.resolve_damage:268-270`致死时直接写`now_bits`；`ai_lifecycle135.cleanup_ordinary_corpses:31`仅marker==1后才读取旧U4并比较age>1.2 | marker0，旧值不需要。发生致死后由已恢复的producer把U4变为已知clock，再供corpse cleanup消费 |
| Q32 `linked_id_32`，32..39 | `unit_records135.py:41`解包QWORD；`combat134.UnitState.__post_init__:99-101`要求uint64 | `cast135.projectile_targets:168-169`保护扫描中，仅`x.marker==0 && x.kind_40==2`才读x.Q32，且该扫描还需target的kind40==-1、elite244!=-1、phase412未生效、phase408未生效；`combat134.damage_phase_bits:188-195`仅target.elite244!=-1或kind64!=-1且两个phase分支均未返回时扫描，扫描同样仅活kind2读Q32；`combat134.resolve_damage:250`另在target.kind40==3时读目标Q32 | kind40/64/244全-1；无活kind2来源；扫描条件短路，不读Q32。kind3目标还会先被`cast_events135.apply_hit:28-29`拒绝，当前common-hit组合到不了914的kind3→Q32分支 |

`combat135.py:8-11`是`combat134`类型／算术的显式reexport，因此上述combat134行号就是当前135路径实际使用的代码，不是把旧案例数计入135。

## Decoder其余字段逐组核对

下列全部处于constructor已写范围内；不需要补任何129B未写域即可得到它们的位模式。条件来自当前实际消费者，和decoder当前eager解包是两件事。

| 字段／物理偏移 | 当前消费条件与位置 |
|---|---|
| marker U0；targetGUID Q112 | `cast135.query_targets:145`先按marker／排除GUID过滤；GUID还用于lookup、结果同步及唯一性检查 |
| kind40 U40；kind64 U64；elite244 U244；elite416 byte416 | projectile priority：`cast135.py:162-171`；damage modifier：`combat134.py:144`；phase modifier：`combat134.py:188`。所有分支应先消费相应tag再决定附属字段 |
| HP U288；maxHP U292 | `combat134.damage_modifier_bits:146`低血判断；`resolve_damage:263-274`HP／accounting；HP另用于`cast135.projectile_targets:182`近邻ordinary优先级排序 |
| control deadlines U124/U380/U388 | `combat134.damage_modifier_bits:140-143`控制状态item18分支；实际本headless的items空，但当前函数仍检查deadline |
| afflicted U240 | `combat134.damage_modifier_bits:148-149`item21分支 |
| modifier deadline U356 | `combat134.spell_modifier_bits:166-170`：spell非零且实际存在tag50 modifier；当前headless `CombatState`的spell_modifiers为空 |
| additive magnitude/deadline U144/U148 | `combat134.damage_modifier_bits:150-151`：先比较deadline148，只有有效才用144 |
| additive magnitude/deadline U152/U156、U160/U164 | `combat134.damage_modifier_bits:153-156`：先比较156；失效才比较164；有效分支才读对应magnitude |
| additive U368 | `combat134.damage_modifier_bits:160`返回时使用 |
| phase deadlines U408/U412 | `cast135.projectile_targets:166-169`仅elite244!=-1的目标；`combat134.damage_phase_bits:188-193`仅elite244!=-1或kind64!=-1。普通opening两个tag均-1，故短路 |
| movement duration U344、start U340；fromXY U316/U320；toXY U328/U332 | `cast135.position:125-132`先读duration；duration<=0直接返回toXY；duration>0才用start/fromXY插值。致死时`combat134.py:269-270`写duration0与start now |
| priority deadline U372 | `cast135.projectile_targets:162`先检查；生效直接priority3，不继续tag／phase扫描 |

AI补充：`ai135._validate:77-89`、`position:45-52`、`_speed:55-60`、`_attack:64-67`以及普通更新循环的字段全部落在constructor已写范围；其注释明确byte276在ordinary family未消费。`ai_lifecycle135:29`的resource-family守卫只用已写U40/U64/U244/U232/U240；旧U4读取仍仅在marker1分支。此处仍有完整hex/bytes表示约束，但没有新增未写字段的实际算术需求。

## 不能只放宽decoder

1. `combat134.UnitState.__post_init__:95-101`不允许U4／Q32为None，当前类型本身就是先于语义分支的阻断。
2. `area_effects135._cast_finite:132-135`遍历每个UnitState的全部`*_bits`，包括活NPC旧U4；`tick_areas:208`在遍历area记录前调用，所以空area也会被阻断。`produce_area:152`同样调用。真实snapshot若旧U4是allocator NaN，仍会发生与当前area语义无关的finite拒绝，不能据此认定真实Game非法。
3. `unit_records135.patch_unit:63-66`无条件打包全部FLOAT_FIELDS与Q32，包括未改变的旧U4／Q32。`headless135._cast_phase:258`每阶段均调用patch；只把decode结果改None仍会在此失败，或在以默认0代替None时污染未知字节。
4. `_cast_phase:181,258,276`及`_ai_phase`、effect adapter、projection仍用hex/bytes表示。要携带None直到实际producer写入，必须共享一份可保留未知cell的immutable row；不能在这些边界隐式转零。其consumer算法读集可以按本表逐一移植，而不扩大输入支持域。

## 建议的最小None-aware入口契约

保留`tuple[int|None,...]`424个物理cell及constructor provenance。做显式的`require_u32/require_u64(offset,consumer,guard)`读取：已知返回位模式；只有真实走到该读点且仍None才返回带GUID／offset／width／consumer／guard的boundary。此入口不读取观测padding来生产状态。

普通活NPC入口可保存`death_time_4_bits=None`与`linked_id_32=None`，先验证已知marker0、kind40/64/244=-1。UnitState与area验证均应只要求实际当前算术会消费的字段；不要遍历全部`*_bits`来强迫无关的死亡时间有限。以后变为kind2／kind3且消费Q32时，必须有实际producer或明确输入，不能沿用默认0。

Patch保留原物理row及未写cell：未发生写入的U4／Q32继续None；accepted nonlethal伤害只把HP288变为新值；lethal branch按`combat134.py:267-270`写HP288、marker0→1、duration344=0、afflicted240=0、death_time4=now、movement_time340=now；death placement另按明确写集写XYZ316/328。Area status写U120/U124也已有显式effect_writes。可以以这些语义producer的defined writes更新row，不要以dataclass默认值覆盖其余字节。

之后即使跨过此NPC接口，from_opening的真实capacity、伴生88B、special40／window／boundary、world、kind2 pickup以及完整880前段仍须分别接续；本结论没有把这些现存边界消除，也没有增加独立帧或完整一局证明。
