# 官方 0.134.0：kind 1 金币收取到当前局状态

固定 **0.134.0 / 983346a7**，原件 SHA-256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。已从完整新函数恢复 `2862 → 31731 → 28795` 的金币收取守卫、数值运算、局内计数、联机队列和玩家字段更新。**本次仅静态提取及 23 条纯 Python 手算契约检查，新运行原件案例数为 0；尚无本轮 28795/2862 金币收取差分通过证据。** 账号持久累计和之后的玩家字段 wire flush 仍为 unknown。

证据目录：`evidence/currency0134-chain-20261101T022005.805413Z`，manifest SHA-256 `c7cdf6a88d4b0dc81de2cd68c68977f2ede54f2e5ae969058e2391b2a3604ef0`。共保留 30 份完整函数 WAT/body、16 条连续指令 guard、5 份连续窗口和一份此前原件输出的真实 56B 金币记录。SQLite 只读，完整 WAT 按已核对的函数偏移 seek，没有运行 WASM、EXE、APK、应用 start 或存档。

## 收取守卫和执行顺序

```text
2862(G) 第二遍扫描：
  kind1：distance <= entryRadius
       或 marker == 1 且 arrival <= entryNow
  合格索引正向入临时列表，再倒序处理：
    保存 kind / amount
    31731(G,index) 按序删除记录并追加 despawn 消息
    28795(G,amount)
```

距离只用记录 `+40/+44` 和玩家 `G1504/G1508`，保留原 binary32 的减、乘、加、sqrt 顺序。半径来自入口快照 `G1384`。半径内的 marker0 金币不需要先吸引，也不需要有效的 arrival；因此旧 fixture 的 radius0 使偏移约 `(0.8,0.8)` 的金币保持 idle，而自然 radius9 会在第一次 2862 直接收掉。半径外则必须精确 marker1，并检查 arrival；NaN arrival 不满足 `<=`。本函数没有 phase 入口守卫。

31731 先用 `memory.copy` 把后续 56B 记录前移，再令 G1868 减 1。规范 marker0/1 路径追加 opcode **170**、长度 **8B**、payload 为该拾取的原 u64 GUID；aux 列表中的每个 GUID 也分别追加同类消息，再释放 aux。消息向 G1872/1876/1880 的 16B 消息 Vec 追加，不能将它称为已发送或接收。非规范 marker 和错误/分配失败行为没有被独立模块静默模拟为 no-op。

## 28795 的完整数值链

| G 偏移 | 类型 | 已证明的角色 |
| ---: | --- | --- |
| 1408 | f32 | 金币倍数 |
| 1544 | u32 | 本局可消费金币；20660 明确检查后减去 G2444 成本 |
| 1100 | u32 | 本局金币收取累计；28795 只按实际 award 增加 |
| 2574 | u8 | mode |
| 2520 / 2532 | u32 | 本地 peer / member count |
| 184 / 188 | ptr / len | 区域 ID，交给新 38322 |
| 2148 / 2152 / 2156 | cap / ptr / len | 金币联机队列，元素 8B |
| 2468 / 2472 | root / depth | 玩家键值树，u16 key、u32 value |

mode0 不追加金币队列，mode 倍数为 1。任何非零 mode 都先追加 `(G2520, baseAmount)`，记录的是**未乘倍数的原 amount**。仅精确 mode1 再计算：

```text
coefficient = regionIndex <u 3 ? f32(.7) : f32(1)
members = f32.u32(wrap_u32(G2532 - 1))
modeMultiplier = f32(1 / f32(1 + f32(f32(coefficient * members) * f32(.312))))
```

其他非零 mode 仍追加队列，但 mode 倍数保持 1。member count0 的减法先绕回 `0xffffffff`，不能默认单人。金币队列满时调用 65326，正常容量增长为 `max(4, wrap_u32(2*oldCapacity))`，4B alignment、8B stride；实际分配与异常边界仍由原完整 callee 承担。

随后严格按原顺序：

```text
scaled = f32(modeMultiplier * f32(G.f32(1408) * f32.u32(baseAmount)))
award = trunc_sat_u32(round85718(scaled))
G1544 = wrap_u32(G1544 + award)
G1100 = wrap_u32(G1100 + award)
player_key1176 = wrap_u32(G1544 * 10000)
```

**这里没有 XP 路径的 NaN→1 或最小 1。** amount0、倍数0、负值、NaN 都可以得到 award0；正无穷/正向超限经 `trunc_sat_u32` 得 `0xffffffff`。完整28795没有金币总量最大值 clamp；只有浮点转整数时的饱和。两个累计加法和乘10000都按 u32 绕回，不能把它们实现成饱和加法或无限精度整数。

key1176 存在时原地覆盖；不存在时携带查找位置调用3735插入。28795 没有直接消息构造/flush、1513 重算、1202、账号序列化或存储调用。其本体的正常算术/队列/键更新路径不读取 RNG；1820 的金币创建角度 RNG 属于此前的创建阶段，不应在收取时再消耗一次。

G1544 是可花余额，G1100 是这里增加的局内收取累计。**本轮未证明 G1100 何时转入账号的持久 `stat.gold`，也未恢复其新版本账号基址和触发 guard。** 不套用0.126.0的 G3696/368B旧布局，不把局内数值增加称为账号进度已保存。

## 完整 callee 与 unknown 边界

28795 的 **direct-call 递归闭包**共25个函数，完整函数均保留，直接闭包中没有 import。它不是所有间接调用的闭包：172316 有1条、49501有3条 `call_indirect`，处于错误/panic动态 handler 路径，目标行为尚未恢复。JSON保留4个站点及连续上下文；后续原件 probe 应保留原表和callee，不能换成 no-op 或据“0 direct imports”宣称所有错误路径无副作用。

| 函数 | 原 body bytes | body SHA-256 |
| ---: | ---: | --- |
| 28795 | 481 | `060656ba494343bd4edf74adead6e6b4d33a8674d9f2a69e1a44305da4d86946` |
| 2862 | 3179 | `502221f3e34228e0a37970e55505d1506f323d2c5f81510b707d8d8e414122ef` |
| 31731 | 411 | `560c55a9de7ea32b0e2ef6df126cb8ce457b3eb203f25090da48df26fb152cdc` |
| 3735 | 2092 | `a74c80160cb7cd545f993cbf932d40c9bcf9e4e692251615487da71fed6b4b7b` |
| 65326 | 109 | `d16105dd925ce6d1084b289dde9b86235bea0656c98139c699935ea952ce60e7` |
| 85718 | 68 | `3f9127d30eefb0c9bad49101460ed45df1f6069e63c42d87e351ffbb67151c36` |

JSON另给所有30函数的完整WAT/body范围、哈希、direct调用站点与完整闭包名单。物理B树/分配地址、后续玩家字段wire flush、联机队列消费者、账号持久化、混合XP与金币的完整2862调度、其他kind回调均保持独立边界。

## 独立模块和受控 fixture

新增 `reconstruction/core_spec/currency134.py`，只使用 stdlib 和已有独立 binary32/round 规则，不读取或调用原件：

```python
from core_spec.currency134 import CurrencyState, apply_currency

result = apply_currency(CurrencyState(gold=0, earned=0), 4)
assert result.award == 4
assert result.state.gold == result.state.earned == 4
assert result.key_update == (1176, 40000)
```

`CurrencyState`的 `multiplier_bits`对应G1408；`queue`为 `(peer, baseAmount)` 元组列表，`queue_capacity`对应G2148；`player_fields`为按唯一u16键排序的 `(key,u32value)` 元组列表。mode1要求显式 `region_index`，缺失返回 `pending_domain` 并保持原输入。成功状态为 `core_projection`，返回 `pending` 明示物理tree/queue分配、错误动态handler和后续wire义务，未把这些边界当作已执行。调用方负责真实2862守卫和倒序删除；本模块不会重新排序拾取或写账号。

fixture保存在证据目录的 `controlled-collection-fixture.json`。56B记录来自此前原件run `full0134-oracle-20261101T020143.890376Z` 的 case0/after_death/record0，已记录914→1417→1820的真实输出；该受控case使用真实普通定义模板、显式baseXP0变体，具体定义hex与seed均冻结在JSON。本次只读取已有回执，没有重跑该原件链。

该记录 kind1、amount4、marker0、visual9004，原append未初始化的arrival实际观测词为14519000；全部56B保留，SHA-256 `5a9ce3d687c7a0ce1972779f91857ee42b30efee0d6d9a07bd112470fb1a638b`。配方要求G8192B、原玩家xy、radius9、G1408=1、mode0、空claim/aux、有效消息Vec和空键树。预期删除记录、G1544/G1100各为4、key1176为40000、RNG不变；这仍是**未执行配方**。radius0、marker/arrival边界、NaN/饱和/绕回、mode/member/region与queue/key有无均列为后续差分目标。

23条纯Python契约已运行，覆盖手算round、零/负数/NaN/无穷、金币和key绕回、mode0/2/255、member0、mode1缺区域保持输入，以及原amount0仍追加非零mode队列。这些检查不能替代完整原件差分。

复现静态提取：`python3 reverse-engineering/scripts/trace_currency134.py`。固定profile manifest SHA-256 `952e2cd4c1fdb0bbf62cf44d6cf4f265ae15120a1572facaad23b43ff4fc51b9`，完整WAT `6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422`，SQLite `f131b4454ac1a8754f5b0417e4192efbaada6478df737e09490154c71fd340f9`。脚本末尾复核所有固定输入稳定。模块SHA-256 `e392ee41d15b9f64bd1ecbdc17df494f90ec26b79d866b4e95b6fd47792d62aa`；脚本SHA-256 `bb2c58937aff6b5584fc143ad110a4ba0c0a724445f4447343971ac3b94d6572`。未改既有pipeline/pickups/stats/builder/host/docs，未commit/push。
