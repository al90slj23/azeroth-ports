# 当前139默认自动攻击：不同作者只读独审

结论：默认Human Warrior／真实首张新Thunder的4个受控场景，48次完整1238和48次完整2123共96个目标入口，独立重算通过。另有3个实际925移动来源、3个warmup2123、3个输入一致1076及20个前缀入口，合计125直接入口；内部922／913／1466不重复登记。

独立从current139静态声明和canonical world重建opening、RNG、XP5、首new卡tier0／4，保留4NPC、2Rune、窗口／special／bounds以及2owned／racial／live／Aura。不同作者旧AI925纯reference生成3份实际BFS路径（235200个u16）和8次移动；没有读取原件输出回填独立NPC位置。玩家坐标是显式按NPC0插值位置加0／8偏移的受控输入，NPC坐标及HP未由harness改写。driver确实预写velocity／path头为0，属于显式setup，不改称自然App所有权生产。

新独立scheduler逐步舍入，恢复basic→cleave→Thunder→racial顺序、成功CD／失败retry、8673移动目标与HP优先顺序、2123正回血／1020到期和racial带来的属性／Aura变化。13次伤害、4次basic（3自然crit）、4次cleave、3次TC、1次racial，10个正Leech与24个正Regen均匹配；共5NPC死亡，其中3个仍在移动，221停止位置／地形Z／序号、死亡冻结XYZ及XP／币奖励RNG也独算一致。额外1次owned crit使总crit为4，不能把3次basic crit当全部crit。

basic的913实参是spell0／school0／critical／最后flag1，owned实际非零spell845／6343的最后flag0；继承Game908=0为另一项上下文，三者不混淆。class1、race1、level2、GUID0、真实声明指针／rank1及source flags均绑定原始捕获与当前WAT。三条1076的GUID和(1,0,0)与纯输入一致，param5=0仍不等同925动态队列索引。callback／incoming history／category未扩大验收。

完整23stats、逻辑player keys、owned、live32、Aura48×16、117个player投影与100个共享ledger快照一致。ledger按melee／cleave:r1／Thunder:r1／regen／leech计算G960／G1016与reason f64总量、93行Vec48语义；不是完整2077复合96B key、catalog、Deque bucket、448B历史验收。49092B NPC None物理守恒，248832B Game输入继承、480组背景owner及原2Rune守恒，None不补零。

37个已知包／1587B严格按有序子序列匹配64个观察包／2593B。basic330包含真实Melee\0melee\0字面量；完整HP／特效／UI回调包流仍未知。旧作者pilot因漏该metadata有1差异，原receipt保留并排除；正式矩阵没有借此缩减断言。

87源／73生产文件／333导入边和40个当前body重新绑定，私有WASM仅增加export。所有计算使用不同作者参考函数及新纯逻辑，没有执行作者模型／builder／runner／checker或原件。评审自己早期fp别名、bytes-only helper接口及expiry诊断事件遗漏的失败源／终态均保留，不属于作者差异。最终PID50117正常退出，PID／进程组均不存在，源前后SHA一致。

正式证据：`evidence/player-autocast139-readonly-review-20261102T132118.787059Z/review/review.json`。原件／作者执行0，作者7件及V3复核3件保持原SHA。连续main884整帧、持续AI／spawn／collection组合、全技能／所有伤害源、完整UI／网络／存档与完整一局仍Pending；没有公共登记、Git或Android修改。
