# 固定0.135.1：开局附属对象与world actor组件

新[独立组件](../reconstruction/core_spec/opening_entities135.py)与[静态数据](../reconstruction/core_spec/opening_entities135_data.py)对照完整原1744／1821，最终[收据](../evidence/world-snapshot0135-oracle-20261101T101743.010880Z/opening-entities135-comparison.json)为**27组、116次原件入口、0声明差异**，SHA `132de5b5e8fd59a6f74ecb3b34859f8677b291122f5fa1aacb9c2fbd41cd2499`。这是由真实世界snapshot派生的组件差分，未启动应用或重新bootstrap，也不是完整1089验收。

1744从两条显式inline8B声明中过滤tag255，按有效条目顺序生成附属88B记录：位置为玩家朝向加逐f32的`(i×0.35+1.15)×π`，距离2，世界高度走原有成功／nearest／fallback语义。每条增加一次G2408，GUID使用F130、entry低24位及counter低24位；本函数不消费G RNG。13个对象字段、完整unit create169包与六项移动速度均恢复；G1556与原G273字节的速度顺序保持。88B的`+8..15/+21..23`未写区域保留旧值，新分配的未知字节不预测为零。显式fixture原型的定义指针仅按受控分配映射规范化，完整raw记录、44B原型和映射另存。

1821每次先增加counter，再按真实高23位采样0至2π角度，逐f32生成朝向及四元数相关字段。F110 GUID、完整key表和gameObject create169 payload均独立实现；包括counter跨uint32边界与GUID的24位截取，WASM有符号i64返回值另存，并按u64解释GUID。全部新169 payload逐字节比较，物理metadata分配地址不冒称已独立还原。

27组覆盖原型非零entry／display／scale、tag过滤、旧88B槽与增长、保护守卫、两次连续生产、原始counter边界、非默认朝向／速度、零RNG及69次连续actor。23份源码闭包在原件前冻结并保存快照；真实after_world6730的117,440,512B整memory逐字节恢复，原world与缓存保持原字节，没有写Once或手拼Rc。独立256MiB／4096页域拒绝全部878宿主导入，实际0次；进程52920退出0、栈保持1048576。期望另存，原件只接收4个输入字段。

另外已经编码1089内联的8B窗口、40B special声明、circle／polygon边界和83B开局banner150。窗口数量取原数据2..3，按末Boss分钟分段；每段终点取60%至100%区间，所有操作逐f32。special保留未写12B，四个方位依次筛选真实候选及导航／高度，边界actor仍逐个消费随机角度。这些内联producer**不计入本116次入口验收**，等待完整1089组合的新差分。

[历史观察重放](../evidence/opening0135-historical-replay-20261101T102107.100725Z/replay.json)核对了两条附属记录、四条special记录、83B banner及69条边界payload。边界RNG输入由真实终态逆退已知69次actor转移得到，因此属于观测重组，不能证明此前NPC／kind2／窗口链已独立还原，新增原件调用和主切片帧均为0。原历史counter10→87已明确分为2条附属、4NPC、2kind2与69边界对象；没有把后半当作no-op。

首个pilot的4处差异是JS有符号i64返回值的表示问题，旧收据／源码快照保留；修正adapter后pilot与full均通过。本批不覆盖完整世界／菜单profile或4NPC与kind2的全1089组合；后继默认开局组合另列。完整880、存档、UI、联机及独立一局仍未完成。完整字段、SHA、限制和当前复核状态见[JSON](2026-11-01-opening-entities0135.json)。复现：`python3 reverse-engineering/scripts/check_opening_entities135.py --phase full`。

[独立只读复核](2026-11-01-opening-entities0135-independent-review.md)已通过，最终 review SHA `a489d812eaea8e68fed6c6bb41f730750335f35d3160efb91b33533ca1e897e6`；未执行新原件，原批验收边界不扩大。

后继[完整默认开局组合](2026-11-01-opening0135.md)另有16组/32入口新原件差分；其内联分支覆盖不倒记到本27组/116调用。
