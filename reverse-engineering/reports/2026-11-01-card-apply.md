# 真实选卡的独立能力状态规格

目标为原始 Web **0.126.0 / 3e72472a**，原 WASM SHA-256 为 `067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c`。本轮把1065的拥有能力更新变成可执行 Python 规格：先对照**原1065连续片段，非完整1065**，2345张升级卡和1份初始化记录全部按80字节比较，0差异；再对**完整原1065**执行5个有限空状态样例，80B及选择收尾状态全部一致、0宿主调用。

生产规格 [`ability_state.py`](../reconstruction/core_spec/ability_state.py) 不加载原游戏。完整原函数执行是另外的研究oracle；其中1573/4595和其他原内部辅助函数照常执行，没有被替换为模型。有限样例通过不能称为全部选卡流程已复造。

## 可直接使用的API

| API | 输入与结果 | 已执行范围/边界 |
|---|---|---|
| `AbilityRecord.from_bytes/to_bytes` | 完整80B拥有记录与数据类互转 | 所有字段保留raw u32；浮点字段以binary32位模式表示 |
| `AbilityDefinition(pointer, ability_id, execution_kind)` | 定义指针、字符串ID字节、定义+84类别 | ID用于数量上限；不以spellID代替字符串ID |
| `UpgradeCard(owned_index, kinds, tier)` | 拥有向量索引、有序kind序列、档位0..4 | 同一kind可重复；顺序必须保留 |
| `apply_upgrade_card(record, card, definition)` | 返回新的80B记录，不改传入值 | 完整已有能力升级数值循环；不包括后处理 |
| `NewAbilityCard(ability_id, tier)` | 新能力字符串ID与档位 | `from_candidate_bytes`只解canonical new tag |
| `initialize_ability(definition, tier=0, additional=28B)` | 返回新拥有记录 | 必须明确提供26840的28B附加字段结果；非零tier显式raise |
| `neutral_additional_bytes()` | 返回空modifier向量的26840结果 | 只有调用者已证明modifier向量为空才可采用 |
| `accept_upgrade_selection(state,index,definitions)` | 处理入口guard及现有记录更新，返回`SelectionResult` | `definitions`按定义指针索引；结果列出未执行副作用 |
| `accept_new_ability_selection(state,index,definitions,additional=...)` | 初始化并追加新拥有记录，返回新增索引 | `definitions`按字符串ID字节索引；同样显式返回未完成副作用 |
| `selection_completion_control(...)` | 4595中的计数/优先级决策 | 必须显式确认loot pass已处理；不调用4595/2098 |

两个`accept`入口要求`phase2299==2`、候选索引在范围内、`selection_kind2297!=255`；否则返回`accepted=False`和原状态。已有卡指向越界的拥有索引时不更新记录，但原1065仍会进入共享后处理，因此该情况仍返回`accepted=True`及待执行副作用。选择API不会悄悄清除候选或把阶段改成1。

最小用法：

```python
from core_spec.ability_state import (
    AbilityDefinition, AbilityRecord, UpgradeCard, apply_upgrade_card,
)
definition = AbilityDefinition(12288, b'fireball', 0)
record = AbilityRecord(12288)
updated = apply_upgrade_card(record, UpgradeCard(0, (0, 1), 2), definition)
assert updated.level == 3  # 每个kind各加一次，不是整卡只加一次。
```

## 两种80B结构不能混淆

拥有记录来自`state+1468`，长度`state+1472`，步长80。候选来自`state+1716`，长度`state+1720`，步长也为80，但布局不同。

| 拥有记录偏移 | 含义 |
|---|---|
| 0 / 4 / 8 | 定义指针 / u32等级 / 剩余冷却bits |
| 12 / 16 / 20 / 24 / 28 | 伤害倍率 / 冷却倍率 / u32额外数量 / 范围倍率 / 持续时间倍率 |
| 32 / 36 / 40 / 44 / 48 | kind0..4各自的u32次数 |
| 52 / 56 / 60 / 64 / 68 | 附加伤害 / 附加冷却 / 附加u32数量 / 附加范围 / 附加持续时间 |
| 72 / 76 | 生命属性伤害项bits / 尚未完整命名的效果字段bits |

候选`+60`是niche编码/向量capacity复用槽。原switch把非负值与`0x80000001`都送入已有能力分支；该分支`+64`指向kind字节向量，`+68`为长度，`+72`为拥有记录索引，`+76`为档位。canonical新能力tag为`0x80000000`，此时`+64/+68`为字符串ID指针/长度。`+0..59`为展示/说明相关数据，不能当成拥有记录前60字节。

## 已有能力的精确更新顺序

对候选kind字节序列中的**每一个kind**：

1. 等级以u32加1并wrap，再调用25242；它读取的是当前记录，因而重复kind看见上一次更新。
2. kind0写`damage=(1+x)*damage`；kind1写`cooldown=cooldown-x`；kind2把`trunc_sat_f32_u(x)`加到数量并u32 wrap；kind3/4按原操作数顺序写`x+area`、`x+duration`。
3. 对应次数以u32加1并wrap。
4. 公共伤害增长为`damage=(1 + .04 / (1 + .125*sat_sub(new_level,2)))*damage`，每步binary32舍入。`new_level`先wrap，再做无符号饱和减；不能用未wrap的Python等级算增长。

空kind序列不访问档位，也不增加等级；规格保留这一点。恢复的支持域为kind0..4；超出域会明确拒绝，不模拟原件未确认的非法输入行为。非空kind的tier域0..4沿用已验证的25242规格。

## 新能力初始化与未完成辅助函数

1065按字符串ID扫描113条88B定义。初始化记录等级为1、剩余冷却为f32(0.5)，主倍率12/16/24/28为1，目标数量和五个次数为0。附加区域52..79的空modifier基线为`[1,1,0,1,1,0,1]`，其中数量槽为u32。

原件随后先调用26840写入附加字段，再调用26457按tier修饰，最后把80B结果追加到实际拥有向量。tier0的26457只是复制记录，因此本规格可在调用者显式提供26840结果时完成该分支并追加。非零tier的26457有执行类别/效果tag/允许升级列表分支，本轮未实现；直接raise `UnresolvedAbilityEffect`。未提供26840结果也会raise，不会以空天赋值替代。

新技能追加后的spell通知、1065其余共享天赋/通知/装备相关后处理、1573属性重算，以及4595收尾都以`pending_effects`暴露。调用者必须处理这些工作，才能宣称整次选卡完成。

## pending、phase与4595边界

1065尾部顺序为：共享后处理 → `1573(state)` → `4595(state,入口2297)`。2297必须在入口保存；不能先清成255再交给4595。

4595先按入口选择类别对队列计数做饱和减1：kind1减2092，kind2减2096，其余类别减2088并把2293置1。然后清候选长度1720并销毁候选内容，再收取符合条件的经验loot；该收取可能增加待选计数。**必须在loot pass之后**才按2092 → 2096 → 2088判断下一队列。2088还受`2284==1 && (2285&1)!=0`抑制。

没有下一队列时，原件清2285、置2297=255，随后置阶段2299=1；模式0还调用25345恢复相关移动/消息路径，并有1020效果及其他通知。仍有下一队列时调用`2098(state,next_kind,0)`；enter_now为0，不执行主动切入阶段2的分支，原先阶段2维持。2098的候选生成仍未实现。

`selection_completion_control`把以上控制子集变成可执行决策，绝不自动跑loot：`loot_collection_complete=False`会raise。若已按原顺序处理了递减和loot，传`entry_kind=None`以及最终队列计数；若已证明loot不改变队列，可传原计数和入口kind，让函数执行递减。返回的阶段/类别是控制决策目标；待执行的恢复、效果、通知或2098仍明确列出。该子集的108组断言是**模型及静态恢复检查，非原4595差分执行**。

## 原件差分与证据

```sh
python3 reverse-engineering/scripts/check_ability_state.py
```

本机证据：`evidence/ability-state-oracle-20261031T234910.842713Z/`。提取脚本先重验原WASM和原1065/25242函数体哈希，编译仅用于取得操作码的WAT片段，再在原1065二进制体中查找**唯一、连续、逐字节相同**的片段，执行时复制这些原字节。模型实现独立于原片段，不参与oracle计算。

| 原1065片段 | 原文件范围，末尾不含 | 字节 | SHA-256 |
|---|---|---:|---|
| 已有能力升级循环，原WAT行836..948 | `[5576603,5576839)` | 236 | `354042ac41bdda1031fa4c21af37c08af790de5db997d3d3ceb51bbda966eb7e` |
| 新能力初始化stores，原WAT行457..495 | `[5575733,5575881)` | 148 | `b57ef6ed4b41ee816c0b62d49d22fdc8253ef05b8dc1b66d9a4015461e0fa42c` |

原25242完整620B函数体逐字节复制，原函数索引及它的panic80330调用索引保留；其余80330个函数体为trap占位。另有两个明确标识的合成wrapper，只设置fixture用局部变量并承载上表原片段。模块无imports/start/table，固定82页内存，没有完整游戏入口。

| 升级卡输入组 | 数量 |
|---|---:|
| 全部长度1..3的kind有序组合，全部五档 | 775 |
| 等级及次数wrap、u32转f32边界 | 40 |
| 类别11与四个特殊ID的数量上限 | 30 |
| 固定种子有限raw word，最多15个kind | 1500 |

共2345张卡逐字比较整80B记录，另1份初始化stores输出比较完整80B，**0差异**。随机输入不承诺NaN载荷身份；脚本对计算字段保留NaN类别比较规则，本轮没有出现需按NaN类别放行的差异（`nan_equivalent_words=0`）。未更新字段照常按原字比较。

微模块SHA-256为`571ee4ce95303c18e3b447207e6bd37c1afd5adc02eb6ac945c9786cd9ab8309`。这些结果证明已测试输入的初始化与已有升级片段一致，不证明全部可能输入穷尽，更不证明完整1065、天赋、rarity、候选生成或收尾副作用均已实现。未启动完整原游戏、使用网络、读取存档或修改安装包。

## 附加：完整原1065的有限受控执行

```sh
python3 reverse-engineering/scripts/check_full_card_apply.py
```

通过独立的`build_full_function_oracle.py`只修改原模块export节7，添加1065、1573和原allocator/deallocator的研究导出；其余节的每个字节均与固定原件一致，包括全部原指令、数据、表、内存及globals。builder与runner分别重查非export节完全相同，原模块没有隐式start节，runner也没有调用任何原应用启动导出。878个宿主函数导入全部被设置为立即throw，实际调用0次。

所有state、拥有向量、候选向量及动态kind序列都由**原106495分配器**分配，再写入人工构造的数据；没有复用存档。状态使用warrior/human、等级1、无modifier/装备/loot、mode2294=0、pending2088=1，定义为实际表中的`cleave`。调用完整1065后，读取整80B拥有记录、拥有数量、phase2299、selection_kind2297、pending2088及候选长度1720，与独立模型/静态控制预期逐项比较。

| 完整函数fixture | 结果 |
|---|---|
| 已有能力：kinds(0,1)、tier2 | 等级1→3；80B逐字一致；完成收尾 |
| phase1入口守卫 | 拥有记录、候选及pending不变；不接受本次选择 |
| 空kind序列、tier999 | 不访问非法tier；记录不变，仍完成收尾 |
| 越界owned index1、实际只有1条 | 不更新拥有记录，仍完成收尾 |
| tier0新技能 | 执行原26840/26457、真实append、原1573/4595；初始化80B一致 |

四个接受的选择均在原1065内完成所有命中的后处理，返回phase2299=1、selection_kind2297=255、pending2088=0、候选长度1720=0。阶段不合的fixture保留phase1、selection_kind0、pending1及候选长度1。**5例全部通过**，不是把模型的`pending_effects`忽略后宣称完整成功；完整oracle实际执行原件后处理。生产模型的未实现副作用仍明确保留。

本机证据：`evidence/full-function-oracle-20261031T235147.634032Z/full-card-apply-probe.json`；完整研究模块SHA-256为`a8ad6ad7bb15599e1c03ec76f9f4f137cb969ff88891dbb63367ab80c292192c`。它与上文无imports的微模块是两种不同oracle，不能混称。

该附加验证尚未覆盖非空modifier/装备/loot、非零新技能tier、pending2092/2096或自动生成下一批候选。它验证的是固定原件在这些自造状态中的真实函数行为，未启动完整游戏、未允许宿主调用，也没有把原函数加入生产规格。
