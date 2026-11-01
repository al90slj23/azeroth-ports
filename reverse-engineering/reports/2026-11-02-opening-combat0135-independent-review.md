# 固定135真实opening／120帧／首次选卡组合独审

**限定声明投影通过，未发现阻断。** 本次只读复核[原comparison](../evidence/opening-combat0135-oracle-20261101T154826.676203Z/comparison.json)、frozen checker/runner及其输出，没有执行原件或模型producer，也未改该批90份来源、输入或收据。

[独审receipt](../evidence/opening-combat0135-independent-review-20261101T160437.916704Z/review.json) SHA256 `2b768595711ff9f5daea0fcd718c4e963b8d2d02b652823285444000e2e96d2d`；[复核脚本](../scripts/review_opening_combat135.py)耗时4.92s。90份current/frozen来源及80份production AST闭包一致；生产模块未见直接文件/进程/eval类IO调用，原件research模块只有export section变化，代码/数据等其余section逐字相同。

完整1805行JSONL按输入动作重新推导顺序：1个case_start、constructor、opening、120个clock_control、1681个stage、case_end；stage_index/action_index与14阶段顺序无遗漏、重复或调换。外部clock的每次f32相加独立复算，select不推进clock。原进程7.20s内退出0、stderr为空，PID/PGID在复核时均不存在；完整880与native调用仍为0。

独立重比6,033,328个known record bytes、185,013个投影leaf、33,640个vector shape字段及3,362个stage identity leaf，合计恰为原6,255,343项，0差异。每份raw Game2592、App5168以及19类vector的header、真实capacity/count、完整backing长度/SHA都重新核对；world pointer保持真实26204808。没有预填128个零slot或把constructor phase0强改为1。

累计6,194,416个None cell位置仅允许已恢复的静态未写区或真实inactive backing；live NPC未初始化字、pickup+4、special padding与live32的特定未写词逐类限制。对应原件有4,110,367个非零字节，不能把它们预测为零。effects120、delayed56、hits112、active84、timed12、deadline32、secondary112及两种forward queue在全部原capture的最大count均为0；没有把非空未知payload只比count伪装为通过。非空live32最大2条按实际记录比较，3条候选则实际解引用ID/kinds/tier等语义。

首次选择前真实候选为`thunder_clap / battle_shout / bloodthirst`，输入action87确选index0，完整1072后phase1、owned80数量2；其后确有33个完整受控帧。最终level2／XP6／gold7与独立expected一致。另以独立Dijkstra遍历已冻结的独立nav输入，重新得到78,400个u16、seed39340、reachable72660，SHA256 `66afda2e7f733aebcf4f9204bbaa989b8d9310b317a1bcd6b9a23c1d65c71d32`，与每次已产生的原件distance-map摘要一致。

重要范围：原packet队列最大301条，完整payload保留在raw输出中，**其未建模payload语义没有被声称逐包验证**。本结论只覆盖声明的状态投影/known cells，不覆盖完整对象树、heap所有权、UI/传输/存档或整局。它仍是单human warrior／seed0／navigation False／静止标称12秒的固定135研究域：模型使用预解析独立world，原件使用合法历史snapshot，时间由显式外部调度推进。raw451资产入口是另一份生产层收据，本复核不将其加算为第二个原件case；136/137也不获得动态通过。

机器可读结论见[review summary](2026-11-02-opening-combat0135-independent-review.json)。
