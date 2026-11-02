# 139 普通刷怪952：不同作者只读独立复核

已独立复算3个fresh原件fixture中的1080次完整952输入/输出，限定默认静止、无战斗、40秒前普通调度域，0差异。复核者未执行作者model/checker/builder或任何原件。正式目标仍是952的1080入口；2945/1600/1108各3次为setup，独立复算opening不扩记成新的正式target。

- 真实初始budget3；每帧预算、clock、四RNG字、counter、NPCcount/capacity、previousXYZ、velocity、timer阈值和packetcount全部独算。初始跨位置速度过滤3次；killcost+0的衰减域1080次，没有借此验证非零catchup。
- 从current952/20357及静态12×72B表重绑权重、候选与有序RNG；47次选择与94次NPCyaw/jitter。全部47个新NPC：定义0为45、30秒解锁后定义1为2，创建包169全部独立重编码，完整payload共8413B。
- 1080次density判断无补足请求；15778次55距离回收判断均未命中。对应实际触发的density-fill/远处NPC回收仍Pending，不能把谓词未命中说成分支已验证。
- 27处完整快照核85749个已知NPC字节、69771个None观察（61295个非零），其中47061个既有None字节物理继承；未用实际输出填未知。2227份完整有序累积包快照为前缀观察，新增包仅47。
- 保留4初始NPC、2Rune、windows、4special、69bounds、aux/claims、技能/live、属性/HP/tree；189组背景owner守恒。独审核68040B Game非写集继承，比作者67824B多216B，是额外要求每checkpoint的8B velocity字段也物理不变，统计口径没有覆盖扩张。
- 输入契约逐项核：3个App seed0/1/42、LCG→真实constructor种子、dt=.0625、frames600/320/160、最长37.5秒；完整2232B account/profile来源字节，selection40和canary均匹配。没有更换目标Game、移动NPC、改budget/RNG/velocity/path或隐藏死对象。
- 源闭包46件/34生产/135边及作者7件全不变；19个作者绑定body与11个额外纯helper相关current函数重绑（具体去重清单见JSON）。完整原件只增export section。合法v2 resource-only context与独立canonical geometry来源边界保留。

冻结v1将两个研究变量/报告角色名叫反。独审将 `evidence/spawn-schedule139-timer-label-corrigendum-20261102T125058.478630Z/notes.json` 及5个窗口重新对到当前完整952：**2424初始60秒是多形状波次；2440初始240秒是普通精英**，续期间隔分别为now+max(35,60-1.5min)与now+max(25,55-2.5min)。本批最长37.5秒，两个原件分支均未进入；偏移/数值正确，错误名字未进入已执行计算，因此接受该普通前缀域。旧7件不改，未来版本必须改正角色，不能把60秒视为空精英tick。

原作者PID86599正常退出；独审PID13017，exit0/11.30秒，PID/PGID均missing。1089份原件setup/target返回记录SP均1048576；33轮2318-range世界守恒与0host调用为冻结driver捕捉/静态守卫，独审没有重跑。完整物理捕捉用于NPC/Game/owner继承复核；分配指针和资源None的语义未推断。

两个先行独审尝试只因当前manifest键名和capture.frame结构检查错误退出，日志/当时源/PID终态保留排除；均为0作者/0原件执行。最终独审目录 `evidence/spawn-schedule139-independent-owned-20261102T130255.254303Z/`，review SHA `5a19e028ac0a8653bcd2f8e4dd922d28842bddb644b2da89876551af2893046d`。

40秒拾取、60秒波次、240秒精英/Boss、非零killcatchup、移动/死亡/回收/池满/其他模式，及连续884整帧、完整一局、Native/联机/存档均不在本次通过域。现有安装包、存档、Android和公共登记未改。
