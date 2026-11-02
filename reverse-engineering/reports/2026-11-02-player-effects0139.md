# 0.139.0：Human Perception与48格Aura

新player_effects139纯模块已在联合player-update批通过：5种节拍、155次完整2123，保留真实1238与922／1542／1173内部调用；5次实际Perception成功，6次live到期重算。默认0.125步长在0.5秒触发racial，live8.value+12=.15令damage1.03→1.18；1秒1020到期、14.5秒Perception到期，属性／Aura／键恢复一致。0.1步长第五次cooldown仍微正，第六次才触发，未强行改CD。当前等待联合批异作者独审，不能另将155调用重复算本报告覆盖。

922 Human定义5891892为exec9／effect8／spell20600。先真实27754→36518→20123按alive标记、插值XY和有序f32距离平方≤900查询NPC；有目标才发self306、保留／替换owner0同spell记录、追加live8，再1542及1173。新live记录+16从未初始化scratch复制，作为‘写入未知’保留None；value在+12。RNG不因这些步骤消耗。racial cooldown与308／309由调用方1238负责。

1173输出是48格×16B，不是48B：active为(tag1,spell,expiry,count)，inactive只写tag0，其他12B继续None。active live12的+12／+16不作为数值读取；live8仅读实际+12。前32格为正Aura，当前无owned effect12冷却Aura源；47..94写spell，95..100每格4bit flags（正Aura9／后16格8），113..124编码每组四个min(stack,255)-1。旧ready状态下只改发生变化的逻辑字段，依然重新生产48格vector，物理指针不预测。

最初8帧pilot其余状态全一致，唯我错误复用顺劈encoder导致self306带mask2＋packed0。原批1包差异保留；已按当前10490 target variant2独立编码mask0、不带显式packed target，后继fresh8及正式155均匹配。正式5个20B self306与调用方10个308／309构成15条已知有序消息240B；完整展示消息流未宣称还原。

联合比较中live8172已知／12308 None，Aura32880已知／90000 None，都是byte occurrence非完整覆盖率；大量实际非零None未反填。源码在正式前冻结；额外10个函数的完整WASM／索引WAT静态绑定在正式后完成，清楚标记为补充，不倒写成预运行来源证明。

当前仅Human／sourceGUID0、空七类stat/proc来源、live12/1020与8/20600、无owned effect12 Aura源。其他buff、非空modifiers、冷却Aura、直接no-target／精确半径边界尚无本批独立原件矩阵；自然App／Rc／资源bootstrap／AI／输入／主循环／原生Windows和完整游戏仍未知。

[机器报告](2026-11-02-player-effects0139.json)提供联合收据、失败与未知边界。
