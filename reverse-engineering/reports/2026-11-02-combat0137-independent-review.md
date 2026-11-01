# Fixed137 combat数值域的只读独审

**通过已声明范围的独审。** 固定`0.137.0 / d171b8f9f`的既有80组、125次完整原913调用，全部432B单位记录、G984 f64与RNG的比较相符。本次只读取原件字节、冻结输入/expected/输出和源代码；没有执行原件、生产模型、builder或checker，没有增加original case或完整游戏帧。[最终独审收据](../evidence/combat0137-independent-review-20261101T165245.268006Z/review.json) SHA256 `ed989d9ed22a20bbc9ae173432bdf8c3b2a1151fb424073cc51bc2d2107b2d33`；[结构化报告](2026-11-02-combat0137-independent-review.json)。对应原[comparison](../evidence/combat0137-oracle-20261101T163523.434970Z/comparison.json) SHA为`d6a8a3e4ea448f933f8e01b871193e597ca42f52549df1471d4dcb68cdb1c72c`。

独立解析原WASM确认真实伤害入口为913，签名`(i32,i64,f32,i32,i32,i32,i32)->void`，body区间`[2372939,2399389)`、SHA `6d151d679785bc113d37f4a551974c979f3cc0d4653666b8e5362575972a1d3a`；137索引914确为六个i32参数的其他函数。私有模块只增加913函数与global0两个export，保留原export次序、malloc91933及所有非export section的完整原字节，没有应用入口或start section。完整913原callee未改。

审阅器另用`struct`进行逐步f32舍入，独立重算125项操作：118项非致死接受、5项phase拒绝、1项dead marker拒绝、1项目标不存在。重比55,296个完整记录字节，接受的单位写入仅限目标U288..291；每步G984与四词RNG均与原件输出及冻结expected相符。17项操作能区分真实f64累计与f32累计，原WAT也明确为`f64.load984 → f32.min → f64.promote_f32 → f64.add → f64.store984`。不是只核对最终HP。

新`(school & 254) == 2 && U372 > now`分支实际触发3次，严格边界及其他school均有对照；+0.1项位于phase乘数之前。432B stride、移动后的416/420 phase字段、kind2链接保护与完整记录尾部也核对。新增380/384字段没有恢复语义，但本输入的完整字节被保留和比较。

前提是显式完整已知的受控432B记录、空item/spell/proc sources、context0，以及本批非致死/noBoss/kind3 continuation域。**7个phase fixture（case73..79）使用U64=0、U68=0的显式输入；该数值分支没有消费timer或destructor，因此不证明这些记录是完整有效的特殊NPC owner，也不证明137 constructor已恢复。** 没有将这些零升级为自然开局生产规则。4项pending检查只核对既有纯模型收据及停止边界，本次没有重跑它们。

11份当前/冻结源SHA一致，4份生产文件只依赖通用数值模块，AST未发现直接IO、进程或eval调用。原件进程PID/PGID76087退出0、2.347秒、审阅时均missing；80个fresh实例，285项allocator/913入口栈检查均返回1048576，878导入全deny、实际host0，峰值20,578,304B低于32MiB。命令具备512MiB heap及60秒预算。原件统计、包与视觉等其他Game/heap副作用没有独立预测，不把它们算入数值投影验收。

137静态profile的完整WAT SHA及642,613,248B SQLite SHA重新核对，数据库保持0444并以`mode=ro`读取；实际四表计数为175,327函数、824,576调用、5,193,343整数常量、5,536,899内存指令。分析工具均exit0且PGID消失，producer已完成并消失，lsof收据exit0。原ps受权限限制仍记为`unavailable_not_negative`，没有伪报可观测。profile manifest SHA `d2370cc52637d96b1635ce8ebb75b798a411eeb5b7682a75867f5b1e0fc9565a`。

Windows137只作数据静态互证：重新核对12个NPC各45B标量尾部、UTF8名称及真实PE64名称指针，测得WASM声明stride72、Windows声明stride80。EXE SHA `aa6b254f905e2f7a4cbc7c2c8f11af822ec362e3d2b8e84cabd8c38893a10dc8`。这些事实不确定Windows伤害函数地址、调用ABI、Game/Unit布局，也不证明任何原生运行结果；没有把WASM的432B Unit布局套给Windows。

本结论限于非致死、空proc的伤害数值组件；死亡/XP/掉落、137增强萨满proc producer、constructor/opening、完整880、Windows运行与可玩重建仍未验收。未借用135/136动态case，也未将pilot与full求和。审阅脚本SHA `b0f10b38d2696324fc47ce20b2d4f231b295cc19cbfecba846ae0c467962b449`；其纯读取helper SHA `eef4d27841357cd445bb250e0d60803d5efe965bebdf58d61d5fc7934f23c152`。
