# 固定 0.135.1：真实 Boss 矩形效果生产链

新增独立规格 [effect_geometry135.py](../reconstruction/core_spec/effect_geometry135.py)，恢复三条真实 Boss `raw9` 描述的 **2785 构造 → 910 生产 120B 记录 → 915 消费**。最终 390 组、2,883 个状态快照零差异。其中 **277 组正常完成；113 组是预期资源拒绝前缀，不能算正常命中完成**。[机器报告](2026-11-01-effect-geometry0135.json)区分两类结果，完整游戏流程和全 915 仍未完成。

最终收据：`evidence/full0135-oracle-20261101T080844.947484Z/effect-geometry135-comparison.json`，SHA256 `94cbbfaf8d629037ac4739b334e1b6eda6642f4485467218d29a4d66508177b8`。原件固定 `c62c85f5…dc96e2`；28 项源码闭包含包入口和传递数据依赖，在原件前冻结独立预期。完整原函数及内部 callee 保留，只修改 export section 7。

## 原始生产者与记录

从已逐字保留的 290 条 Boss 描述中，选择全部三条 `raw_tag37=9`、归一化类型 6 的描述：

| Boss | 区域 | Boss72 地址 | 原始 40B 描述地址 |
|---|---:|---:|---:|
| Tendris Warpwood | 5 | 5434088 | 5433104 |
| Anub'Rekhan | 11 | 5455432 | 5453396 |
| Patchwerk | 11 | 5455576 | 5454132 |

每组先实际执行 2785，读回完整 Boss 424B 与所有技能计时器，再调用真实 910。没有向原件直接注入 synthetic120；描述也没有改成零法术。阵列的相对坐标、移动插值、弱化、时间和高度开关是原件前声明的受控输入。2785 按既有平坦高度域构造；关闭高度开关的实验只在构造快照之后显式切换该输入。

910 的相应分支调用 `4865 → 21024 → 61441 → 34693`：先预测玩家坐标，再停止/锁定 Boss、发送 221 与 305，最后追加 `normal0 / type0 / shape2` 的矩形 120B 记录。`G2356` 为效果编号，**独立于**单位与拾取物共用的 `G2408`；这里的 910/915 不增加 G2408，也不额外抽取 RNG。

| 偏移 | 恢复字段与规则 |
|---|---|
| 0 / 8 / 40 | normal 0 / type 0 / rectangle 2 |
| 4..7 / 119 | 保留目的槽原字节 |
| 12 / 16 | 4865 预测玩家 Y / Z，来自复用的 scratch |
| 20..23 | scratch 尾字未写后被复制，显式标记 unspecified |
| 24 / 32 | source GUID / visual GUID 0 |
| 44 / 48 / 52 | 原描述长度 / 宽度 / 新 G2356 编号 |
| 56..68 | 施法者插值 XY、世界高度、朝预测玩家的 atan2 角 |
| 72 / 76 | now / now + delay × (difficulty 非零时 0.85，否则 1) |
| 80 / 84 / 88 / 92 | 0 / 真实 spell ID / 弱化后攻击 × 原描述系数 / +Infinity |
| 96..118 | 原件重叠写入产生的零值 |

没有把记录整体清零。整个 120B backing 共严格比较 **22,128,144 字节**；仅产生记录的 `+20..23` 共 13,296 个观察字节明确不预测，其中实际有 3,324 个非零字节，原始值保存在完整 sidecar。`+4..7/+119` 等保留域照常严格比较。Boss `+248` 仅规范化分配器地址；其余 424B 与计时器 payload 严格读回。没有 NaN 等价放宽。

## 915 的已恢复行为

该类型使用非周期的一次命中尝试。当前域 `player_flags2496=0`，预测点与玩家当前点相同；矩形判断为局部 forward 在 `[0,length]`，且 `abs(side) <= width/2`，边界包含等号。到 `now >= deadline76` 时，不论命中与否都移除该记录。到期前写 `118=1` 并产生预警；若第一次消费已经到期，原件先写 118、随后用移除索引过滤预警，**不发送短暂 hz，只发送 hzend/hzt**。这由新增同帧首次到期用例和完整 WAT 5237..5414 的控制流共同确认。

消费按记录顺序累加伤害，只在正总量时调用一次 `1073(category2, critical0, lastGUID, lastSpell)`。系数为：`2568==1 && difficulty<4` 时 1；否则 difficulty>3 时 3，其余为 2。已验证护甲、护盾、HP、最后受击时间、G992 浮点累计，以及 phase 守卫。多条同帧到期验证了浮点累加和一次进入伤害入口。记录按索引逆序做稳定 `memory.copy` 压缩；旧末槽保留，不清空 backing。

逐阶段新增通知严格比较：221 共 522、305 共 522、306 共 477；JSON 的类型、编号、kind/shape 与顺序严格比较：hz 共 498、hzt 共 1,224、hzend 共 477。完整二进制包与 JSON 字符串保留原始 sidecar；坐标/时间的十进制编码、wire codec 尚未独立实现，不宣称这些字节已经还原。

## 命中后的真实资源边界

113 组 phase1 命中在真实 915 → 1073 中先写入已比较的 HP/护盾/G992，再进入 `4546` 的真实 Spell.dbc 初始化，经 `95986 → 23171 → 50449 → 96127 → 67826 → 19179 → 122098` 请求真实 SELF。隔离宿主按设计抛出拒绝；98 组已实际改变 HP，其余包含护盾吸收等前缀。

这些组只验收到该前缀。捕获拒绝后立即停止整组并换新 instance，不恢复原件执行；生产结果为 `pending_original_spell_database`，状态 `entry_pending=True`，再次进入模型会拒绝。没有开放 host、写 Once/cache、伪造 SELF、把 spell 置零，或以 phase 守卫替代这些真实命中。后续 registry/history/aura、资源成功解析后的入口尾部仍未知。277 组正常未命中、phase 守卫或零伤害的完整返回单独统计。

原件进程固定 Node 22.23.4、60 秒期限、512 pages/512 MiB heap；最终 PID 见收据，退出码 0，原件尝试的 113 次 host 调用全部被拒绝。没有启动 app、执行 EXE、联网、读写存档。

## API 与拒绝边界

`EffectGeometryState135` 持有完整 `storage: tuple[Effect120135]` 与 length、完整 units424、now/zone/playerXYZ、incoming 标量、G2356/G2412/G1644/G2364/G2408、RNG、难度与高度输入。`Effect120135` 同时持有完整 raw hex 和明确的 unspecified 字节位置，不能把占位零当实际原件值。

- `produce_rectangle(state, unit_index, descriptor_pointer, raw40_hex)` 返回新状态与逻辑事件。
- `tick_rectangles(state, dt_bits)` 返回新状态、总伤害、逻辑事件及明确 status。
- 未恢复的 120 类型或辅助状态、非空 delayed56、未知地形/碰撞/导航、玩家移动预测、远端 owner、非空 incoming producer、非零 2364、致死或 callback 边界均保留输入并停止；11 项拒绝用例通过。既有 `effect_system135.py` 的 500 组组件没有修改。

本轮未接入 headless、完整 880 或 Boss 的真实调度流程；不能把这批受控 producer/consumer 用例加到现有八种子主链作为新完整帧覆盖。

## 本批时的浏览器 host 方案（历史静态记录）

下述方案在本批收据冻结时尚未执行；之后已在单独的[真实浏览器资源实验](2026-11-01-browser-resources0135.md)跑通三组正常命中。后批采用不同宿主策略，不能回改本批 113 组拒绝前缀的验收分类。

官方 glue 提供真实 SELF、XMLHttpRequest、同步 GET、responseText，以及 `__wenilla_data_base/layout/stamp` 配置所需的原始绑定。真实 Spell/SpellIcon 资源已可从现有独立资源 provider 读取。可尝试在单独本地 HTTP 研究页提供真实两个 DBC、真实 `__index` 和静态 URL，由浏览器原生 API 让 4546 自己解析。

但不能直接调用官方 `initSync()` 或默认 init 后宣称没有 app start：其 finalize 调用 `__wbindgen_start=176107`，完整函数是 `call851; call4253`，而 4253 正是 `export start`。安全的下一批应在新研究 bridge 中只追加 get-imports 与 bind-only 导出，保持官方 import 函数原样；手动实例化并绑定 wasm，单独执行原 `__wbindgen_init_externref_table` 初始化，绝不调用 finalize/176107/4253。真实浏览器提供 SELF/XHR，明确只允许本地资源请求，记录 URL、状态、资产 SHA 与解析后的真实状态。此方案尚未实例化、未架浏览器、未执行任何原件入口，externref、实际 XHR/索引与资源预算仍需验证。[静态证据](../evidence/effect-geometry0135-static-20261101T081015.075418Z/trace.json)保留 16 个完整函数身份和 glue 行号。

失败证据保留：080006 首次发现真实 host 边界；080249 的 206 项差异来自 clamp 先除后乘的 f32 顺序及 2785 fixture 高度域；080653 的 12 项差异补出同帧到期的预警过滤。最终通过依赖这些实际纠正，不覆盖旧结果。

[独立只读复核](2026-11-01-effect-geometry0135-independent-review.md)已通过，最终 review SHA `9b0f1a3bd7332c4f571c07250241ddfd79081784cdac5aa5f775c61d0d326a3f`；未重跑原件，既有验收范围与未知项保持。
