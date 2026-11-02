# 当前139 Kobold/Wolf 普通近战：不同作者只读复核

通过限定范围：4个fresh实例，4次完整952、40次完整925、12次完整913，共56个目标入口；12次2945/1600/1108为setup，68direct。103源/87production/418边及169个当前函数体、静态数据和只增export的完整模块重新绑定。两处声明重叠的元数据另以只读补充检查完全相等。

独参先于作者冻结，直接从当前925/913/5719/1076/40215等体与两条72B定义恢复。Young Wolf为ptr5830976/entry601/display165，与Kobold ptr5830904/entry600/display26的尺寸、生命、攻速、移动速均按真实来源构造。两者XP56=1/cost60=1；913从Unit+284获取每个定义，不能以仅替换名字冒充不同敌人逻辑。

显式跳时钟到30.1秒的真实完整952，每组从初始4NPC再生成3NPC，保留全部7NPC；seed0/5各实际生成1Wolf，seed1/8是无Wolf对照。玩家随后跟随真实Wolf或首Kobold的位置，未改NPC位置/HP/状态、随机数、CD或禁用racial。不是自然运行30秒或完整主循环。

40次925的完整有序包、真实地形/四张非均匀BFS、105条direct-clear运动路径、23次非致死普通近战与实际英文history名称/分类0一致；Young Wolf/Kobold英名来自当前English表enemy.601/600，fallback也与定义字段相符。四次死亡在1.0秒保留、1.25秒严格超过1.2才回收，完整432B稳定前移、capacity与staleTail保持。没有验证blocked-flow、远程、精英、Boss、护盾/修饰来源或致死玩家分支。

12次direct913仅basic0/抑制flag1和owned cleave845/flag0，包括8个实际伤害/Leech、4死亡和4次already-dead无动作守卫。critical标记作为直接函数实参，不会再把提供的amount数值乘二。奖励XP/金币、f64伤害与共享G960/G1016/语义账本、Vec48 Leech投影一致。Thunder/Demo身份虽有静态字段，本批动态验收为0。

154个已知包9277B是170个实测包9801B的有序范围；其中925与spawn包完整，913余16包524B仍未完整重建。不能宣称完整UI/网络消息流。原初4NPC的6912B逐字节保留；52次输入的整Game仅允许时钟/玩家动作134784B继承匹配；179712B物理NPC回放与known/None保持，146140个physical None中130328个实际非零，从未以输出填充独参。两个Rune和全部背景向量保持。

原件PID43173正常结束、进程组消失；不同作者只读复核PID11343正常结束、进程组消失（42.59秒），0作者程序/0原件执行。最初只读脚本缺ast导入的NameError失败保留；补齐后完整匹配，再加固冻结helper整表SHA与真实English数据绑定后最终完整复核。7个先验源+2报告原SHA不动，原doubleLF不格式化覆盖。旧pilot和旧通过均不转计。

完整2077物理键/目录/桶/历史、整个输出Game与整堆、App/WorldRc/externref启动、其他普通family、完整884/完整一局、Windows整应用与联机均不由本批完成。资源守恒依冻结runner的范围hash与回执，不是独审重新执行或独立保留全部原始资源前后对。
