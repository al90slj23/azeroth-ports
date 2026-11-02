# fixed138默认构造1571：异作者只读独审

**限定通过。** 当前138原件的新鲜162例构造结果，已由另一作者重新提取静态数据、独立计算默认空profile属性、PCG种子、完整80B记录、动作与226包，并完整核对502个已知Game字节。独审没有执行原件、生产模型、checker、builder或验证器。

原件比较`evidence/initial138-oracle-20261101T234430.736166Z/comparison.json`，SHA `fd3b76ad14f92f33bb7611888b5e86df6f9ea21918292a824aef1a3da380a3b5`。0.138.0 / `382771e6c`，WASM SHA `c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b`。162个fresh实例/162完整1571/0差异，未转入任何135运行次数。

## 来源、静态恢复与借用输入

21个来源、10个production、35条完整本地导入边，在冻结副本、运行前后与当前读取时逐一核同。期待在原件启动前生成，inputs只有输入；source顺序是来源证据，不冒充外部签署的时间证明。WASM仅增加1571和stack导出，原非导出section和函数体保持；1571三i32参数、7069B、body SHA `37447d2eef76c4d93a5e2d2b5c0143ff8ef591e13fded44ee84e06bcb8d9a43e`。

从138原始data segment独立提取114个技能声明、新class/race表及12区记录，9职业starter/HP/armor、8种族能力/修正、12区id/XY/朝向都与数据模块、原静态收据一致。重新定位1571/1512/29649/48118/15913等10个函数的签名和body，按只读SQLite坐标seek各WAT片段，未全扫大WAT。Windows EXE的9组HP/armor与12组XY共21个8B模式再次各找到唯一位置；这仅是静态数值对应，不是Windows ABI或运行验收。

每例输入是显式空selectedProfile376与borrowed flatquery128。完整profile376前后不变，class/race、seed/GUID、region长度与empty字段核同；region指针是实际分配观察，不预测其数值。查询的4个明列字段是V120=flat1、V116=高度、V56/V32=FFFFFFFF，其余5A保持，完整128B前后相等。1571传V+8给29649，所以该函数相对112/108正好是V120/V116。此视图**不是Rc owner、缓存world6760、自然App/profile生产者或可直接延伸完整游戏的生命周期对象**。

## 独立数值与物理范围

空profile1512按原顺序逐次舍入f32：读取新职业HP/armor，累积种族修正，得到23个derived值、HP/辅助池、速度与三个逻辑BTree键值；没有调用作者shared135/138数值实现。1571四路u64种子混合/rotate与初始完整starter/racial80B记录另写重算。所有162例使用普通PCG seed分支；退化fallback保留静态规则，动态覆盖仍为0。

- 每例2592B中独立构造502个known byte，合计81,324B逐字节一致。
- 剩余338,580个None保留，其中23,708原件字节非零；没有把未写/未知指针或inactive payload当成0。
- canonical mask由审查者独立组成，并与冻结期待逐cell核同；包含新timed592/596/600、active84 640/644/648、reserve764/decay752及byte768，不沿用旧物理偏移。
- 完整80B记录和23属性/初始标量/RNG/位置/朝向/计数/标志相等。这里只验声明502B，不称完整Game2592全部重建。
- 逻辑BTree键值、80B记录内容、226 payload均有输出；物理BTree节点、owned堆backing、packet metadata/backing没有导出，不能声称审查者独立重读这些物理所有者。

## 速度消息与失败保留

夜精灵修正使newSpeed=f32(1.08×7)，与旧7差值大于0.01。原1512调用48118，发送完整226：packedGUID + 旧sequence1 + newSpeed:f32，随后G1644为2。独审重做全部GUID mask与字节序；40个完整226逐字节相等，40例G1644=2，其余122例保持1，队列count与包数同。

首次151例原件已成功执行，但作者模型有9个+1644已知byte期待1/原件2的差异；这9例均是职业×种族矩阵中的夜精灵。旧receipt SHA `fe4f3eb0b8cd118597208f7efa9898bd9e966794efbe7672b8dcaed595a9158a`及旧全部source/artifact再次核hash，原失败目录未覆盖。

最终162同时扩展了语料：新增11个GUID mask样例，并将原随机矩阵中的20个human改成nightelf。**它不是前151例全部同输入重跑。** 审查者按旧151各自输入重算，确认旧9个错误和旧raw队列中的9个速度消息计数；旧payload当时未捕获，不补称完整。修复保留全部原498个known byte，+1644仍为已知并正确1/2；新增+1888的4个known byte到502，同时投影新增action_sequence/movement_packets，未通过删字段或改None过关。

## 收据与边界

原Node63071 exit0、4.8596s/60s、PID/PGID均消失；878导入全拒绝/host0，20,643,840B/32MiB、810次stack检查。验证器自有45秒终态也核同且已消失。没有旧快照、App、externref造值、网络、存档或phase1。

最终独审`evidence/initial138-independent-review-owned-20261101T235611.111917Z/review/review.json`，SHA `93f16b753213ba61d77e62fa0175c3d333034c5b8d4d5eea7464da19f301c454`；独审79283 exit0、2.8128s/60s、双missing。首次完整162通过收据与随后“误以为全部同输入”的reader拒绝均保留；最后仅修正审查者的历史输入绑定，未重跑原件/作者模型。

未完成自然账号/profile生产、完整堆/BTree/向量、world/cache6760 bootstrap、opening1087/phase1、连续138流程、原生Windows或完整一局。原135和其它138组件通过均未转计。审查者未改作者源、primary或registry。
