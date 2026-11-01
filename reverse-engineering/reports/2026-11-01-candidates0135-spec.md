# 官方0.135.1 kind0候选metadata完整函数差分

目标 **0.135.1 / 0898d5e3**，原件SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。本次phase `full`：4126个预先落盘fixture，原件输出4126行，metadata mismatch 0，有序唯一ID覆盖 `True`，状态 `passed scoped metadata comparison`。

实际执行原完整2159及其全部可达原callee，只有export节增加批准role；没有替换内部函数、shim、app start。固定Node22.23.4、32MiB WASM上限、heap512MiB、owned进程60秒上限、原91941 allocator；全部878 host imports拒绝，实际host调用见receipt。

比较候选数量、new/upgrade/gold变体、ID、tier、owned index、kind-byte序列、gold；另比较最终四word RNG、phase2587、kind2585、counter2400。每例fresh分配8192B G，32例换instance；mode2582=1使原guard跳过世界35514，2566=0跳过6310。完整fixture、预生成独立期望、原结果、stderr、mismatches与前后source hash在`evidence/full0135-oracle-20261101T034357.816011Z`。

输入覆盖与候选实际出现统计以JSON为准；full corpus加入所有114种owned定义、全部职业byte、level/luck、3/4卡flags、owned6上限、权重/随机边界、caps、execution9/11特殊interval、blocked/banished、demonic effect/summon、tier4多kind和shuffle拒绝抽样。pilot仅用于最初两例确认真实80B tail解码，不能称为完整候选接受。

**独立实现边界**：只接受kind0 metadata/RNG/三个控制字段。80B展示payload+0..59、世界/通知表现、种子初始化、实际reroll动作、kind1/2、XP→选择组合、new能力应用、UI与完整游戏均未因此完成。原1480/1203等显示/天赋函数虽然保持原件并可能执行，其语义没有被此metadata差分独立验收。

补充：复用模型中少数docstring仍保留134的helper编号；本版真实调用为29737/27376/32653、world35514，不能据旧标签定位。生产逻辑与原始新结果均已冻结，不将旧版计数转记新版。

独立只读复核重新生成全部输入/期望并比对持久原件结果，源码快照、原件及export-only模块绑定通过；复核未重跑WASM，收据与SHA见相邻JSON。
