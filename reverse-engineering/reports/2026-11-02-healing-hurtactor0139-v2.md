# current139：真实受伤后的回复、Thunder生命偷取与共享统计（v2）

作者差分通过，异作者独审待执行。新的两批正式9实例合计42次完整2123、9次完整1076、32次完整922，0差异；另各32次空1775/3755及各9次2945/1600/1108/4677/1093前缀分开计数，共192次直接入口。55个正治疗事件（27regen、28Leech），42个伤害统计事件、8次自然暴击、9个NPC死亡、99次减速写入均有来源和差分。

正式regen5：`evidence/healing139-oracle-20261102T113942.871601Z/comparison.json`，SHA256 `1028911f7b4ef3ace46eed0098f04dadbf5efbdeedc03605745a055016417ac1`。34次2123（5warmup+29后续）+5次实际1076；25正治疗、4零治疗步，包含封顶、零dt、float32累计和长delta。

正式hurtactor4：`evidence/hurtactor139-oracle-20261102T114019.166570Z/comparison.json`，SHA256 `672f1629ab546a9810f6c81f9723bf065cfaa06ff1a66104b68c02be3cb797fb`。32次完整922、4次实际1076、8次2123（4warmup+4postcast），42目标伤害、28正Leech、2后续正regen、最多3目标；另外30个已知launch/reward包2093B有序子序列匹配。

## 真实状态链

所有case均新建Game完整1108、显式XP5、选实际首张newThunder。先完整2123在1秒自然移除1020并施放真实Human perception，再调用实际1076对玩家造成非致死伤害。此后HP来自原件伤害函数，不写回满血、不直接写HP、不禁AI或种族技、不清NPC/proc/source。保留4NPC owner、2Rune、窗口、special、69边界、2owned、live/Aura与种族技。hurtactor按实际NPC对中点与独立地图高度受控移位，半径、crit、RNG和owned参数均不改。

1466是已经发生的正治疗记账函数，不写HP。2123在caller中按f32累加regen并min到maxHP，写key22/28，再传 `min(max(actualHPdelta,0),regenRequest)` 给1466。当前无periodic28、无额外source，默认gate0；非满血和封顶行为均通过。

18421默认Warrior基础生命偷取为class5877920+80的 `0x3c75c28f`（1.5%）。913先损伤并记账，再将 `oldPlayerHP+actualDamage*.015` 封顶到maxHP，给1466传实际HP增量，然后更新HP键。击杀依然走原有死亡/经验/货币RNG，未以满血克隆绕过。overkill时伤害统计用min(oldNPC_HP,damage)，生命偷取仍用完整actualDamage；两者不能混淆。

G960/G1000被伤害与治疗共享。新OutgoingLedger139明确保留伤害事件：913→36520先分配eventID，913→2077记录伤害，随后正Leech1466再分配eventID并记录治疗。实际owned(def5882916,rank1)经8569/30861/26202与当前格式得到 `ability:thunder_clap:r1`，没有从capture字符串回填预期。

明确按WASM零起算参数编号：0=Game、1=amount、2=resolved spell ID、3/4各为描述符指针。Regen的param2=0、param3所指首字=-1、param4所指首字=0（静态record1592624）；Leech的param2=0、param3所指首字=-2、param4所指首字=-1。它们来自当前caller完整body/静态片段，不是原件入口参数动态采样。Regen归因id/name/icon为regen/Regeneration/Spell_Nature_Rejuvenation，Leech为leech/Leech/Spell_Shadow_LifeDrain02，最终Vec48均借用metadata。已验证G960/G1016、source语义f64总量、治疗Vec48 name/icon/total/owns/nestedcount；没有把它们称为完整2077物理结构恢复。

## 证据与未完成部分

regen批53源/43production/160edges、30个current函数body；hurtactor批61源/47production/217edges、34个current函数body，全部先验冻结且前后/当前SHA一致。只改导出段，完整原件callee保留。预期先于原件生成，模型阶段禁读WASM/WAT/原件快照。两批全部玩家72键、23项属性、2owned/racial、live/Aura与known/None比较；hurtactor16356个NPC未知字节逐帧物理守恒（15044个实际非零），38940个NPC已知字节与5824个拾取已知字节一致。连续Game只更新显式clock，覆盖75168B与82944B继承。

真实constructor的G2192来源registry和G2204保存history均为[0,8,0]，有current1600独立静态producer证明，原件保持未改。1466在此真实guard下不追加448B保存history，仍执行2077与Vec48；不把不存在的完整history补零。

Regen Node74637 exit0/1.463秒、hurtactor Node75673 exit0/1.312秒，PID与PGID均missing；882导入全拒绝、host调用0、177078272B峰值/256MiB上限。89与148次栈检查全部回1048576；54与56次资源检查各2318ranges全不变。

保留一次hurtactor失败：8次922的HP/key/Leech/死亡均一致，但27个统计差异暴露G960/G1000共享伤害事件；失败SHA `a0011b2d9e75be078b00c89c438f351923090b1aa17c2c2863face6db0c91ac3`，没有覆盖。修正后fresh1/8pilot通过，再以最终source/identity guard fresh4正式验证。regen1pilot也单列。此前正式5/4因为字段名source_tail_tag可能混淆param3与param4，已保留旧comparison/handoff及全部11作者件exact归档，再以明确字段名fresh重跑最终5/4。旧handoff SHA `41b1236495ec9c45a402b935f6849927bdc8c2ed4633dd853b78bd37c3bdfdbf`，归档收据 `b583dabe0ee043f05a7a97d7baeaf41b051b5cd63093f282133470f7dd77ced4`；旧正式数值结果没有被覆盖。全部研究累计2123=97、1076=21、922/1775/3755各80、各前缀21，共463入口；旧批不加到当前正式192。

这消除了默认regen和当前Thunder生命偷取的满血限制，但新的2123适配器仍使用quiet1238调度。近身basic/cleave/其它owned成功、自然AI925→2123与完整884尚未验收；hurtactor事件身份仅绑定真实rank1Thunder，其它身份明确Pending。非零healOnKill1600/11033、overheal32/33、gate>4、其它source/shield/periodic28/复活死亡均未扩张。

2077完整96key、optionalCow/related列表、catalog140/112、Deque16/Vec40桶、指针/空闲padding/容量与完整UI消息流仍未知；静态协作者新恢复布局不倒记为动态通过。Vec48只验语义字段，448history只验真实空来源guard。没有原生Windows、联网、存档、Android或完整一局验收。旧冻结件、安装包、存档、公共登记与Git未修改。
