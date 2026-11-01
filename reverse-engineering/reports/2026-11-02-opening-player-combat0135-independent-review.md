# 固定135：完整玩家live/Aura所有者连续750帧独审

**限定通过。** 新采集固定0.135.1 / `90898d5e3`、human warrior／Elwynn／seed0／navigation false／静止玩家，真实6730/1089后运行750受控帧、6次选卡、10,506阶段、10,508次原件入口。本审重新读取完整原件记录，严格重比声明投影并独立推导完整玩家live32／Aura48及typed opaque来源传播。原件、生产模型、checker和builder均没有在独审中重新运行。

[原件比较收据](../evidence/opening-combat0135-oracle-20261101T224816.309189Z/comparison.json) SHA `dc70b70714d05adbfded365abe954adf6d28a6447ebb09883f130935c5545f28`；[独审收据](../evidence/opening-player750-review-owned-20261101T225502.529952Z/review/review.json) SHA `a7b5a506a15a28f1640b14eb3d46d4cd3f353b95b06a742816f3975afecbae15`。原Node56467 exit0、PID/PGID均missing，72.199秒；独审70157 exit0、双missing，84.653秒。

## 完整性与比较范围

114份冻结源、其中98production，当前文件／捕获前后表／source-snapshot均逐一一致。独审自己10份依赖也冻结保存；仅导入只读审查算法和已审CAS证据解码器，不导入root生产或其`LiveAuxiliaryVerifier135`。原件WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`；所有非export区段逐字相同，完整callee保留，878导入全拒绝，实际0host。

- 已知值共63,946,427：59,447,445严格物理字节、4,236,309投影叶、241,661 vector形状字段及21,012阶段身份值，合计与primary完全一致。
- 51,485,323个物理None单列，其中原件36,810,893字节非零；21,959个未写arrival词和2,090个来源绑定kind2地址词分别核对。它们不能称为已恢复的已知值。
- 完整CAS finish：11,260逻辑记录／5,332,629,590B、33,724唯一blob／305,579,726B、2,799,102传递引用，逐条逻辑SHA、blob、出现次数和首末位置全核。逻辑SHA `72c83c9f1327919bd08a7b132310497da2ba43cf96cbc4133dc77607ceb4cbc8`。
- 每阶段raw Game、vector header、complete backing、队列metadata/payload和keyed字段投影均绑定。所有被模型声明的known字段严格重比，没有为了消除差异改成None。未声明的其它UI／wire语义仍不在验收范围。

这是一份新的原件750采集，新增完整玩家物理投影。先前750／120收据各自保留，计数不相加；独审不增加原件用例。

## 独立玩家所有者与事件顺序

审查算法从初始化空live/Aura、原始clock输入和固定指令规则推进；完全不调用headless模型。10507个opening/阶段快照逐个检查完整capacity和inactive尾，独立得到1次live扩容、10次dirty expiry、2次整32B移动、6次1020保护partial append、4次self-buff写入及20次Aura重建。

2088只在`now>=expiry`为真时启动dirty pass，随后用严格`now<expiry`向前retain整32B，尾部不清零，origin与物理行同位移动。属性／Aura／回血前缀只执行一次。选卡续跑先移除1020，append仅写0..11和20..31；+12/+16继承retain后的目标槽，并保留其旧origin。922 self-buff则先移除owner0同spell，再实际覆盖+16为新的typed来源，不能误当目标槽未写。

Aura正面槽顺序、expiry、marker、spell、application和48缓存重建独立推导；66个Aura对象键与原件值一致。当前Level独占HP／属性／时间／RNG，物理owner只持live／Aura及App通知上下文；prefix和2862各自从当前Level生成临时context，返回时原子提交并清空Collection.resource_context，避免跨阶段保存旧副本。

另读回[异作者Aura新分配静态证据](../evidence/player-movement135-static-20261101T224900Z/aura1202-fresh-allocation-proof.json)，SHA `555e63df4485c6d7b884fda9b59aa1959e55604b6ada11d3bc9f0616fb83d453`：原1202先分配768B新缓存并写48个marker，之后才释放旧G2004并替换header。inactive payload的12个未知字节来自新分配，不是原地将既有known字段改None。此为独立静态证据的指令/body读回，附于已完成主reader之后，不改变其冻结源或收据，不新增动态用例。

## 四份opaque源的现场绑定

原922 effect8/9的live+16来自尚未恢复的caller frame+48。旧“definition+8／零”推断已由[105反证审](2026-11-02-live-owner0135-105-independent-review.md)推翻，显式来源传递另由[109组件独审](2026-11-02-live-owner0135-independent-review.md)证明。本组合不把这4个源值变成expected输入。

| 完成帧／stage | spell／owner | 绑定内容 |
|---|---|---|
| 6／70 | 20600／racial80 perception | 新写入slot0，原件辅助词`0x4289add5` |
| 385／5380 | 6673／learned80 Battle Shout | 新写入slot1，原值仅作观察 |
| 427／5968 | 20600／racial80 perception | 新写入slot1，原值仅作观察 |
| 594／8307 | 6673／learned80 Battle Shout | 新写入slot0，原值0也不升格为固定零规则 |

每份token的frame、now、spell分别与原件阶段、f32时钟、持久basic/owned80以及固定88B definition绑定；该技能timer必须已到期且实际reset。本轨迹共有6次selection；这些未知源在各自出生后的保护继承、expiry压缩和inactive尾保留中，共产生15,562次同词传播观察，独立origin数组与root声明逐项相同。token中的attempt-count注记因原捕获缺完整三份ledger，只保留为未独立验证注记。

读审还确认SP-496地址等于2088 frame96＋1076 frame208＋922 frame240再加48的嵌套位置。但每个完整入口前后读取的该地址，只是未来定位线索；中间callee可能改写它，不能当作内层922实际读值证明。**caller栈源值仍未预测，观察值从未送入生产模型。**

独审自检1正例／7个破坏例全拒绝：known magnitude改None、遗漏origin、错误frame／spell／slot、opaque传播值改变、无producer的capacity变化。它们只是审查器自检，不增加游戏用例。

## 仍未覆盖的实际行为

本750轨迹的750次collect均没有自然消耗附近符文，App通知计数一直为显式输入1。资源3／4的retain/partial append origin接线与kind5无live变化已静态核对，但不能据此声称自然mixed资源闭环已经运行通过；[61／119共存组件](2026-11-02-self-buffs0135-independent-review.md)与[混合拾取组件](2026-11-02-mixed-pickup0135-independent-review.md)的各自范围继续单列。当前human-warrior域也不新增kind7 incoming清理或kind9自然caster验收。

原件依然使用合法历史snapshot，模型使用独立预解析world，时钟为外部f32调度14尾阶段。没有完整880、Windows运行、最新138完整流程或独立完整一局验收。现有安装包和存档未改动，研究目标保持未完成。
