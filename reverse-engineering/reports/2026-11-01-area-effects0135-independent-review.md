# 0.135.1 持续范围技能独立只读复核

最终两批 [full525](../evidence/full0135-oracle-20261101T062917.025429Z/area-effects135-comparison.json) 与 [death168](../evidence/full0135-oracle-20261101T062939.812946Z/area-effects135-comparison.json) 在声明域内通过。冻结生产模型独立组合重放693组、5,495阶段，与预先保存expected和原件输出逐字段一致，共1,013次成功施法。未运行原件或改作者生产源；[独立证据与脚本](../evidence/area-effects0135-independent-review-20261101T063449.578641Z/review.json) 已冻结。

每批34份source snapshots、全部artifact哈希、包含package init的28模块生产闭包、922/3757角色/body、7条真实88B定义与原data段均核对通过，当前无源码漂移。两执行模块除了export7，其他原件字节全部相同，无start section。预期生成、序列化读回和源码冻结均发生在原件执行前；Node以512page/60秒截止运行，保存日志没有host调用。独立检查14项缺失来源、非bool声明、未知variant/spell、非有限输入与缺失hit callback均拒绝，caller状态保持不变。

持续效果记录全88B严格比较6,782行、596,816字节，完全没有mask；1,013次append保留的19字节（8..23、85..87）共19,247字节逐字节匹配显式A5/5A槽输入。pickup完整56B比较2,688行、150,528字节。NPC比较范围是每单位32个返回u32字段，共1,851,520 word，包括HP/death、坐标、控制120/124等；这不等于完整424B NPC或物理ECS字节已经还原。浮点和整数均严格，有限输入域未采用NaN分类放宽。

独立复算301项到期与due重叠均先expire，2,625个due area条目每次只消费一tick，不追赶遗漏tick；向量稳定压缩。持久伤害76在施放时存储，tick重新读取当前critical机会与倍率，没有再次乘当前damage/area倍率。death批1008阶段连续共享G2408与RNG，504次普通死亡产生672个pickup，后续目标继续使用死亡消耗后的RNG/counter。effect1的144次致死命中全部先完成914普通death/loot，再进入2244；2244按marker1跳过，未写死者slow120/124。该顺序同时从原WAT确认。

范围限consecration、volley、immolation_trap、blizzard、flamestrike、rain_of_fire、hurricane七条固定kind3/effect0或1定义，显式无地形/navigation、proc/item、follow36/override49来源，玩家HP固定已满。非空其他producer、effect2/frost trap、地形修正均拒绝或保留未知。完整visual/packet载荷、ECS/allocator容量和技能显示并未因无host数值通过而视为完成。父任务headless尚未接入本模块，接入后必须按最终源码另跑same-G原件验证；旧checkpoint证据不能自动升级。完整880与全部游戏重造目标仍开放。
