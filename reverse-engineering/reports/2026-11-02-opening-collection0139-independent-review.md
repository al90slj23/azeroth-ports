# 0.139.0 完整开局→真实击杀经验→首次选择→续击：异作者独立复核

3个appseed（0、1、42）的同Game受控连续流程通过。new2945／1600→完整1108→真实伤害死亡→真实经验球吸附／到达／消费→4677内部2181产生三卡→1093选择首个new技能回phase1；seed42保留实际两个owned记录和live12，再对活NPC完整922续击。没有直接插入经验，没有清四NPC、两Rune或背景。

原件目标入口47次：3×1108、21×922、20×2890、3×1093；2945／1600各3次仅setup，内部5719／913／4677／2181不重复计数。独审0原件／作者model／checker／builder执行，重新从当前139静态表、raw-derived world与冻结独立数学／开局／伤害／成长参考构造全部结果。

228条完整opening包共24336B一致；后继60条已知有序消息共3117B一致，仍是592／HP169／成长UI等完整消息流的子序列。11次XP与3次金币领取、105项已知player字段、125项已知growth字段，全部RNG／f64累计／三个spell集合／owned80／HP及phase一致。三组都依靠实际掉落累计总5XP升到level2。

NPC25620已知／10668 None与掉落3820已知／884 None通过；10668个NPC未知字节和884个拾取未知字节严格继承。collect另核3952已知／528 None、从实际输入仅施加标记／arrival与56B整移位的4480B完全一致；34560B NPC在拾取过程中不变。选卡live72已知／24 None，续击另24已知／8 None并保留原始字节。21个开局新pointer word只观察；7776B相对开局Game以及两段各51840B的连续cast／collect Game输入继承严格核对。

后续技能数组必须从当前Game1660读取：1093追加第二技能后会重新分配旧cap1 Vec，旧地址可能被BTree复用。失败三组9差异批保留；最终runner与独审核对新owner header、两个真实definition pointer／execution byte，确认均非11且7项hit-source word保持0。该证明只覆盖execution11 arm，不代表全部技能回调／新技能自动施放已恢复。

原件仍借合法v2post1108资源上下文，再新建Game；独立预期仅用raw-derived world。初始accounting／kill／gold／sequence是显式检查输入，未恢复完整Game producer。玩家移位、直接入口调用和时钟均是受控调度；尚非自然设备输入／AI／owned1238／主884整帧。完整UI／物理树／分配器、Windows原生、胜负／存档／联机和完整一局继续未验收。

完整收据与散列见[机器报告](2026-11-02-opening-collection0139-independent-review.json)。
