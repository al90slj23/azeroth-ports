# 0.135.1 NPC动作生产与880调度静态清单

[固定原件证据](../evidence/npc-effect-producer0135-static-20261101T071734.993684Z/npc-effect-producer135-static.json) 保存16个完整函数及其签名、body/WAT范围和SHA。本轮只读静态及保存输出，不执行原件，不改shared/headless或旧报告。

原data的12区域表独立给出148个72B normal定义：124个前16B为四个u32零，是普通近战声明，不是动作tag或40B动作；另外24个prefix1保存spell ID、range和cast-delay原始word。921中普通近战走临时直接1073路径，prefix1 ranged走另一16B cast队列，不能混同为910的44B动作队列。[normal-declarations.json](../evidence/npc-effect-producer0135-static-20261101T071734.993684Z/normal-declarations.json) 保留每个原始72B及字段。

60个boss的静态数据另含257个44B周期动作和33个52B HP触发动作，共290份完整40B descriptor。raw37标签、normalized值、原始words/hex、cooldown或HP fraction、boss名与地址全部保留于 [action-declarations.json](../evidence/npc-effect-producer0135-static-20261101T071734.993684Z/action-declarations.json) 和 [boss-declarations.json](../evidence/npc-effect-producer0135-static-20261101T071734.993684Z/boss-declarations.json)。这是可供后续规格直接读取的数据声明，不能算290种行为已恢复或验证。

921给910投递的唯一直接call在收尾。临时队列的stack cap/ptr/len是148/152/156，每条44B为NPC index加完整40B descriptor，队列+41就是descriptor raw37。四个append点分别来自U64非MAX家族的U96定义+16/+20的52B阈值动作、U68/U72计时器与U84/U88的44B周期动作，以及U244非MAX boss的U256定义+24/+28阈值动作、U248/U252计时器与U260/U264周期动作。U64家族完整声明/构造路径仍未知，未用boss数据冒充它。收尾byte387<=3时raw12/26会抑制910；临时队列raw255退出整个队列，这是921的规则。

重要勘误：旧915静态摘要称raw255“跳过”已被后续非空原件实验推翻，真实915先pop再到80660/90675 panic。本报告不沿用旧skip语义，也不把921临时队列raw255规则套到915。

保存的064308 same-G NPC全424B读回可进一步限定当前域：71,106次逐stage记录出现仅含Kobold Vermin/Young Wolf，U40/U64/U244均MAX，U72/80/88/96/104/232/240/252/264/272均0，符合上述动作族未激活的静态条件。这不是新增NPC数量（实际出生仍122），也不能替代915的2364/1816/1828真实读回，更不能证明未来动作族不会出现。

880的单状态尾段顺序是2088→916→975→1754→3757→915→38007→2602→921→2862→2573→[2579为0时947/2376]→49037。还有两个915调用位于party状态换入/换出路径；证据保存所有对应call的if上下文和窗口，不能把三个词法位置都当单机连续调用。

通向完整880还缺：916的active84/proc系统；975对owned execution11及784..904等状态的处理；38007的1836/1840 stride32队列；2602的1860/1864 stride112（区别1754的1848/1852）；2573的phase1 claims88/资源与XP续行；49037的400/phase/protection终态处理。它们的完整body、直接G读取候选和callee已列出，当前same-G没有这些入口验收，不能默认无效或空。完整880前段还包含命令/网络会话、clock、transport及后续阶段门控，真实1089/resource boot与应用启动同样未完成。

下一步以原八seed、原动作新增真实915观测及独立规格差分，再按上述缺口逐项补齐；静态调用顺序和声明数据不升级为完整调度或游戏重造完成证明。
