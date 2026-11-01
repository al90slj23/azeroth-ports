# 0.138.0 damage913 独立只读审阅

固定原件 **0.138.0 / 382771e6c（9 字节）**。对 fresh 80 组、125 次完整原 913 调用的有限非致死数值投影审阅通过；本审阅新增原件调用、模型执行和完整游戏帧均为 **0**。

最终[审阅收据](../evidence/combat0138-independent-review-20261101T211907.648414Z/review.json) SHA256 `a4098947aa8d671dfd757e4eeda026a8e1518f93c35b8966a5921cf78ee3dd94`，绑定[原差分收据](../evidence/combat0138-oracle-20261101T205616.629599Z/comparison.json) SHA256 `282e38ed4d2f14e87a12568cc9f0dbcca81c9641f63464936c9c08047278b7fa`。原 4 组 pilot 和先前只读审阅保留，不累计到 80/125。

## 独立复核

- 不导入生产模型、builder 或 checker，仅用标准库解析既存输入、原件输出、源 AST、WASM section 和有界 WAT 窗口。独立解释原 913 指令时序，在每次 add/mul/sub 后按 f32 舍入，再以真实 f64 累计 Game+984。
- 125 次全部复算相符：118 次接受非致死伤害、5 次 phase 拒绝、1 次死亡 marker 拒绝、1 次找不到 GUID；其中 17 次能区分真实 f64 累计与错误的 f32 累计，3 次实际应用 U372 的 school 加成。
- 逐次比较完整 432 字节单位记录，累计 **55,296 字节**；唯一允许单位写入为目标 HP+288..291。四个 RNG 字和 Game+984 的 64 位表示也逐次核对。
- 11 源、4 生产模块、14 条本地导入边均闭合；首尾与冻结快照 SHA 一致。生产 AST 无直接文件/进程/动态执行接口。原 expected 写盘行 68 位于原件 Popen 行 80 之前，prepared artifact SHA 与现有文件一致。
- 原与私有模块只有 export section7 改动，新增 damage913 与 global0 只读导出；所有原代码、数据和 callee 保持字节一致。实际 913 签名为 `(i32,i64,f32,i32,i32,i32,i32)->()`，914 的六 i32 签名没有被误当入口。
- 从只读 0444 SQLite 主键索引 seek 实际 913/68536，保存逐指令窗口与查询结果；另外定点核 137 的旧 helper68459。没有全文读取 1.32GB WAT。68536 是四参数 ABI，旧 68459 是两参数，不能据静态对应外推其非空行为。
- 125 份 Game8192 原始记录均保存并核对顺序、总伤害、RNG、单位 Vec header、phase、时钟和 **G1972=0**；其余 Game 字节和队列 payload 仍属于原件观察。

## 执行与身份边界

原执行 PID/PGID 81053，exit0，首尾缺失终态已读回；3.725 秒小于 60 秒预算。实际 0 host、878 deny、峰值 20,643,840 字节小于 32MiB，stdout/raw observation 各小于 4MiB。285 次 stack guard 均恢复 1MiB，其中 allocator160、damage125；构建器 validator 与 profile 进程亦有独立退出证据。

再次读取实际 WASM 数据中的版本与 9 字节 build，并核 Windows branding 指令的既存原始字节。Windows EXE 仅做完整 SHA 与 **一份声明的 45 字节 scalar tail** 静态匹配；未运行 EXE，也未验收其伤害函数地址、ABI、Game/Unit 布局或玩法。

## 明确保留的未知项

7 组 U64=0 / U68=0 的 phase fixture 只覆盖未消费 timer/destructor 的数值分支，不能证明完整 NPC owner 或 constructor 合法。非空 G1972 的新 68536 行为、致死/经验/掉落、装备/法术/proc 非空生产者、非零继承 context、Boss/kind3 接受分支、统计/网络/UI payload、完整 Game/880 自然帧及 Windows 运行仍未验收。本批不是完整游戏重建或 IEEE754 穷举证明。

复现：`python3 scripts/review_combat138.py`，仅重读已有证据并写新的专属审阅收据。审阅器 SHA256 `67282c72c394c9aaeca74d3500657f037db6562bf604cc2d48f4f26cc545901c`。
