# 连续开局战斗接入40秒资源生成

固定 **0.135.1 / `90898d5e3`**，原WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。human warrior／Elwynn／seed0／静止玩家／navigation False，真实候选优先已有升级否则第0张。

新批 **500受控帧／4select／7004阶段／7006原件入口，声明投影0差异**；99源含86production前后相同。最终level5／XP20／gold64，时钟49.99980926513672秒。真实6730/1089与14阶段原入口保持原callee；不是完整880或Windows运行。

[原件差分收据](../evidence/opening-combat0135-oracle-20261101T181700.263141Z/comparison.json) SHA `2ce0181ba4f9303213d6038e9e0f5001c361dcddb771086b609ca96ff356dd71`。独立预期在原件前生成；原件输入只含动作与构造参数。完整7508逻辑行共2,437,042,742B；CAS20696唯一blob／123,298,206B，逐行/滚动SHA与1,476,054引用完整验证，没有删阶段或字段。原件owned78734退出0且PID/PGID missing，60秒子进程deadline未超；报告中的127.616秒含父进程后续比较。

[500帧独立只读复核通过](2026-11-02-opening-resource-combat0135-independent-review.md)，receipt SHA `cd9b122b6f004552c84d2efde8f8d61b313af9fb102cd010e8ee5887911d92e7`。完整CAS、99源／86production、31,918,511已知叶、guardian/Battle及首次资源RNG/字节/169均核。首个审阅器收尾常量笔误失败批保留，修复后完整重审；审阅器未执行原件/model/checker，不增加case。

旧headless也在当前源码及新deadline投影下[重放8seed／1614帧／22607阶段／11select](../evidence/full0135-oracle-20261101T182527.169824Z/headless135-comparison.json)，0差异，计数不加进本连续case。

## 实际接入的规则

`HeadlessState135.next_resource2444_bits`由真实初始标量40秒初始化，不再每帧取不可变初始值。顺序为本帧玩家/死亡/拾取/claims→ordinary947→资源切片→special2376；947中间的G2440、G2424/Boss段及其后G2448仍以未到期守卫限制，不能把两段组合称完整947调度。

第一资源在**第401帧（0起始400）**、f32时钟40.09996032714844秒触发，G2444写为f32(now+45)即85.09996032714844秒。本批kind5／visual9008／amount3146146168／GUID17370383913897164969；amount是种类draw之后的RNG state0，未解释成经验或金币。

使用同一world、最新ordinary RNG/counter/velocity与当前完整pickup物理vector。资源追加同时回填56B backing、active count、capacity、semantic records、共享RNG/G2408及deadline，保持G2412不变。旧slot的+4已有非零arrival word如实保留，未补零或新增mask；该帧资源位于collect之后，下帧才可能消费。近身kind>=2消费者仍明确pending。

新增逐阶段比较G2444及全部resource单actor169的GUID、完整payload、数量与队列顺序；其它完整捕获wire语义仍只观察。组件[64组1417/947及独审](2026-11-02-resource-spawn0135-independent-review.md)单列，不加进这个连续case。

## 原始资源入口与下一边界

[raw451→world→opening→500模型收据](../evidence/asset-combat500-owned-20261101T181719.658025Z/model500/receipt.json) SHA `562309d015a695934f02344daeea1c9d6d54b4313ed5a2c55522c001e1ffef7a`：67,281,330B、93源／资产前后不变、不读原memory/WASM/预解析world；500帧／4select／7005摘要（含opening）。owned78574退出0/missing，179.796秒／300秒限。

[44项终态衔接](../evidence/asset-combat500-owned-20261101T181719.658025Z/projection-bridge.json) SHA `3fe02192f59ec50a7101236ae1d182b20524c297cc017f1b10da786f2be6577d`：共同terminal字段、七vector物理backing、guardian、资源169、86共有production源及三world SHA均一致；不新增原件case。

[同一固定实现的纯模型延伸](../evidence/opening-resource135-model-boundary-20261101T182112.106492Z/receipt.json) SHA `8a4d3d8c3585afda86283bc03698b4df31a3848a15b828ef846f59186327e71f`另到600帧／5select，下一帧因G2424和G2448到期返回pending_due_event。它使用独立预解析world，**500之后没有原件差分，不能称600帧通过**；也未自然验证85秒第二次资源调度或cap2连续路径。

## 修复与证据边界

首次接入遗漏内层tuple转换，expected-first在首次资源处报TypeError，原件未调用；旧失败目录181407及主动停止的raw181501/owned70051保留，不加原件case。修复后完整500重新运行并通过上列独审。

正式CAS decoder只采用既有全6008行A/B等价基准的一行encode_basestring优化，FloatToken/surrogate、路径/引用及字节SHA守卫未变；新[codec两正例及26负例](../evidence/opening-cas-codec135-review-20261101T181343.524929Z/review.json)全通过，receipt SHA `fa66c3ba5a9aa13e118ec04fc694ed63cffae5efbba5391c76d3ec63410795d3`。旧400收据与源码快照保留原身份。

[官方metadata重新核对](../evidence/official-latest-goalcheck-20261101T181528.650406Z/receipt.json)截至2026-11-01T18:15:28Z仍为0.137.0且EXE SHA与已固定137相同；未重取大二进制。本135结果不转计137。原件snapshot、locale、外部clock与预解析world的依赖均保留，raw资产独立生产另层陈述；本批完整880／native运行／完整独立一局均为0，最终目标未完成。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reverse-engineering/scripts/check_opening_combat135.py --phase full --frames 500 --capture-format cas
```
