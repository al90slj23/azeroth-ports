# Fixed135 strict400 CAS组合只读独审

**通过已声明范围的独审。** 结论绑定fresh目录`opening-combat0135-oracle-20261101T173256.931310Z`：400受控帧、4次选卡、5604阶段、5606原件入口，原比较0差异；固定`0.135.1 / 90898d5e3`，98份当前/冻结源SHA及85份生产AST闭包全部一致。[独审收据](../evidence/opening-combat135-cas-independent-review-20261101T175230.239980Z/review.json) SHA `376b09cd9ce10da25396d815824432e48eb456dbb1aeaea9674db95d25aa6482`；[JSON报告](2026-11-02-opening-combat0135-400frame-independent-review.json)。本次未执行原件、模型或checker，新增original case和完整880帧均为0。

独审100.301秒，低于120秒预算，每100记录保存进度。6008条完整logical记录合计1,662,490,742B，逐条logical SHA、累计SHA、原字段和全部blob/child edges/occurrences均校验；累计SHA为`814cdb65300a5bd66d80e3801efda5b1f8cf97c260f1e92124b5e6a03712fb8f`。16,316个blob共83,331,346B、1,085,989次展开引用，CAS stdout gzip496,272B；gzip为完整单member，envelope stream bytes/SHA与runtime一致。expected为5605条、193,142,479B原始JSONL，另核完整gzip与SHA。

传输明确依赖已[26类负例通过的root decoder](2026-11-02-opening-combat0135-cas-codec-review.md)，固定SHA `16ca91ea52fdb107988d2f9c0c7b8d3b069d21df13f5a1b6091dd8ddb1199049`。本审阅使用其private copy，仅将`_string`的`json.dumps`改为同样保留surrogate guard的`json.encoder.encode_basestring`；没有改validator或FloatToken。完整A/B性能收据SHA `364fc922efe85faae19ea1814ef128b29670c680123b56298524980cf94c04ed`证明两版6008条的逐条与累计SHA、所有finish结果相同，解码63.727秒→44.080秒。正式98源没有应用此优化；旧171633 archive仅用于性能等价，不作为第二个游戏验收case。[审阅依赖身份](../evidence/opening-combat135-cas-independent-review-20261101T175230.239980Z/reviewer-source-provenance.json)单独保存。

| 独立重比 | 数量 |
| --- | ---: |
| 严格记录字节 | 23,538,261 |
| projection叶值 | 781,515 |
| vector形状字段 | 112,100 |
| 阶段身份字段 | 11,208 |
| 合计，与原comparison完全一致 | 24,443,084 |

21,862,027个未知字节位置均受恢复的active写入掩码或inactive backing范围约束，其中13,824,115个原件字节非零；另有11,615个未写pickup arrival word。19类vector header、真实capacity、完整backing/SHA、raw Game/App/world持有关系、clock、RNG、候选语义与全部声明scalar独立核对。四个guardian的2804份owner capture、11,216份payload全部按GUID与当前index绑定；U68仅44,864个物理pointer字节未知，其3timer backing、静态44B记录及28B header严格比较。原件静态image仍由初始零内存和全部active segments顺序覆盖重建，没有模型literal或snapshot声明fallback。

4次选择依次为thunder_clap、升级thunder_clap、升级cleave，以及frame379/action382的tier1 battle_shout/index0。新learned80的初始CD为0.5；真实player入口在raw frame384/stage5380、第6次player tick施放。独立核对kind8、spell6673、完整64-bit owner0、强度0.4、expiry约49.6999855秒、CD约20.8320007秒，以及完整owned80与23派生字；当时damage multiplier约1.51999998。live+16的原件word为**0x5800008f（非零）**，仍只将这四字节声明为未知，不能填0。三套attempt ledger的完整payload验收属于独立Battle Shout组件，本组合没有扩张到未捕获的ledger堆内容。

最终level5、XP6、gold53。vector最大units12、pickups7、owned3、live32为2、special4、windows2、boundaries69。effects120、delayed56、hits112、active84、timed12、deadline32、secondary112、XP/currency queue这些只声明count的域始终为空，没有非空payload的count-only伪验收。packet最大905条，完整payload保存并核捕获结构，未建模的payload语义仍仅观察。独立Dijkstra重算78,400格、seed39340、可达72,660，u16 SHA `66afda2e7f733aebcf4f9204bbaa989b8d9310b317a1bcd6b9a23c1d65c71d32`与所有原件map digest一致。

原件Node PID/PGID72778退出0，process-terminal明确`deadline_exceeded=false`，60秒`child.wait`及stack/878 host deny/256MiB WASM/512MiB heap边界保留；审阅时PID/PGID均missing。comparison的161.865秒包括父进程CAS与expected复核，不能解释为Node运行时间，也不能据此伪报原件实际秒数。所有原件非export section和原callee完整保留。

本结论限一个human warrior、seed0、navFalse、静止约40秒的受控14阶段组合；仍显式依赖独立预解析world、原件snapshot上下文和外部f32clock。不是完整880、native Windows运行或完整一局，不与120/250帧、组件或旧400批累计case。新审阅脚本SHA `d65b449185ea0ab448ce34ecdcb64942e25badba42e04009e3bf4ee3261d45e3`。
