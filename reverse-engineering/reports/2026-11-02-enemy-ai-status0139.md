# current139：真实 Thunder 减速→AI925→到期恢复

作者原件差分通过，异作者独审待执行。正式 4 fresh／144 次完整925、0差异。每组先真实2945→1600→1108→4677显式5XP→1093首张新Thunder，再完整922一次产生2189减速；前缀各4次（20次）和4次真实slow生产入口另列，共168直接入口。没有把内部913／2189／1076重复计数，没有调用空1775／3755。先前1 fresh／36帧pilot不加正式数。

新 enemy_ai_status139 组合冻结Thunder与enemy_ai139，旧AI源码未改：它本来已含81682的数值分支，此前缺少真实2189生产后连续运行的验证。4个原始NPC位置、全部owner均由真实1108产生；driver只允许时钟和玩家XYZ控制，NPC状态／HP／source headers／CD／racial／live没有任何注入、清除或补满。玩家初始位于原NPC的+8码（第四组为原位置），3秒附近移到原位置-8码，Z来自独立canonical地图高度。

实际链为922→27754／10490→913→2189写U120=0.5、U124=3、U376=0，然后完整925→81682。三个相邻binary32边界都使同一真实NPC产生新运动：3秒前一ULP速度2.625，恰3和后一ULP为5.25；原件写出的duration分别为0x4082a89e、0x4002a89e、0x4002a89e，恰为2倍差。原件没有在到期时回溯修改已有运动段：前一ULP创建的慢速段在3.125至3.625仍保留原start/duration，之后新规划才用正常速度。U120／U124字节本身保留旧值，不能把速度失效误实现成清字段。

共96条真实motion221（包括4条stop）、6次接触attempt。第四组在0.125有实际接触，1076的selected live12有效guard使HP239、incoming总计0、history0；过1秒后自然产生伤害，live12记录及Aura并未被925物理删除。共5次真实非致死掉血，前三组末HP236.3513、第四组233.7026。所有两owned、racial0.5原CD、live/Aura完整物理owner保持；新guard视图只暴露kind／spell／expiry，live12未知value没有补零。未调度1238或2123，不能将本批解释为完整游戏中的技能频率、感知调度或真实UI到期更新。

每组两张真正由925生产／重建的完整78400值BFS图，共8图，非固定None或uniform。所有实际路由direct_clear，blocked-flow仍未动态验收。144帧入口完整Game继承373248B，仅显式写clock／XYZ；全部NPC432B存储248832B逐帧物理重放，179376已知／76368 None，其中70300实际非零仍保留未知。live共15808 None（全部实际非零）、Aura85728 None（74784实际非零）、history12504 None（11084实际非零）；均未用原件反填。两Rune、windows、special、69边界、aux／claims与counter背景保留，实际NPC运动和接触伤害是允许的行为变化。

完整925消息增量为102条：96×221、6×330，逐帧全部字节一致；上游922仅已知launch子序列，不宣称已还原完整592／HP169及其他统计状态。32个current函数体／静态decl、全部非export section与82源／70production／291边在原件前冻结且前后／当前一致。预期阶段Python open audit禁读原件／WAT／snapshot；原件借既有合法v2资源上下文新建Game，来源边界明确保留。

原件Node PID73622，约2.083秒，exit0，PID／PGID均missing；882导入全拒绝、host0，177078272B峰值／256MiB上限。20次分配和168入口共188个SP检查均回1048576；168次资源检查各2318ranges不变。一次新adapter bytes/cells类型错误发生在纯模型阶段、原件0次，已保存失败；修正在新文件，旧冻结代码未改。纯模型研究和pilot均另列，不叠加正式通过数。

非空effect49／slow376移除、其他NPC状态／ranged／boss／guardian／fatal、正数治疗／吸血、失血后再次922、动态新刷怪、主循环884与AI／player联合、自然App／worldRc／externref启动、完整UI／联机／存档／Windows原生／Android及完整一局仍未完成。现有安装包、存档、封装优化与公共登记未修改。

详见[机器报告](2026-11-02-enemy-ai-status0139.json)。
