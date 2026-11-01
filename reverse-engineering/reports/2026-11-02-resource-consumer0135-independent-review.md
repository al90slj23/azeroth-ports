# 固定135资源消费与aura的只读独审

[最终130例/244阶段原件差分](../evidence/resource-consumer0135-oracle-20261101T203315.893397Z/comparison.json)通过限定范围独立复核，原收据 SHA256 **`970e32ef5af326ffd665b488a43f949eb8bd9e3192d6ffd7e2c121b78636c963`**。这是固定0.135.1／实际9字节build `90898d5e3`，WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`；历史alias `0898d5e3`不改写，135辅助pool物理字段为**G768**，没有套用137的G764。

审阅器没有执行原件、生产模型、builder或原checker。31份冻结/当前源在审阅两端SHA一致，独立AST核84条本地依赖边、24份production闭包，生产源无文件/动态执行/子进程调用。5份审阅器本地文件冻结前后来源见[源码收据](../evidence/resource-consumer135-independent-review-owned-20261101T203921.645035Z/reviewer-source-provenance.json)。私有模块只加10298/2862与stack export，全部非export section和原函数/callee均与原件逐字节相同。

## 独立重建与完整重比

本审阅独立从固定原件静态class/race声明和按顺序live来源重算23个派生词，先检查每个case的初始typed基线，再逐操作重算资源影响；没有把初始derived当作不可检查常量。覆盖九职业、四race的本组件既定子集、已有正Battle kind8、资源刷新及expiry guard；不推广为外部装备/天赋/负效果的完整来源恢复。

- 163次完整原10298直接入口＋81次完整原2862入口＝244次外部调用，130个fresh实例；完整2862实际嵌套消费29件资源。因此实际效果为192件（speed71、berserker66、heal55），不能把嵌套效果再算作额外外部调用。
- 32B live所有owner的同spell稳定过滤、57次匹配删除、70次容量扩展、已知与None +12/+16字节及inactive尾部完整重建。普通同spell去重保留first；774按其独立规则累积并取最大expiry。
- 56B拾取先以入口XY执行binary32距离≤3选择，Z与amount不决定本域资格，再按逆序稳定compaction并保留完整inactive尾部。marker0/1均比较实际170 destroy，far kind2的unknown amount保持未读，未把其它消费者伪装成成功。
- speed23451为10秒/+0.6速度，berserker23505为15秒/+0.5伤害；heal23493为50%maxHP，再按gate387>4减半并封顶。RNG、spawn counter和message sequence保留，42次实际速度变化及action sequence226独立核算。
- 48×16B aura cache完整重建：137次rebuild，87次强制初始化、50次有效旧48-cache比较；独立推导本域5,802次逻辑键写规则。47..94 spell、95..100 packed flags、113..124 applications共66个可写key，101..112保持不写。inactive行仅tag4B已知0，余12B为未知新allocation字节。完整逻辑BTree字段集合和数值均比较，非仅挑出三个numeric key。
- 82,981个已知值完全一致；101,062个明确未知物理字节保留None，原件其中14,777个实际非零。每个None位置还由独立重建的完整live/pickup/aura backing约束，没有放宽成任意标量mask。

所有244阶段均绑定完整8192B原Game观测中的派生、HP、速度、计数器、RNG、G768、vector形状和aura initialized字节。完整Game未投影字节、物理BTree/malloc身份没有被声明为预测；本动态采集比较最终logical-key值与稀疏key集合，不宣称已经动态观察每次键写入的先后或ECS投递。

## 完整wire与通知owner

最终`packets_known`直接等于原件queue.active，**没有按opcode筛选后只比较170/306**。实际新packet事件为306×192、226×42、150×192、170×29；累计阶段队列观察840包、通知JSON累计346次，分别记账而不当作840个新事件。

独立重建packed GUID（包括0与u64MAX）、spellgo306、旧action sequence携带的226、**type6** chat150及每件资源的完整JSON；比较所有字节、长度、终止符、JSON字段顺序和packet/notification队列顺序。150不是growth的type10或旧误推type5。完整2862每件资源保持`170 →306 →可选226 →type6 150`的顺序，notification JSON也逐件同序。

从原件静态声明取出Speed/Berserker/Restoration Rune英文名称，复核29537→19964→82070真实locale入口与cold Once0自然初始化；112个实际消费case已初始化、18个far无消费case保持cold。原件没有注入Once或字典。这里只证明显式English标签域，不把它写成中文通知已恢复。动态130例中的active live expiry均有限；NaN expiry的aura短路另属先前静态/纯模型检查，不扩张为本批动态覆盖。

通知ID源是原件**全局word14340336**，静态初值1；42920先读取旧值并u32+1，再分别10434序列化JSON、15915生成chat字段、22747编码150。每个case的1/0/FFFFFFFF是显式typed输入；审阅核其完整序列和一次FFFFFFFF→0绕回，不能把其全App生命周期说成已自然恢复。该global不是G2412 message sequence，也不从已有packet数量猜测。

## 静态来源与进程

以RO SQLite逐函数seek核17段WAT和原二进制body/SHA，单段最大98,121B，未全文读取1.3GB WAT。包括2862/31732/10298、1512/1202、aura helpers29629/30834/23583、heal/306、通知及locale链。完整body和静态内存区间见[静态证明](../evidence/resource-consumer135-independent-review-owned-20261101T203921.645035Z/review/static-proofs.json)，SHA `031a7193945999ffa69579c035154e0f7361c9b0f771cc640bfdf72fe9ea4db7`。

原件PID30502，exit0、3.9580秒，578次stack检查全部恢复，0实际host调用，memory峰20,578,304B/32MiB。只读独审PID39480，exit0、0.8078秒；PID/PGID均实际检查missing。审阅[最终收据](../evidence/resource-consumer135-independent-review-owned-20261101T203921.645035Z/review/review.json) SHA **`e4fea3e425135d6db469e5261749ff843f1e86b3a19fe2a82a250e909a7a8036`**；[机器可读报告](2026-11-02-resource-consumer0135-independent-review.json)附进程与来源。

首个审阅尝试203853因审阅器误把1202的`i32.load/store offset=2000`写成寻找`i32.const 2000`而失败；修正审阅器该静态语法断言后，203921完整重跑通过。失败终态和源码快照原样保留，未修改生产源或原件收据；它不是原件失败，也不是正例。

## 保留的未知与历史失败

新130批只在纯模型中拒绝marker2与nonempty claims。另核同版历史[1417 marker2失败批](../evidence/full0135-oracle-20261101T190005.927219Z/supply-kind2-comparison.json)，SHA `4f8d02ce08e0fd3b0ccca538090dadef50ff1c709cfa20bdcf8734ceaa5b51c4`：旧runner finally以`Stack not restored`遮盖原trap，没有final runtime。因此动态只证明该原件调用失败；31732先compaction后无效marker异常属于同body静态定位，不能说本次完整2862 marker2新执行已验，也不能从该失败批宣称0host/0diff。137失败不转计135。

这是手工Game8192/BTree/live/aura、真实cleave默认声明和显式empty外部来源的组件域，未调用原constructor、未读snapshot，不是完整world或自然开局主循环。非空claims/auxiliary GUID、XP/coin及近身kind2消费、装备天赋/definition38/负与控制aura、重复kind8 dominance、非英文通知、全App通知ID生命周期、完整UI/network仍未恢复。完整880、Windows原生运行和完整独立一局计数均0；主流程接入需另验，不由本组件通过代替。
