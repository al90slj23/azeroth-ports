# current139 Healing/Hurtactor v2独审：参数保真未通过

**不接纳为完成，等待v3。** 数值投影与独立参考一致，但原件入口参数和作者期望输入不一致。不能以当前空源样本的数值相同替代源码／输入保真。

两个冻结runner都调用1076(Game,amount,实际NPC_GUID,0,0,1)：按当前签名为contactFlag0、category0、spellID1。两个期望checker却调用resolve_prefix139(...contact_flag=1)。差异分别位于run_healing139_oracle.mjs:46/check_healing139.py:75及run_hurtactor139_oracle.mjs:51/check_hurtactor139.py:47；JSON保存精确AST行和调用片段。incomingcategory/history/callback没有纳入该批比较，不能称自然NPCcontact1受击链已覆盖。

另一套只读参考使用既有独参Fraction/f32、开局／选卡／调度／Thunder／死亡奖励函数，加自写回血与共享账本逻辑，未导入执行作者生产模块、runner、checker或builder，也没有新原件执行。42次2123、9次1076、32次922的保存观察，数值上匹配27正regen、28正Leech、42伤害事件、8暴击、9死亡、99slow写入及30个已知包2093B。包括HP上限、key22/28、伤害先记账再正Leech、零heal不记event、G960/G1016/f64总量、Vec48name/icon语义；158112B连续Game继承及16356B NPC未知字节物理守恒也匹配。这些均只保留为窄数值结果，**不是v2正式接纳**。

1466的Regen参数2=0、参数3所指首字=-1、参数4所指首字=0(record1592624)；Leech为0/-2/-1。此项是当前caller/28155/字面量静态绑定，不是入口参数动态采样。完整2077物理96key/catalog/bucket、Vec448历史、native／884／完整游戏仍未接纳。

数字参考receipt7cdd2ba7bb1e2cc12f25a4d976421099716594b841c8ad6e5fcf8c8687906d83及先前所有receipt保持不变。最终只读裁定receiptab9067b6a76643b7988f1b709943a21f5d60b750f303acab5f1e6afae20da1a7标记not_accepted。作者11件、v1归档和失败a0011均未修改。

新v3需统一实际参数与期望输入，重新冻结并执行fresh5+4，再做不同作者只读复核。不能在旧数值通过记录上直接改成参数通过。
