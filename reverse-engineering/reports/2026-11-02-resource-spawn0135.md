# 0.135.1 G2444 资源生成分支

已恢复独立 `resource_spawn135.py`，完整原函数 1417 ×12、947 ×52，共 64 个 fresh 用例、196 个完整 169 创建包（32,043B），0 差异。全部 58 项源码闭包、输入与真实 451 资产 world 的哈希前后稳定。原件固定 **0.135.1 / 90898d5e3**，SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。

这是组件验收：原件 fresh 实例接收独立 opening 和真实地形的类型化输入，显式设置约 40 秒后单次执行完整 947。模型按独立 opening → ordinary → resource 顺序生成期望；没有替换原函数，没有读取原件内存快照。**0 full880 帧、0 自然 40 秒整局验收。**

## 规则与所有权

- `now >= G2444` 先写 `G2444 = f32(now+45)`；统计活动 pickup56 前缀中 `kind+8 ∈ [3,5]` 的合计，忽略 marker。达到 2 个时，资源子分支不抽 RNG、不查 world；完整947此前的 ordinary 分支仍消费共享 RNG、查询 world 并可创建 NPC。
- 未达上限，xoshiro128++ 输出乘 3；低位 `(product & 0xc0000000) == 0xc0000000` 时重抽，高 32 位选 kind3/4/5。**1417 的 amount 是这次抽取后的 state[0]**，之后 13516 才继续改共享 RNG。
- 13516 使用真实 world、半径 15..40；1417 再执行地图半径减 2 的夹取和最终高度查询。覆盖 5 例种类 RNG 重抽、2 例真实 world 连续 12 次拒绝后的第 13 次无条件位置回退。
- kind3/4/5 分别为 visual 9006/9007/9008、display 5931/5995/5991，scale1、对象 kind21=5、flags9=0。1821 按真实 GUID/counter、朝向 RNG 顺序创建；完整 169 字节与原件一致，消息序号保持。
- 56B 写集合为 `+0` 和 `+8..55`；`+4` 未写。aux Vec 固定 `(capacity0,pointer8,count0)`。完整容量、旧 inactive 尾部、已知旧字节和 None 遮罩均保留；增长后的真实未写字节继续 None。

## 接口

`ResourceSpawnInput135(zone, now_bits, next_resource2444_bits, player_xyz_bits, velocity_xy, rng_words, counter, pickups)` → `step_resource_spawn135(value, world)`。

返回 status、下一 G2444、完整 `pickups: OpeningVector135(stride56, storage, count)`、共享 RNG/counter、creates（含完整169）、种类/amount/位置与分项 draw 计数。调用方在 ordinary947 后按顺序回填这些字段。

单独 producer：`produce_resource_pickup135(ResourcePickupInput135(zone, kind, amount, position_bits, now_bits, rng_words, counter, pickups), world)`。资源种类仅准入 3..5；world 必须明确携带 primary 状态。

## 验证边界

原件函数和全部非 export 段逐字节保持。每例 fresh，32MiB 内存上限，峰值 20,578,304B；878 项 host import 全拒绝，实际 0 调用；所有调用前后 stack 复原。expected-first、源码闭包冻结、owned 60 秒 deadline；PID/PGID 6261 已消失，exit0。精确比较 122,748 个已知值；71,736 个真实未定义字节保持显式未知，不冒称逐字节全部已知。

待验收：其他 due947 事件/Boss/elite；资源 3..5 的拾取和实际效果；1417 其他种类；primary 存在但 nearest miss 的原件低地址 `kind+116` 读取。当前真实 451 world 的 primary 为空，该异常支路明确 pending。此组只覆盖 Elwynn 的实际 world，未新增其他地图动态验收。

## 冻结与证据

生产源码 SHA：`f142c219f60abc3b69ba645ef2fd87adec7728a0e034069e524d06b15c0b2aa3`。

- 收据：`/Volumes/RuiRui4TB/CloudBackup/Mac/code/github/al90slj23/azeroth-ports/reverse-engineering/evidence/full0135-oracle-20261101T174727.123299Z/resource-spawn135-comparison.json`
- 收据 SHA：`85b5c088e80e33d059b880275e59aa6f2a3613344fc887f2886566130fdde005`
- 完整输入、期望、原件输出、差异、运行账本和源码快照均在同一 4T 目录。
- 静态追踪通过只读 SQLite 索引定位 947、1417、13516、1821、29631、23181、26970、50798、65337；没有全读 1.3GB WAT，报告不复制原件完整函数。
- 运行：`PYTHONDONTWRITEBYTECODE=1 python3 reverse-engineering/scripts/check_resource_spawn135.py --phase full`。

机器可接续的函数身份、源码哈希和证据绝对路径见同名 JSON。

[只读独审](2026-11-02-resource-spawn0135-independent-review.md)已复核完整196包、58份冻结/当前源码、None写掩码、独立RNG及资源字段；独审收据SHA `4b28ac7f2c381a1d12b854eb70708e6d3f24b33e7da91000df1200cb3ec48347`。world为既有独立451资产查询文件手工装入fresh原件的查询等价布局，未执行原件World构造器；该组件仍不代表自然40秒或完整880验收。
