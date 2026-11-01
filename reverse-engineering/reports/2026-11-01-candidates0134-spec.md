# 官方0.134.0 kind0候选metadata完整函数差分

目标 **0.134.0 / 983346a7**，原件SHA256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。本次phase `full`：4126个预先落盘fixture，原件输出4126行，metadata mismatch 0，有序唯一ID覆盖 `True`，状态 `passed scoped metadata comparison`。

实际执行原完整2159及其全部可达原callee，只有export节增加批准role；没有替换内部函数、shim、app start。固定Node22.23.4、32MiB WASM上限、heap512MiB、owned进程60秒上限、原91940 allocator；全部878 host imports拒绝，实际host调用见receipt。

比较候选数量、new/upgrade/gold变体、ID、tier、owned index、kind-byte序列、gold；另比较最终四word RNG、phase2579、kind2577、counter2392。每例fresh分配8192B G，32例换instance；mode2574=1使原guard跳过世界35513，2558=0跳过6310。完整fixture、预生成独立期望、原结果、stderr、mismatches与前后source hash在`evidence/full0134-oracle-20261101T023007.496491Z`。

输入覆盖与候选实际出现统计以JSON为准；full corpus加入所有114种owned定义、全部职业byte、level/luck、3/4卡flags、owned6上限、权重/随机边界、caps、execution9/11特殊interval、blocked/banished、demonic effect/summon、tier4多kind和shuffle拒绝抽样。pilot仅用于最初两例确认真实80B tail解码，不能称为完整候选接受。

**独立实现边界**：只接受kind0 metadata/RNG/三个控制字段。80B展示payload+0..59、世界/通知表现、种子初始化、实际reroll动作、kind1/2、XP→选择组合、new能力应用、UI与完整游戏均未因此完成。原1480/1203等显示/天赋函数虽然保持原件并可能执行，其语义没有被此metadata差分独立验收。
