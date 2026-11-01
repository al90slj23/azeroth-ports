# 0.135.1 ordinary placement 独立只读复核

最终 [052411 receipt](../evidence/full0135-oracle-20261101T052411.434992Z/ordinary-placement135-comparison.json) 在声明范围内通过：**924 inputs**（396次完整1417、528次完整914死亡路径）。从冻结生产模型重新计算全部预期，全部吻合；重新比较既有原件结果也无差异。审查未运行原件或修改作者源。

1,268条pickup共71,008字节全部严格比较。arrival+4为明确的prior A5字词，1,268处均按0xa5a5a5a5比较，未使用None、位掩码或NaN放宽。reward/entity RNG、counter、message sequence、kill cost，以及死亡插值后的XYZ、两端点、U340/U344均保留在比较范围。

原件SHA、21源快照及全部artifact哈希吻合，当前无源码漂移；除export7外所有WASM section逐字节保持原件，新增914/1417角色及body SHA吻合。12地图中心/radius也与实际初始data段逐词核对。最初924清单遗漏包入口和upgrade_values，作者补齐后重跑，最终以052411为准，先前924/876不叠加。

几何规则核对了pre-hit记录插值、XP死亡位置与coin先+.8再单独clamp、limit=max(1,radius-2)、最终flat/base V116高度。独立6个负例确认缺少世界声明、terrain/navigation存在、畸形/已死记录、非有限高度会拒绝。

本批不证明实际地形或寻路、非空现有pickup的merge/cap、任意Boss/elite死亡、完整combat/UI/包/account行为。完整独立证据与复算脚本见 [review.json](../evidence/ordinary-placement0135-independent-review-20261101T052541.411145Z/review.json)。
