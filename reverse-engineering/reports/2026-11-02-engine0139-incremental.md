# 0.139.0 / f79c5e2b4 静态增量迁移检查

本轮完成官方 0.139 原件的完整静态索引、30 个主要入口的源身份映射，以及 143 行明确字段的数据比较。**尚未执行 0.139 原件或独立游戏模型，没有把 0.138 或 0.135 的通过结果计入 0.139。**

- WASM：`71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299`，92,511,151 B。
- Windows EXE：`0e8e314df4d78ab211b1bef5c48d78d713ed64260894af342f998d298d74d274`，150,595,584 B；实际消费的 9 B build 与 Web 一致，由独立身份 sidecar 绑定。
- 全静态索引：177,101 定义函数、882 导入；WABT 完整验证、SQLite integrity 均通过，耗时 70.56s。WAT 1,372,908,199 B，DB 655,261,696 B，均在 4T。

## 入口映射

先绑定完整字节或完整指令结构相同的函数，再沿同一指令位置的直接调用、唯一精确调用上下文和实际 owner 调用图定位。补充的入口前缀保留局部变量、内存偏移和控制流。没有按相同编号或相似度阈值认领身份。30 个入口的参数/返回类型均一致；11 个在调用编号和静态地址归一后整体相同，19 个仍有差异。

| 角色 | 0.138 | 0.139 | 原件 body B 变化 | 整体归一相同 |
|---|---:|---:|---:|---|
| player | 2086 | 2123 | -6 | 否 |
| extra | 917 | 924 | +0 | 否 |
| owned_effects | 973 | 983 | -37 | 否 |
| hits | 1754 | 1775 | +0 | 是 |
| area | 3756 | 3755 | +0 | 是 |
| effects | 915 | 920 | +3 | 是 |
| deadline | 38039 | 38553 | +0 | 是 |
| secondary | 2596 | 2621 | +0 | 是 |
| ai | 919 | 925 | +2 | 否 |
| collect | 2862 | 2890 | +0 | 是 |
| claims | 2567 | 2584 | +0 | 是 |
| spawn | 946 | 952 | +21 | 否 |
| special | 2359 | 2372 | +2 | 否 |
| terminal | 49086 | 49961 | +0 | 是 |
| constructor | 1571 | 1600 | +2 | 否 |
| cached_world_construct | 6760 | 6786 | +113 | 否 |
| opening | 1087 | 1108 | +2 | 否 |
| stats | 1512 | 1542 | -11 | 否 |
| owned_tick | 1232 | 1238 | +0 | 是 |
| cast | 916 | 922 | +37 | 否 |
| player_aura | 1155 | 1173 | -20 | 否 |
| select_ability | 1072 | 1093 | -15 | 否 |
| outgoing_damage | 913 | 913 | +1864 | 否 |
| incoming_damage | 1057 | 1076 | +147 | 否 |
| proc_event | 980 | 994 | +0 | 是 |
| fatal_transition | 5613 | 5648 | +0 | 否 |
| network_decode | 965 | 973 | +100 | 否 |
| player_motion | 2327 | 2346 | +6 | 否 |
| network_peer_route_helper | 2077 | 2105 | +0 | 是 |
| application_tick | 880 | 884 | +29 | 否 |

App884 是同时调用八个已独立定位阶段入口的唯一相同 ABI caller；其唯一连续 14 调用窗口为：

`2123 → 924 → 983 → 1775 → 3755 → 920 → 38553 → 2621 → 925 → 2890 → 2584 → 952 → 2372 → 49961`

窗口位于真实 WAT 175221–175257 行。旧 App880 的对应阶段在其原件中单独核过；这只绑定该实际分支，不代表完整 App、UI 或渲染系统已恢复。

## 数据与浏览器桥接

- 114×88 B 技能记录：展开偏移 12/20/28/36 的四个真实指针/长度切片，其余字节原样逐字比较，全部相同。新表基址 5882740；构造1600 中实际 base、88 B stride、10032 B 上限共同绑定，未用地址平移推断。
- 9 职业的起始技能、HP、Armor；8 种族的技能 ID/effect tag/执行类型；12 区域的 ID、XY 和 field116，所列字段全部相同。共 143/143 行相同。完整 raw 记录保留，未把未解码的其他嵌套结构计为相同。
- 新增四个 Date 导入：getFullYear、getTimezoneOffset、new Date(value)、new Date(year,month,day)。其余 878 个导入未删除，签名未变。
- 官方 wenilla JS 删除这四个新增 wrapper 与生成器的 closure shim_idx 注释后，其余字节完全相同。它们在游戏中的实际用途尚未证明。
- Windows 只作真实版本消费和所列数值字节出现位置的静态参照；未执行 EXE，未宣称恢复其 ABI。

## 影响与下一步

伤害入口旧913→新913、受伤1057→1076 已由已绑定 parent 的实际调用位置定位；其中 outgoing body 增加1864 B、incoming 增加147 B，需要重新恢复并差分。技能静态声明相同，也不能跳过 cast922、stats1542 等变化体。联机965→973、移动2327→2346 与 peer helper2077→2105 已定位，协议/ECS对象更新/网络互通仍需逐项验证。

建议顺序为：139伤害新组件 → 139构造与关键状态 → 139完整一局连续差分；联机链单列恢复。历史135/138原件、实现和通过记录保持独立。

## 证据与边界

- 完整 profile：`evidence/wasm0139-profile-20261102T012426.951871Z/manifest.json`，SHA `40a35af3cb76c533f2b23fb43104ea9480b9993f9c84a1cb8af00ccc3e02661f`。
- 最终角色 map：`evidence/engine139-refined-static-20261102T013743.612949Z/mapping.json`，SHA `7b41961bce7f45e74a8d2a24305cf84d0d64f2f2d739c723b1e445af208c40f0`。
- 数据/JS差异：`evidence/engine139-data-delta-20261102T014028.095422Z/delta.json`，SHA `c2b0fee13ad520de0cb4feebc3a003ade8e9be339f6d9c0daf3e6db639f9c4be`。
- 机器可读汇总：`2026-11-02-engine0139-incremental.json`，SHA `4762d8532f3882a4555c89b5eb3b9e059967ae6c3f33275aba82f65a5e6b41fa`。

所有静态子进程均有 deadline、专属 PID/PGID 和退出收据；最终 PID/PGID 均已消失。首次 map 的 duplicate-key TypeError 和较小预算的早期 baseline 中断保留，不改写为成功。源导入闭包另作 as-read 绑定，不冒充早期收据已冻结未列出的依赖。

本轮没有修改旧版本生产模块、原件 reader、公共版本登记、现有安装包或存档，也没有新增任何游戏行为验收。
