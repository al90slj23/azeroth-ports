# 0.135.1 可选扩展的默认行为回归

headless组合增加可选cast dispatch及destination_slots完整backing接口后，保留旧调用的默认行为。两份新收据通过，输入连同expected与对应旧批逐字节一致，原结果也逐字节一致；不作为新增语义覆盖相加。

| 回归 | 新收据 | 结果 |
|---|---|---|
| 1076/1754默认施法 | [055718](../evidence/full0135-oracle-20261101T055718.108039Z/owned-cast135-comparison.json) | 639组、5924阶段、4923次accepted hit，0差异；33源快照。 |
| 947/8751/heading默认生成 | [061408](../evidence/full0135-oracle-20261101T061408.239242Z/spawn-motion135-comparison.json) | 5068组、1299237个比较词，0差异；26源快照。 |

原件只增export、完整callee保留，878host imports拒绝且实际0次；无start、网络或存档。完整SHA和旧收据映射见[JSON](2026-11-01-default-extension0135-regression.json)。这证明新增可选接口未破坏已有默认输入域；新注入消费者及实际非零backing域由独立headless收据另验。

639批的basic80是G1256槽中的effect0隔离fixture，不是1560真实racial；真实racial由151构造、720施法和headless分别验证。5068批保留原float NaN分类政策，未知地形/其它947事件仍未覆盖。旧收据及其源码快照原样保留。
