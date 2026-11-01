# 独立重造的工作基线

目标是逐项拆清原作逻辑和数据，形成能够独立运行的游戏核心。按用户最新方向，**主目标已切到官方0.134.0**：Web build`983346a7`，Windows官方SHA单独固定。此前0.126.0 / 3e72472a作为历史验证与复用参考保留，不再作为继续扩展的主目标。完整原件身份见[targets.json](targets.json)，迁移原则见[版本策略](VERSION_STRATEGY.md)。工具安装、原始游戏、WAT和原件函数测试模块均保存在本机忽略区；独立实现放在[reconstruction/](reconstruction/README.md)。

这里的“完成”需要覆盖行为、状态变化和结果，而不是只有函数地址、解码文本或一份大关系图。原作Rust变量名和源文件原文没有恢复；重造不以逐字找回这些标识符为验收条件。

## 0.134.0迁移状态

| 范围 | 当前证据 | 下一步 |
|---|---|---|
| 官方原件 | Windows更新EXE通过官方大小/SHA；同版Web快照完成身份提取；[新版完整WAT/独立索引完成](reports/2026-11-01-wasm0134-profile.md) | 资源RAR仍单独下载/验收；按新版索引恢复消费者。 |
| 原生同源核对 | 本版PE重新定位五表、两原生函数；五路升级结构与历史规格相符 | 继续在当前原生消费者中核对行为；Web结果不冒称原生执行结果。 |
| 目录与差异 | [114能力、9职业的新表](reports/2026-11-01-catalogue0134.md)；新增stormstrike/rockbiter、移除call_of_flame，stoneform参数变化 | 新定义/职业kit不等于所有技能、天赋行为已实现。 |
| 升级数值 | [新原25368的11560例对照，0差异](reports/2026-11-01-upgrade0134-spec.md)，现有独立数值模型可复用 | 四个逐字节匹配的其他helper尚待新版上下文与执行验收。 |
| 选卡与施法状态链 | [16完整新函数、29条guard](reports/2026-11-01-selection0134-chain.md)；[完整新1073的779例，0差异](reports/2026-11-01-selection0134-spec.md) | 已验完整80B+5标量；共享后处理、属性输出与完整选卡控制API仍未独立迁移。 |
| 敌人扣血 | [424B单位、36B新加区与55条guard](reports/2026-11-01-combat0134-chain.md)；[独立combat134与完整新914的454例，0差异](reports/2026-11-01-combat0134-spec.md) | 缺完整触发/掉落/死亡RNG；玩家incoming1063与IceBarrier另行恢复。 |
| 经验与成长 | [12完整函数/28条guard](reports/2026-11-01-progression0134-chain.md)，确认新版120级上限；[独立progression134与完整新4630的2197例，0差异](reports/2026-11-01-progression0134-spec.md) | phase3只验level/XP/pending/phase；拾取几何、消息/治疗独立实现和2159候选生成仍缺。 |
| 其他独立模型 | 下表所列模型有0.126.0依据；未自动计入0.134.0完成度，逐项范围见[版本支持清单](reconstruction/version-support.json) | 刷怪、施法基数/暴击、属性、存档、UI与协议继续迁移和连接。 |
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
| 模型、地图和音画资源 | M2/BLP/WMO及DBC入口 | 尚无独立完整资源管线 | 索引/加载/动画/特效/材质/声音与具体玩法ID关联。 |
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

`core_spec.binary32`用精确有理数计算和逐步binary32舍入。**0.134.0已验证范围**为升级值11560例、有序拥有记录/中性tier0初始化779例、新`combat134`扣血主字段454例，以及`progression134`经验四字段2197例，各自范围和未实现项见上表与版本支持清单。选卡、扣血和经验的完整原模块确实被实例化、内部callee保持原样；未调用应用start，所有宿主导入拒绝且实际调用0次。

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
# 当前0.134.0；需要已固定的新原件及本机证据输入。
python3 reverse-engineering/scripts/check_upgrade134_spec.py
python3 reverse-engineering/scripts/check_selection134_full_spec.py
python3 reverse-engineering/scripts/check_combat134_full_spec.py
python3 reverse-engineering/scripts/check_progression134_full_spec.py

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

上述不同验证层分开记录：无宿主导入的微模块、承载原连续片段的合成wrapper、仅新增导出的完整原模块。完整模块所有878个宿主导入均拒绝调用，应用start未调用，真实内部callee按所述fixture运行。没有启动完整游戏或访问网络/存档；也没有把0.126.0实验次数称为0.134.0验收。有限输入的一致不等于穷举证明，NaN不承诺载荷一致，替代panic的范围各自列明。

下一条可玩切片按“状态推进→生成敌人→自动施法→伤害/死亡→拾取经验→升级选卡”推进。与此同时持续补资源、存档、UI和协议清单，避免只完成战斗数值却遗漏整局流程。
