# 当前139刷怪调度 v2：自然跨越40秒资源生成

固定0.139.0／f79c5e2b4，未切换新139.1原件。新模块纠正研究角色：2424=初始60秒多形波次，2440=初始240秒普通精英；旧普通7件及单独标签更正保持SHA。本v2只接受60秒前普通调度与真正40秒资源，不称完整952。

4个全新实例／3119次完整952（另12次2945／1600／1108前缀，合计3131直接入口），全部按dt=.0625从0自然推进到59.9375／50／45／40秒，原budget3、timer、RNG、4NPC、2Rune、window／special／bounds保留，harness在1108后只写时钟2352。132新NPC、4个40秒资源、136个完整已知169消息；469267项断言0差异。

40秒周期从真实2444到期，下一deadline=now+45；当前kind3／4／5 count<2时，实际xoshiro bounded3→kind3／4／5，保存kind选择后的RNG wordA为arg2，再13563抽15..40位置、1446约束高度、1886生成actor／counter／yaw及56B记录。静态cap2分支没有在本矩阵到期第二次，未算动态覆盖。三常规seed0／1／42覆盖kind3／3／4，纯模型搜索2..6找到自然kind5的seed6后，另新fresh640完整952原件验证，不注入kind或改RNG。

普通调度跨30秒unlock，实际definition1新增24次；其余新NPC为definition0。正向density、全局50cap以及后续定义仍未进入实际分支，不能把静态实现当作这些分支通过。

37个完整物理checkpoint及全部3119步标量／RNG／counter／timer／packetcount匹配。238764个已知NPC字节、203604个None观察（178717非零）与132534B既有None物理继承通过；pickup4524个已知字节及3764个None保持部分状态；92352B Game输入继承与222组非pickup背景owner守恒，原2Rune原始字节不变。模型没有以原件值补None。

两套正式源闭包各46源／34生产文件／136导入边，23个当前body／五种资源相关callee静态绑定；原WASM仅增加export。expected和source快照先于原件冻结，模型阶段禁止读取原件／观察。原件world使用已校验resource-only v2 context，纯模型使用独立canonical world，两者不等于自然App／WorldRc生产。两个Node PID77475／84890均exit0，PID／进程组不存在；0hostcall，256MiB WASM／512MiBheap上限。

第一次v2试跑的clone命令误指旧v1runner，旧40秒guard在639次952后拒绝，没有40秒原件调用和结果行；失败源码／runtime／owned收据保留且不计通过。修复后pilot640次仅列pilot；正式只计上述3119次。旧7件、存档、安装包、公共登记、Git、Android未改。

下一必需项是实际60秒多形波次、60秒Rune／window kind6、240秒精英和3分钟起Boss。模块到60秒到期即明确Pending，不跳过或伪造timer。持续战斗／AI删除／密度／killcatchup组合及完整884／完整一局仍Pending；本批等待不同作者独审。
