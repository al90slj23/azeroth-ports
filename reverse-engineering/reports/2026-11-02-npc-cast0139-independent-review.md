# 0.139 同一Game：自然四NPC接顺劈斩独立复核

当前声明组件通过。8组healthy-v2状态恢复、32次完整5719(None)后接20次完整922，全部声明输出由独立参考重新计算，复核未执行作者生产代码、检查器、构建器或原件。

先从当前139原始class/race数据重算23项默认属性、80B owned记录和构造PCG；位置期望只读raw资产生成的canonical地形。四个NPC严格按“8740位置→同一RNG的yaw/jitter→下一NPC”生成，再把同一组canonical432B记录送入施法参考。施法参考直接读取byte/None，未知值一经真正消费就失败，没有构建A5、5A或零载体。仅HP288..291被写入。

52个阶段四槽共58824个known字节完全一致，31032个None不填充，实际观察14664个未知非零字节仍保留未知。20次施法累计7740个未知字节逐次守恒，27次selected hit、4词RNG、f64累计伤害、三spell-set及owned80全一致。19条完整306消息共566B独立重算，并核target顺序；32条新NPC169单列。其他592/HP169消息和完整Game物理分配仍是观察。

同状态连续性另逐字节检查：32次NPC的2592B before/after逐次相接，81536个非声明写入字节守恒；首个cast除显式XYZ/phase的13B外继承20632B，后续cast完整继承31104B。每次RNG、f64 total、spell-set count及同一unit vector均接续前一步。不是把两份独立结果拼成同状态结论。

36来源、26生产文件、完整AST的导入边及7作者件逐项核SHA；原件仅增加5719、922、stack三个导出，其他段逐字节相同。原件runner报告882导入全拒绝、0host、70次栈检查、8次快照恢复，其owned PID33723已退出且PID/PGID消失。独审PID73296也exit0并消失，旧两次只读复核收据保留。

范围清楚保留：这批没有重新执行1600、6786、1108，没有恢复自然App/profile。靠近第一或第二NPC的位置移动、phase1是受控输入；四组gentle重复场景显式把owned倍率改为0.1，默认第二击致死仍待恢复。原件前置空G2032/G2056/G1972由runner核对，通用来源owner生产及callback不由本组件闭合。作者两种私有carrier只是模型自检，不加原件覆盖。

作者comparison没有包含post-run stdout/runtime/terminal的散列；独审按当前实际字节另行固定as-read，不能称事后补成原批冻结证明。Pythonopen审计也不是OS系统调用审计。

最终独审收据：`evidence/npc-cast139-independent-review-20261102T052248.233724Z/review.json`，SHAe6146c4a257492ca9599b54029ac46e07f2cd11da9b853d174279520aae88074。完整游戏、默认死亡奖励、AI/输入/移动和Windows执行仍未验收。
