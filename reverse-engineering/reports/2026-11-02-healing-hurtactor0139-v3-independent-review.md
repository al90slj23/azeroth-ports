# 当前139回血／受伤演员 v3 不同作者只读独审

结论：在默认 Human Warrior、实际非致死1076受伤、正向2123回血及rank1 Thunder／913 Leech的限定域，数值投影和输入参数保真通过。旧v2仍为“数值匹配，但源参数不一致，不接受”；本结果没有改写其身份。

独立复算9份新原件实例，42次完整2123、9次完整1076、32次完整922，共83个目标入口；另列45个前缀设置入口及64个空1775／3755消费者，合计192个直接入口。内部callee不重复计数。两批各62源／47生产文件／217条导入边；31／35个当前函数body重新绑定。原件只新增export，其他section逐字节守恒；当前原件SHA固定。

全部9份JSON明确contactFlag=1、category=0、param5=0。独立opening产出的首NPC GUID与expected／actual实际NPC432+112及控制回执一致；只读检查生成器AST和driver实际1076调用，确认两端同源消费。1076的category0路径跳过入参5的两次spelllookup读取，并在其后元数据路径覆盖local5。param5=0是受控值，不能称为重现925动态330队列索引。完整incoming history／category／callback仍未验收。

独立二进制32位顺序重算HP／cap／key22、28及23stats、owned、计时器、live32、Aura48×16、共享统计账本。913先记实际伤害统计，再按完整伤害乘1.5%计算Leech，受HP上限约束，zeroheal不记event。匹配27个Regen、28个Leech、42个damage事件、8次正crit、9个NPC死亡；83个账本快照及66行Vec48语义投影一致。G960／G1016和按reason的f64累计经过原始字节检查。

物理检查保留16356B NPC未知payload及非零背景；live/Aura的None、stale tail和Vec48非数值字节均按来源约束。158112B Game输入继承、160组背景向量守恒；30包／2093B只验证已知有序子序列。完整2077复合96B key、catalog、Deque bucket、外部448B历史、完整网络／UI包和BTree分配均未通过本批验收，不能扩大为完整2077。

1466自身不写HP，写HP的是2123／913 caller。Regen与Leech的arg3／arg4 descriptor头分别(-1,0)和(-2,-1)，仍只静态绑定caller／字面量，没有动态采样callee参数。显式时钟和delta、受控玩家中点与直接施法不等于主循环884、near1238成功调度或自然App全流程。

评审仅执行自己的独立参考函数，作者模型／builder／runner／checker和原件执行均0。首次评审脚本漏import re导致NameError，失败快照和owned终态已保留；不属于作者差异。第二次纯数值通过作为排除的重复；加强category0／param5静态保护后最终重新独算全9例。正式评审PID54002正常退出，PID／进程组均不存在，源前后SHA一致。

正式证据：`evidence/healing-hurtactor139-v3-review-20261102T122235.145962Z/review/review.json`。v2拒绝记录、原作者11件／共享3core、所有旧归档与安装包／存档均未改。没有公共登记、Git、Android或发布操作。
