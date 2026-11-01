# 933/934 实际扣血核心独立规格与原件片段对照

绑定 Web **0.126.0 / 3e72472a**，原 WASM SHA-256 `067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c`；完整 WAT SHA-256 `02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c`。

已实现不依赖原游戏运行时的 `core_spec/combat.py`：934 的有序 base / 暴击，933 的条件加区、阶段系数、特例 cap、实际 HP 减法、统计截顶、HP wire 整数编码与死亡主状态。**这是核心投影，不是完整 933/934、游戏 tick 或完整死亡系统。**

第一组 9153 个确定性案例对照 **0 差异**。本组原件侧执行的是 **12 段逐字节匹配的连续指令片段**，由自定义初始化与终止包装组合；没有执行完整 933/934。每段的原函数编号、完整函数内行号、原 body 相对偏移、长度和 SHA 见 JSON。所有片段在经身份校验的原始 WASM body 中逐字节找到，因而并非把 Python 公式重新写一遍作为 oracle。

## 可接入 API

所有 f32 参数与返回值均为 uint32 位模式；统计总值保留原 f64。数据类冻结且序列字段转 tuple，执行返回新状态。

```python
base = base_hit_bits(definition_damage_bits, ability_damage_bits,
                     ability_additional_bits, category, player_hp_bits,
                     ability_hp_component_bits, player_damage_bits)
hit = critical_hit_bits(base, crit_probability_bits, crit_multiplier_bits,
                        rng_state)  # .amount_bits .critical .uniform_bits .rng_state
result = resolve_damage(state, target_id, hit.amount_bits,
                        spell_id=133, spell_category=0)
# .state .target .applied .reason .damage_bits .old_hp_bits .new_hp_bits
# .accounted_bits .encoded_hp .dead .unknown_sideeffects
```

`CombatState` 含 units、items、now_bits、shield_bits、running_2299 与 accounted_total；`UnitState` 至少需要 target_id、hp_bits、max_hp_bits，其余以原偏移命名并提供普通单位默认值。`ItemModifier(tag, value_bits)` 保留原顺序。投影要求 GUID 唯一；特殊 `kind_40==3 && linked_id_32==0` 目标使用非零 spellID 时必须由调用方提供已解析的原始类别，不会猜测。

## 恢复的实际规则

- 934 保留定义 `+48`、能力 `+12/+52/+72`、玩家 HP/damage 及七项类别缩放的原逐步舍入顺序。暴击用 xoshiro128++ 输出**高24位**乘 `2^-24`，严格 `probability > U`，并返回全部四字的新 RNG 状态；区别于 32475 的范围采样。
- 933 的 tag18/19/20/21/28 按条件先分别累积，再按原顺序加入 M；控制字段、精英条件、严格低于 `f32(.3*hpm)`、afflicted、盾都独立处理。附加 `+144`、优先 `+152` 否则 `+160`、最后 `+364` 的时限与顺序保留。
- P 保留 1 / 1.5 / .25、时间优先级及关联的活着 kind2 记录。特殊 kind3/link0 的类别拒绝、select 型 NaN-aware `hpm/5` cap 和零 cap 早退分别恢复。
- NaN 伤害变1，其余取至少1；执行真实 `f32.sub` 写入新 HP，**不把负 HP 截成0**。统计值截在旧 HP 的非负非NaN部分以内，再提升 f64 累加。
- HP 编码为非负非NaN处理、ceil、unsigned saturating conversion。死亡核心以 `new_hp <= 0` 决定；NaN 不通过。恢复 marker `+0=1`、`+344=0`、`+240=0`、`+4=now` 与 `+340=now`。

## 原件核对与边界

| 组 | 案例数 | 观测边界 |
|---|---:|---|
| base | 2852 | 原934:L440–507 连续片段，所有256个类别及特殊值/随机位模式 |
| category guard | 256 | 原933:L1228–1239 连续片段，全部 u8 类别 |
| critical | 1541 | 原934 RNG 更新与伤害选择两段，含严格阈值及四字状态 |
| cap | 1232 | 原933:L1241–1265，含 NaN/Infinity/符号零 |
| wire | 1216 | 原933 非负选择、ceil、trunc_sat 三段组合 |
| resolve | 2056 | 原933 M/P、cap、真实 HP store/f64 total、death 写入的组合 |

微模块 **2995 bytes**，固定 **32 页 / 2MiB** scratch memory；无 host imports、start、data segments、table、callee 或 stub。保留的完整原933 body SHA 为 `8f3936de6295d0250b32ab3abf1a3bb7f6b913a2b3067f26f6e0561dd3128e5f`，934 为 `0da442c86897761d461c11007b5fdb4cbafb27a1ba1f923a379592c832b67175`。WABT1.0.42 编译/验证通过，原 WASM/完整 WAT 前后 SHA 一致。原件执行与模型结果、案例、mismatch 空表与 source/artifact hashes 保存在 `evidence/combat-oracle-20261031T235733.574000Z/`。

复核修正了取证边界：连续 NOP 标记会与 `i32.trunc_sat_f32_u` 的尾字节重叠，短字节串的首次搜索还可能误中其他指令的立即数。现使用不自重叠的常量/drop 标记，完整解码933/934并逐条对齐原WAT行，所有span均按真实指令边界比较原件字节；另强制末段完整为 `fc01`。执行结果原本不受影响；本报告全部片段偏移与SHA已重算。该段原文件范围现为 `[3151798,3151800)`、body相对偏移6626、2字节、SHA `0ae7b0503ae77d153e4747c652deeaba896527ea5199e0771d69be32ef26f03a`。

`resolve` 的组合包装负责将片段结果接入下一片段，不能据此宣称完整原933控制流执行。原函数 lookup 及省略路径之外的状态空间未被证明；核心 API 另有独立的运行状态/缺目标/已死亡/类别拒绝/不可变性检查。浮点 finite 值逐位比较，NaN 只比较类别，不声称 payload/sign/signaling 等价。有限语料不能替代穷尽证明。

**独立规格没有恢复** per-spell 统计容器、procs、治疗/吸血、loot/XP、位置动画插值及 HP 更新包队列。下述完整原933对照保留并执行可达的原内部消费者，仍不等于把这些规则全部独立重写。没有调用原应用 start、官方网络、存档或修改安装包。

特别是死亡后 RNG 不得假称连续：933:L6895–6929 对普通单位 XP 随机舍入推进一次；L6971–7005 还有奖励概率的一次；成功且普通单位时 L7045–7086 还可能按 rejection 循环推进，再以乘3高32位加2得到2..4。此前触发及 call1411 等闭包没有穷尽。**本 API 不发放 XP/loot，也不消费死亡 RNG；`CriticalHit.rng_state` 不能直接冒充完整死亡处理后的 RNG。**

## 第二组：完整原933真实调用

另外建立了只增加 research exports 的完整研究副本，**只有 section7 改变**，原始函数代码、表、全局、内存及数据段保持原始字节。完整模块没有隐式 WASM start；应用 start export 从未调用。878 个原宿主导入全部绑定到抛错函数，**32 例共0次宿主调用**，无 callee stub。

32/32 例执行**完整原933及原内部callee**成功，核心输出 **0差异**。每例使用新实例、真实原106495 allocator分配独立5000字节state、416字节unit及物品表；没有把自选地址写到原heap。普通目标使用原定义指针1667680，spell133 / school2，能力/天赋向量为空。覆盖最小伤害、过量、NaN/Infinity、临界致死、全部五个条件item加区、目标debuff时限优先级与P1.5/.25。

例如 HP100、damage10 得到原始HP90、f64统计10、marker0、RNG保持原四字；damage150 得到原始HP-50、统计100、marker1、死亡时间及移动时间10。对应原包队列长度分别2和5，这证明完整函数继续执行了原内部队列路径；本规格没有把队列和完整奖励系统独立恢复。

对于本组确切seed `(1,2,3,4)` 与默认普通死亡fixture，实测致死路径均推进4次 RNG 到 `(27274249,25704967,31982592,12605441)`；非致死0次。该观察不推广为所有单位/seed固定4次，也不改变 API 仍排除死亡 RNG 的边界。

原件执行结果和每例 RNG 观测保存在 `evidence/full-function-oracle-20261031T235400.319122Z/combat-full-results.json`，摘要和空差异表同目录。完整研究模块SHA为 `20dd2464ac9e0bf2474b089b8ffa84b3f1731a4bbe6d993339be3d123e7f76ae`（以JSON中的实际manifest/summary为准）。这组提供完整原933对有限合成状态的行为证据，仍不是原应用游戏循环、所有触发路径或官方联网验收。

## 复现

```sh
python3 reverse-engineering/scripts/check_combat_spec.py
python3 reverse-engineering/scripts/check_combat_full_spec.py
```

构建器通过 SQLite `mode=ro` / `query_only` 定位完整原 WAT，重验完整输入及933/934 body/WAT身份，构建仅含受控片段的 micro module，并逐片段复查原始字节；Node 只实例化 micro module。机器可读结果见 [2026-11-01-combat-spec.json](2026-11-01-combat-spec.json)。
