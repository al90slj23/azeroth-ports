# 0.139 伤害913：异作者只读复核

**限定范围通过。** 独立重算正式批 80 个受控案例、125 次完整原件913调用，与保存的期待和实际输出均无差异。审查期间未执行作者生产模块、checker、builder、原件或 Windows EXE，也未沿用旧版本通过结果。

- 独立算术仅用 Python 标准库 `struct`，每一步按 binary32 舍入；核对状态加成顺序、严格时间边界、伤害系别位掩码与 U372、U416/U420、kind2 关联、NaN 最低伤害1、HP 减法及 f32→f64 累计。
- 118 次接受、5 次阶段跳过、1 次 marker1 跳过、1 次目标缺失。125 次操作涉及的完整432 B单位记录累计55,296 B均比较；除目标HP288外没有其他单位字节变化。四 RNG 字与 G984 原始f64位值逐操作核对。
- 独立重解析真实139原件与只增私有导出的模块：所有非export段逐字节相同，实际277个直接调用点、86个不同callee均保留。函数913 ABI 为 `(i32,i64,f32,i32,i32,i32,i32) -> void`；真实allocator93344 ABI另核。
- 882个真实导入名称逐项一致，全部deny，实际host调用0。285个栈守卫均恢复1048576；峰值20,709,376 B，原件进程24922退出0且PID/PGID均消失。
- 源闭包12文件/16边以独立AST解析核对，包含包入口和upgrade_values。输入/期待与模块按作者prepared收据绑定；额外原始输出哈希按本次读取固定，不冒称预运行冻结。
- NPC声明72 B由真实WASM初始内存与active data segments重建核对，名称Kobold Vermin、地址5830904；Windows数值尾45 B唯一位于120664736，仅作静态字节参照。

G1972始终为0，静态分支因此跳过新的69550 pop helper；不接受非空proc的生产或运行行为。7个kind64=0/U68=0输入只是受控数值fixture，不代表合法自然构造或timer owner已恢复。完整8192 B Game逐调用保留为观察，未将所有统计、消息和视觉分配冒充独立预测。8个negative guard仅是作者模型检查；早期prepare-only与4案例/5调用pilot均不累计到正式80/125。

角色map是审查者先前工作的既有源身份依赖，本次不对该map重复记独立恢复。死亡、经验、战利品、非空技能/装备/proc、完整一局与联机仍在本次通过范围之外。

最终独审证据：`evidence/combat139-independent-review-20261102T015228.747722Z/review.json`，SHA `a51863d179b18bbf4e23f4b2db2844274349b5a1a25eb140be0c89bb54be9d0e`。

独审脚本 SHA `158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9`；owned收据 SHA `983fc7a10b23bdfea0e9e5ca8b52e327fec57df63ce263e43bd9be5a909d5efd`。

机器报告：`2026-11-02-combat0139-independent-review.json`，SHA `84d71d42f247fbe6b1e92280be0788efeb82a705ce5d251053fe8baa3770f47e`。
