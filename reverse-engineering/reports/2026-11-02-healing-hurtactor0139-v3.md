# current139 回复/生命偷取 v3：原件与模型参数一致

作者差分通过，异作者独审待执行。v3新增checker/runner/builder，完全不改v2的11作者件及三个core。v2的原件1076参数(0,0,1)与模型contact1不一致，因此只保留numeric-only观察，source-fidelity未接受；本批没有以空源数值等价代替修复。

v3 frozen inputs显式记录 `{contact_flag:1,category:0,spell_id:0}`，模型与原件从同一输入读取。原件调用严格为1076(Game,amount,actualNPC_GUID,1,0,0)，9例sourceGUID与三参数逐项一致。两builder在执行前重新核current1076签名和925调用窗口。普通925当前调用为(1,0,local2)，local2是先前330入队index；category0时入口param5不用于spell lookup。本批param5=0是明确的受控值，没有冒称复刻自然925动态queue-index，也未恢复完整incoming history/category/callback。

正式regen5：`evidence/healing139-v3-oracle-20261102T121237.785322Z/comparison.json`，SHA `5d773c21620cb1334a816776d129b1cf8859e5d0c2ca0b9605e9585446733e20`。34次完整2123（5warmup+29后续）和5次实际1076，25正回复、4零回复步，包含非满血、HP封顶、零dt、float32累计和长delta。

正式hurtactor4：`evidence/hurtactor139-v3-oracle-20261102T121344.276555Z/comparison.json`，SHA `7925e334e6a9328ff3bf57c28afa0cea54325b34cda893a538e93a66f4a142bf`。32次完整922、4次1076、8次2123（4warmup+4postcast）、42目标伤害、28正Leech、2后续正回复、8自然crit、9死亡、最多3目标；另各32次空1775/3755。各2945/1600/1108/4677/1093前缀9次分开计。两批9新实例合计192直接入口、0差异，55正治疗事件（27regen/28Leech）。

沿真实完整1108→显式XP5→实际首张newThunder，先full2123自然移除1020并施放真实perception，再由实际1076造成非致死伤害。此后HP一直继承原件伤害，不回满血、不写HP、不禁racial、不清NPC/proc/owned/live。保留4NPC、2Rune、窗口/special/69boundary与两个owned。hurtactor只受控移玩家到实际NPC中点和合法地图高度。

1466只记账已发生的正治疗，不写HP。2123在caller按f32累加regen、min到maxHP并更新key22/28，再将受实际HP增量限制的请求给1466。Warrior18421默认生命偷取1.5%：913先伤害事件，再HP=min(maxHP,oldHP+完整damage*.015)，1466记实际HP增量，之后HP键；overkill伤害统计cap到旧NPC_HP，Leech仍按完整damage。

共享G960/G1000同时记录伤害与治疗。OutgoingLedger139保留实际owned rank1Thunder的 `ability:thunder_clap:r1` 伤害事件与leech/regen；无正治疗时不会伪造治疗event。已核HP/max cap、72键、23属性、2owned/racial/live/Aura、G960/G1016、reason f64总量及治疗Vec48 name/icon/total/owns/nestedcount。完整2077的96key/catalog/buckets/padding/heap和448B保存history仍未重建；真实constructor的空registry guard被保留，未清零制造通过。

两个正式批各62源/47production/217import边，current body绑定31与35个；全部源码先验冻结且前后/当前一致。预期先于原件，不向原件传expected；原件仅导出段改变、882导入全拒绝、host0，峰值177078272B/256MiB上限。Regen PID32050 exit0/2.099秒，hurtactor PID37426 exit0/3.740秒，PID/PGID均missing。v2旧收据、参数corrigendum及fidelity拒绝独审均保持不改，不加算本批覆盖。

WASM零起算param3/4描述符首字元数据仍来自静态caller：regen(-1,0)、Leech(-2,-1)，param2 resolvedspell0；未动态采样1466实参。旧所有研究累计2123=139、1076=30、922/1775/3755各112、各前缀30，共655入口，正式本批仅192。

仍未完成近身basic/cleave/其它owned成功调度、自然AI925→2123/full884、非零healOnKill1600/11033、overheal32/33、gate>4、非空来源/shield/periodic28/复活死亡、完整UI/入伤metadata、原生Windows/联网/存档/Android或完整一局。当前新2123 adapter仍quiet1238，hurtactor事件身份仅实际rank1Thunder。安装包、存档、公共登记、Git及所有旧冻件未改。
