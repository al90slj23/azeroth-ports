# 官方0.134.0完整经验函数与120级规格验收

新增独立 `core_spec/progression134.py` 与官方 **0.134.0 / 983346a7** 的完整函数 **4630** 完成 **2,197例对照，0差异**。新版自然等级上限为 **120**，不是旧模型的99；旧模型保持历史依据，没有仅换原件SHA后继续使用。

本轮逐例比较4字段：**u32 level1520、u32 XP1524、u32 pending2368、phase2579**。完整原4630及本次到达的属性、消息、治疗等原内部callee保持原样；独立模型只投影这4字段，没有模拟或替代原件副作用。

## 实际执行与原件身份

| 项目 | 结果 |
| --- | --- |
| 官方WASM | 90,953,762B；`2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52` |
| 完整4630 body | `[22064250,22066251)`，2,001B；`4bd68b70d90f63e0a25b63378f10a9a68adcaf275fdffd489462aa7541d1a110` |
| 研究模块 | `eaa7867fcf9ac6cbb3d124d7f51c5e899fa736d3680abbe2b4309f28fec99161` |
| 唯一变动 | export节7，原36个导出保留，新增 `research134_gain_experience → 4630` |
| 分配器 | 原导出91940，每例5000B清零G，class/race360/361=1、GUID1336=1 |
| 实例与内存 | 每32例新建，69实例；最大21,299,200B，上限32MiB |
| 宿主 | 878导入均立即throw，实际调用0次 |
| 启动 | 无隐式start节；未调用应用入口、网络、UI或存档接口 |

fixture使用 **phase2579=3**。4630没有入口phase限制，因此经验增加、升级循环、原1513属性重算、keyed-state/消息和10847/1453治疗链仍按原指令执行；只由末尾真实phase守卫跳过2159候选生成。没有用阶段设置绕过整个升级循环，也没有把该范围称为真实游戏tick验收。

## 独立规则与覆盖

按完整新WAT恢复的算术顺序：

```text
XP = wrap_u32(XP + amount)
n = u32_to_f32(level - (level != 0))
threshold = trunc_sat_u32(R85718((n*4+5)+(n*f32(.35))*n))
while level <=u119 and XP >=u threshold:
    level++, XP -= threshold, pending++   # u32 wrap
    原件执行副作用后重读XP；独立投影只重算已列数字
```

每个浮点步骤使用独立binary32最近偶数舍入。原85718的68B函数体与旧85387逐字节相同；本轮实际经过新版4630及其原callee，不把旧helper的案例数算成新版案例。

| 语料组 | 例数 |
| --- | ---: |
| `XP_wrap_and_cap_boundaries` | 72 |
| `held_XP_amount0_pending_wrap` | 384 |
| `multilevel_cumulative_boundaries` | 357 |
| `seeded_balances_levels_pending` | 1000 |
| `threshold_neighbors` | 384 |
| **合计** | **2197** |

阈值前/等于/后覆盖level0..127，包含旧99级、新119→120级，以及120/更高输入；达到上限后不再消费经验，也不把超上限输入夹回120。amount0仍可消费已有XP；XP/pending绕回、119级累计跨级边界与固定seed随机余额均包含。

## 未实现范围与复核

生产模型仍缺真实属性重算、消息、keyed-state、治疗及实际2159候选生成。`card_choice_eligible`有新原件静态守卫依据，但本轮phase3语料不验证其true分支或候选内容。phase1运行、拾取2862倍率/几何、刷怪→死亡→XP的整段时序及可玩完整一局仍未验收。完整原内部callee执行不代表这些独立功能已经完成。

独立只读复核核对原件body/非export节、角色导出、最终静态28条guards、语料分组与全部源码/产物哈希，并重新用纯Python计算2197例，0差异；没有额外执行WASM。原件身份、字段、完整调用边界见[新版静态经验链](2026-11-01-progression0134-chain.md)。

| 真实回执 | SHA-256 |
| --- | --- |
| `progression134-comparison.json` | `99e0c800f92b79765c1bdc11282f47579166e59f50e88f427aee81fadf037bb8` |
| `manifest.json` | `46de33151413854a146d565135086c1fc1efec470bb7cda6bc0c62374b7a3a87` |
| `independent-review.json` | `995107036d3e1bd2caa89c59995cbd59903d97b6cefe3abee6b96a98a61b6232` |

忽略区归档：`evidence/full0134-oracle-20261101T010259.227108Z`。相邻JSON保留逐脚本/产物SHA和运行元数据。源码哈希属于该轮实际执行版本；更早202b1d1的升级/选卡/伤害报告仍绑定其各自提交与执行源码。

```sh
python3 reverse-engineering/scripts/check_progression134_full_spec.py
```

只验收本报告列出的新版投影，不宣称整核心、Windows原生执行或联机等价。
