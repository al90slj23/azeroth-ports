# 当前139默认刷怪调度：普通阶段首个可执行闭环

固定0.139.0／f79c5e2b4。结果为完整原件952入口在默认静止、无战斗、40秒前普通调度域通过，尚未恢复完整952所有定时事件。

3个全新实例（App seed0／1／42）先实际2945→1600→1108，保留原4NPC、2Rune、2／3个window、4special及69bounds。仅自然推进Game2352及传入dt=.0625；原件正常生产的budget3、各timer、velocity0、pathNone、RNG和NPC状态全部保留，无注入。1080次完整952产生47个新NPC及47个169消息，跨30秒定义1解锁并实际产生该类型2次；201378项断言0差异。

纯模型从独立opening与current139静态12×72B敌人表计算预算、密度、加权选择、共享RNG、真实canonical world位置、HP／攻击时间曲线、GUID及消息。原件使用v2 resource-only world context，旧Game不作为目标。两类world来源边界明确，不将快照所有权当成独立App／WorldRc实现。

全部1080步比较标量／RNG／counter／timer／packet count，27处完整物理快照比较已知432B与完整有序已知消息。85749个已知NPC字节、69771个None观察中有61295个非零字节；其中47061个既有None字节物理继承检查通过，没有补零。67824B Game非写集及189组背景owner守恒；玩家属性、血量、技能／live等保持原值。

新静态查明1600临时T+88复制2592B到Game：T1824的i64zero生产velocity1736／1740；T2504的i64(0x40400000)生产budget3与killcost0；T2456生产path2368None；默认profile371<3令local13保持0，T2072写出1984空事件owner。driver逐项assert，不写这些字段。原件952和全部callee保留原body，仅export section增加研究入口。

46个源文件／34个生产文件／135条导入边、19个当前函数body及表字面量绑定；expected冻结先于原件，模型阶段禁止读取wasm／wat／memory／exe及originals目录。Node86599正常退出，PID／进程组均不存在，1104次stack检查、33轮2318-range世界守恒检查通过，0hostcalls；WASM177078272B／256MiB上限、heap512MiB。

首次期望阶段出现None inbytes的TypeError，0原件启动，失败与源码保留；其后8步pilot通过，正式覆盖只计上述1080步。

下一真实阻碍：40秒拾取1446、60秒精英timer（实际首个精英定义在3.5分钟解锁）、240秒波次、Boss2801、window kind6及回收远处NPC。当前模块到非普通timer到期即明确Pending，后续新版本继续恢复，不能把此普通阶段模块当成完整952或完整一局。战斗/AI/1238/884连续整帧、Windows/native/联机/存档/UI仍不在本批范围。所有旧冻结件、安装包、存档、Android、公共登记与Git未改；等待不同作者独审。
