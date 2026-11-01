# 0.135.1 资源增益到期与玩家更新前缀

固定 **0.135.1 / 90898d5e3（9 字节）**，8 字节 `0898d5e3` 仅为历史别名。新独立组件恢复资源 kind0（23451/23505）与唯一正 kind8 的 2088 到期→1512→1202→回血前缀。fresh **38 组、56 次完整原 2088、0 差异**；尚待独立只读审阅。

最终[差分收据](../evidence/resource-player0135-oracle-20261101T214934.226082Z/comparison.json) SHA256 `82719c31ea3de180d1a4b0c036d1a6764bd1518f3a1cdea17e3a627b6d85024d`。37 源、124 本地 import 边均在 expected 之前冻结并首尾一致。原件所有 callee 保持原字节，私有模块只新增 2088 与只读 global0 导出。

## 可组合接口

`prepare_resource_player_update135(level, context, now_bits, dt_bits, last_hit_bits, periodic_input=(), explicit_other_sources_absent=True)` 返回更新后的 level/context、到期 spell、regen 请求/实际回血、事件、226 packets 与 pending 边界。两个关键字参数必须由调用者显式提供，默认会拒绝。

LevelCycleState 是 HP、23 派生属性、时间与 RNG 的唯一所有者；MixedResourceContext135 持有完整 physical live32、Aura48、GUID、速度 action1644 与 App notification id14340336。每次调用先验证语义 live 与 physical live 属于同一份状态；返回时统一更新，不增加 HP 或 RNG 副本，也不重置 App 通知序号。

## 已恢复规则

- 原 2088 函数 L134..171：至少一条 `now >= expiry` 才触发 dirty。单独 NaN 不触发；触发后按严格 `now < expiry` 稳定保留，因此 NaN 会连带移除。
- 每次保留复制完整 32 字节，原容量和 inactive 尾部保持。kind0 +12..19、kind8 +16..19 的 None 不被读取成数值、不填零；本批还严格核对这些原始输入 poison 字节在原件中保留。
- L935..938：先完整 1512 数值重算，再完整 1202。1512 内部若速度变化超过原阈值，生成完整 226（packed GUID、旧 action1644、新速度）并使 action 按 u32 回绕；随后 Aura48 缓存及最多 66 个 pending keyed 字段按原规则更新。
- L940..1032：先 clamp 1448=minnum(1444,1448)，按 gate387>4 减半；距上次命中至少 3 秒才加 maxHP×1620。按原 f32 次序计算 dt×regen×half；仅 oldHP<maxHP 时修改 HP 与 keys22/28。
- 原 1453 及后续 1076 都真实执行。独立模型到 prefix 结束即返回；1453 的 healaccount/presentation/statistics 未独立重建，1076 的实际技能调度由组合层后续处理。

## 验证范围与执行边界

覆盖 10/15 秒严格边界、6 种资源/Battle 排列、重复 kind0、NaN 单独与连带移除、正 kind8 到期、缓存 initialized bit、HP 上下界与 gate、有限 dt、3 秒 regen 条件和 226 序号回绕。共 49 次 dirty 重算，明确到期 spell 23451×35、23505×13、6673×7；35 个唯一速度226全部字节相符。7 个拒绝检查只算纯模型边界，不算原件调用。

比较 23,309 个已知值与 30,416 个明确物理 None 字节；完整 live backing、48-slot Aura、全部 pending keyed fields、HP/pools/RNG/速度/counters 均核对。Aura inactive tag0 以外的 12 字节仍是分配器未知值，未伪造为已知零。

本批是显式手工 Game8192/World128 输入。learned-owned 为空，真实 cleave80 的 remaining 与 class prelude timer 为 Infinity，因此完整 1076 会返回且不施法；不是自然开局、完整施法或完整游戏验证。每组独立新实例，冷 App notification id1 由 Node 只读核对，没有写回重置。原 1453 自然把 locale Once0→3，相关原始字节保留，不能据此宣称 locale 生产者已独立恢复。

PID/PGID75587，exit0，pid/pgid 均缺失，3.149 秒/60 秒；实际0 host、878 deny、峰值20,578,304字节/32MiB、输出1,207,982字节/4MiB。221 次 stack guard（allocator165、2088×56）全部恢复。无 App start、Windows EXE、网络、用户存档或原始内存快照执行。

5组/11次的 pilot 原目录保留，不累计到最终38/56。现有 player_update135、racial_cast、headless、derived、death、mixed 及封装/安装包/存档均未改动。非零 periodic、其它 live family、护盾/条件 owner、非空外部 stat/aura/proc、完整1453日志和1076调度仍 Pending。

源码：`reconstruction/core_spec/resource_player_update135.py` SHA256 `6b5fc34afc4049347320767ff55339d6aa6f12d66fd866e5709b12441c868ea5`。复现：`python3 scripts/check_resource_player135.py --phase full`（会创建新的受控原件差分目录）。

## 独立只读复核

[独审](2026-11-02-resource-player0135-independent-review.md)通过，收据SHA `8d3159228fe880c3f9153b08a3e36adb8226bd7c5c82ca309b5e8f0429b5de10`。38组／56次完整2088的23309已知值、30416物理None、49次属性／Aura重算及35条实际226均复核；未运行原件、模型或checker。3秒边界旧语料的derived1620均为0，非零附加回血仍待新源验证；NaN在1512与1202的不同过滤规则只作静态／初始fixture证据，不冒称新动态域通过。选卡1020保护与符文共存、实际1076调度和1453输出仍待接线。
