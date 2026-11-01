# 0.135.1选卡→属性→XP扫取→候选再生/运行

固定0.135.1 / 0898d5e3的新独立 `selection_cycle135` 已接通canonical kind0的 **new/upgrade/gold应用→1512属性→4600收尾→近处/已吸引XP扫取→逐级属性/治疗→下一kind0候选或恢复phase1**。对完整原1072做 **660个状态序列、1,090次入口调用，声明数值/控制字段0差异**。独立模型不执行WASM；所有期望在原件启动前生成并落盘。没有把只比较record的旧结果当成本组合验收。

## 实际顺序

原1072在应用canonical候选后，执行共享后处理、1512，再调用4600并传入进入时的selection kind。独立模型从必须显式提供的七组属性来源和20B additional-modifier快照继续；来源未解析不能默认空。新能力/升级80B记录、金币数值与队列、23派生词、HP/辅助池、速度都进入同一状态。

4600的kind0先设置flag2581=1并饱和减pending2376，再清除旧候选。随后按原顺序扫取kind0 pickup：**marker非零或者距离≤重算后radius1560即可，不要求arrival到期**。移除后继续同一index，因此保持剩余顺序；base amount先u32绕回求和，和为0则完全跳过XP派发。非零和先做mode分摊/XP1564倍率、85719舍入与NaN安全最少1，再进入完整4630；此时phase仍2，故4630自身不会提前生成下一候选。非零mode把未缩放base和peer写入独立XP转发队列。

扫取可再次升级，必须每级1512/20%治疗/阈值循环完成后，才按pending2380→kind1、2384→kind2、2376→kind0判定优先级。普通pending还受gate2572==1且flags2573 bit0为0的延迟条件约束。kind0再生调用2159的enter_now=0，保留phase2并更新kind2585/counter2400/RNG。kind1/2 metadata及其RNG尚未恢复，API返回`pending_priority_choice_metadata`并保留明确调用意图，不把前缀状态冒充完整下一候选。

无可进入pending时，flags2573清0、kind2585置255、Gtag清0、phase2587设1；mode0还有待独立实现的25472移动恢复意图。删除所有旧spell1020 live records后，追加kind12/spell1020/expiry=`now+f32(1)`。**原4600未写新record的union+12值**，模型把该无效payload语义canonical为0，786次观测中的321个实际heap word并非0；这一字明确不做原始位预测，其余已声明live语义字段比较。物理32B全部字节没有因此被宣称恢复。

## 对照范围与尚未恢复的字段

比较owned80B记录、23派生词、HP/5辅助字/速度、XP/level/pending、全部四字RNG、候选metadata/phase/kind/counter、flag2581/2573、完整剩余56B pickups及顺序、金币/earned、XP和金币的peer/base队列与capacity，以及live effects的有效语义。logical numeric player keys固定为22/28/34/716/717/1109/1176；其余真实原件键值在每行`unmodeled_player_fields`**完整保留**，不读回填入独立期望，也不计入已还原范围。

其中原1072装备/外观对象使用global counter14384504生成900000起的GUID并写488/489，非零mode还出现272等字段；原4600→1202另写aura数组47..100/113..124，混合来源还观察到380/392/506..509。它们包含外观/aura及其它尚未命名的keyed state，**不能假设全部只影响显示**。API pending明确列出这些producer；没有宣称完整1072状态等价。后续应分别恢复1202、外观/装备与这些未知键的实际消费者。

语料有全部114定义的tier0/4 new→stats→finish，9职业×8种族×三variant的非空混合来源，pending/延迟guard，marker0/1×radius边界×amount0/1/200/u32MAX，mode0/1/2/7/255及member0/1/2/255/u32MAX（已解析elwynn region0）、additional modifiers与连续选卡。模型状态计数为571次running、304次kind0再生、215次入口拒绝；每次原件返回的对应phase/候选已比较，这些不是额外独立用例。

初始G逻辑树明确为空、game tag0；world/单位状态不在本构造中恢复，special kind1/2 pending均为0，party region3/11未由本组合重新验收。此前leaf-only树读回因实际共有字段增加而拒绝，已用有界原树布局读取全树；后续仅比较上述固定数值键，并保留其它全部原观测。另一次人工marker2在原31732中移除后显式进入panic；它在原31732中走不接受的sentinel路径，未据此恢复Rust枚举源码，canonical记录要求0/1。非法原始状态不计入成功覆盖，失败源、输入、已输出817行和具体guard均保留。

最终证据 `evidence/full0135-oracle-20261101T041538.274712Z/`。42实例，峰值20,774,912B，Node22.23.4/512页/60秒owned进程截止，1.314秒、exit0、878宿主导入throw且实际调用0。研究副本只增加原1072导出，36个原exports及所有非7节/内部callee保持原样。22份参与源码、模块/manifest、预生成输入/期望与结果均冻结、保存快照、前后复核。没有启动应用或访问官方网络/存档，未修改安装包。

复现 `python3 reverse-engineering/scripts/check_selection_cycle135.py --phase full`。本组合覆盖独立核心控制和数值，world/未知keyed producers、真实来源、全部特殊候选、UI/网络以及完整帧/一局仍未完成。

最后独立复核发现比较器对integer derived1592/1608允许了过宽的NaN分类。已仅修复checker，增加两个不同NaN样式u32必须拒绝及一个声明float NaN可分类相等的纯contract（0原件案例），随后必要重跑仍660/1090/0。模型、runner、全部fixtures和原件结果文件均与前轮逐字节相同；前轮040531保留为intermediate，不重复计覆盖。

最终041538独立只读复核重新生成660份序列及1090次期望，严格比较69,551个标量，0未声明差异；1592/1608整数与3份纯比较器contract均复核通过。22份源码/快照、模块与结果绑定通过，复核未执行WASM；最终收据SHA为`d9f8a1a1e6123250ad2d432e1364b0cb031f87b8468a1d75081729fb2896cfee`，见相邻JSON。
