# 固定0.135.1：真实Game进入后的只读采集接口

新增[scripts/game_entry135_capture.py](../scripts/game_entry135_capture.py)，把**调用者已经冻结的同一份linear memory**解析为App／Game／向量／消息／world等观察记录。它不执行原件，不构造或安装Game，不写phase／Once／Rc／cache，不连接网络或读取用户存档。当前是原件观察的输入适配器，**不是独立Game生产者**；尚未用本轮真实active Game验收。

接口为`capture_schema135()`和`capture_game_entry135(frozen_bytes, actual_App, include_world=True, limits=CaptureLimits135())`。只接受bytes，或**底层实际owner为bytes**、连续只读且format为B/b/c的byte memoryview；`memoryview(bytearray).toreadonly()`仍会被拒绝，因为原owner可以继续改写。冻结时点由调用者明确提供，reader不隐式复制view；CLI的`Path.read_bytes()`路径不变。所有后续指针均读取这份不可变副本。默认单向量16MiB、累计复制32MiB、普通向量16,384条、tree512节点／depth8；nav／secondary按16MiB的字节预算分别允许更大元素数，不把78,400／313,600误套普通record上限。这些是观察限额，不是游戏上限，也不是原WASM内存上限。遇界限／未知结构保留boundary及已读身份，不把错误清成空向量。

[当前schema JSON](../evidence/game-entry0135-immutable-input-regression-20261101T132916.525232000Z/schema.json) SHA `66ab26c53557440ac176ba44a5b735c8753612ad3400fc5d9a5e723832505042`；[不可变owner针对性回归](../evidence/game-entry0135-immutable-input-regression-20261101T132916.525232000Z/regression-checks.json) SHA `1993f57468525994e85e1881d6223836c80f4e7b381d9b249e11522f6f2b75cf`绑定13份当前来源，capture源SHA为`a71c5f71a7d92d2e4a3b73f767c4618d8774b9ff827bb70856aff3049c48bfc0`。确认bytes／immutable-byte-view投影相同，可变owner只读view在任何hash／解引用前被拒绝，非连续／非byte-view被拒绝，CLI bytes快照兼容。输入仅128KiB合成字节，不新增原件案例或游戏帧。最终[来源冻结清单](../evidence/game-entry0135-immutable-input-regression-20261101T132916.525232000Z/source-freeze.json)同时绑定本报告。

修复前[schema JSON](../evidence/game-entry0135-capture-schema-20261101T131736.326551Z/schema.json) SHA `83649e8006690d085fe767826fc53416889da6bd57039e374c6a7b9bde8ee05f`及[原reader检查](../evidence/game-entry0135-capture-schema-20261101T131736.326551Z/reader-checks.json) SHA `e06628f5e36309c0fbf65830b3754b9ffec8d67f0e456469c8d20b5dd41b0eba`保留当时10份来源，未追溯改写。其小型合成检查覆盖边界、环形顺序及大栅格限额；原“只读view”等同不可变副本的缺口由[独立反例](../evidence/game-entry0135-independent-review-20261101T132657.322250000Z/review-checks.json)记录：同次投影曾能得到raw Game clock1.0、running gate clock2.0且complete=true。修复不把这些合成输入称为合法App／world生产。

[builder独立静态审阅](../evidence/game-entry0135-independent-review-20261101T132657.322250000Z/review-checks.json) SHA `f3a1150ba933263be65f107bf1299b5129d85ffd3e1a99c80ba68e9ede7f35a1`确认：原WASM SHA仍为`c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`；12个section中仅7 export改变，36→37只追加`research_game_entry135_stack` global0，所有函数／memory／table／segment字节相同，`wasm-validate`退出0，未实例化。模块SHA `0afef345401358710e1d08163721716cd61fb19c457821f6b30f1ce58aff23b9`。原global0的mutable位仍为true；**WASM export无只读权限位**，只读必须由host只读取`.value`保证。

## 必须保留的采集时点与身份

原App为已知真实cast定位的`Rc+16`，Game内联位于**App+16**。菜单Game tag2时不跟随内部对象；当前schema只解析已验证的present tag0，其它variant明确保留未支持。tag0本身不代表已开跑：mode0看G2587，非0模式看G2588；只有相应phase1且实际clock推进才有active运行证据。单份snapshot只能证明phase gate，不能证明时间推进。

建议在真实callback正常返回、borrow归零时各取一份同步副本：菜单；第一次自然构造Game后的phase0；第一次自然phase1；接着若干实际移动／战斗返回。记录原UI点击与W键down/up、callback序号、真实now的f64位、App0/8时钟字段和G2352的f32位。不得为对齐模型重置clock／RNG／position或复制另一个G。

如果首次观察到phase1时同一880已经继续运行了后续系统，就不能把该副本标成“1089刚返回”或直接与time0的opening expected比较。完整frozen副本、所有原件原始身份和host事件继续是权威输入；不能在异步分块上传时混入后继live memory。

## Game标量与向量

输出完整App5168和Game2592原字节；以下字段额外以整数位模式投影，不把未知padding解释为零。

| 范围 | 偏移 |
|---|---|
| 进入／phase | u64 G0 tag；u8 G2575 start、2582 mode、2583 deny、2587 individual、2588 global；u32 G2528当前调用者gate |
| 移动 | XYZ G1416/1420/1424，heading1428；动作tag416及420..436原payload；movement gate440/time444；velocity1736/1740、previous2428/2432/2436 |
| 玩家与成长 | sourceGUID1336 u64，class360/race361；level1432、XP1436、HP1440；23个derived words1536..1624及既有aux字段 |
| 时间与RNG | G2352、2364，timer1628，四word1720..1732；due2424/2440/2444/2448及其它已验initial scalar |
| 计数与统计 | counter2408、message2412、budget2416、killcost2420、pending2376、generation2400；outgoing984/incoming992按f64原u64保存 |
| world／对象键 | G2348 world Rc；G2368 optional distance map；player B-tree root2476/depth2480 |

30组已知stride的向量包含owned80、live32、units424、areas88、effects120、delayed56、deadline32、hits112、secondary112、pickups56、packets16、notifications12、candidates80、special40、windows8、companions/claims88、boundaries8、XP/currency8及已定位来源数组。完整偏移见可执行schema，主布局复用[opening runner](../scripts/run_opening135_oracle.mjs)、[headless runner](../scripts/run_headless135_oracle.mjs)和[initial runner](../scripts/run_initial135_oracle.mjs)。

普通Vec保留实际cap／ptr／count、**整个capacity backing**、active前缀和inactive尾部。owned-skills／adjustments／passives及auxiliary-motion只有既有证据明确ptr/count，容量未单独证明，暂只取active条目；G1952/1956/1960只保留12B header，stride不从dangling pointer的alignment猜出。其它未恢复字段仍在rawGame和完整snapshot中，不称完整对象图。

racial80和每个owned80还读其真实definition88与ID bytes，保留definition pointer及execution byte84。候选记录只按已验new／upgrade／gold tag读取相应payload，未知variant保留原80B。packet16读取byte-vector payload和u16 opcode+12，notification12读取原bytes，同时保留payload capacity backing。App4768/4772仅在原vtable1495776下跟随holder24→cell76：记录ring的cap/ptr/head/count、物理全部slot和逻辑有序payload，以及232B command backing；optional snapshot/rows仅保留原cell metadata，不猜完整生命周期。

真实880可能已经把G消息队列搬出；队列当下为空不能证明没有产生消息。应同时保留transport、host事件和前后副本，不能把opening模型的78包与任意后继空队列直接作差分。

## 已知读取与未写域

player B-tree按原节点count u16+50、keys u16+52、values u32+4、internal children u32+76读取全部节点，保留raw节点与全部有序key/value。旧模型只理解22/28/34/716/717/1109/1176；其它值继续opaque，不删除，也不把它们全部归为cosmetic或假定每个value都是同一种语义类型。

NPC424保留完整物理字节。opening producer只独立预测`(0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139)`，其余129B初始未写；**U4也在其中**。这是构造写集证据，后续系统可能写入这些位置，不能永远把它们全部mask掉。pickups56的+4在append时未写；area88、companion88和special40同样保留各自原mask与actual raw，active之后不据旧构造mask推断未来liveness。

world读取真实Rc124，tiles36／bounds16、chunk264／vertices12／holes，以及原nav bytegrid、primary／secondary raw f32位。nav32/36/40、origin44/48、width52；primary absent tag56、ptr72/len76、origin80/84/width88，中间布局不泛化；secondary92/96/100、origin104/108/width112；fallback116、flat byte120。其它tile/chunk字段只保留raw，不杜撰asset/owner生产。G2368的已验distance map保留28B header、u16数组与field24。

## `from_opening`接入的确切阻断

| 现有代码 | 当前阻断与所需工作 |
|---|---|
| [headless135.from_initial](../reconstruction/core_spec/headless135.py) | 当前没有`from_opening`；它要求constructor phase0，但OpeningState.initial已经phase1，并重建空实体／拾取／tail。不能调它后再覆盖phase与RNG来冒充真实入口。 |
| `HeadlessState135.__post_init__`与storage | area backing固定128条，from_initial也预置128条zero424/88；真实opening常见units cap4、areas cap0。需要独立支持实际容量和增长／保留语义，不能预填128个零slot。 |
| [opening NPC输出](../reconstruction/core_spec/opening_npc_pickups135.py)→[unit_records135](../reconstruction/core_spec/unit_records135.py) | opening含None字节，而decoder要求完整bytes424且读取U4等；不得None→0。可将实际未写字节作为显式输入保留，或逐消费点恢复liveness；前者不是独立allocator预测。 |
| 随从／claim | 真实opening的2条companion即同一G2108/2112/2116向量。旧original runner在collect/select前拒绝G2116非0，独立claim2573也只支持守卫域；不能清空随从。 |
| special／window／boundary | opening有4条special40及事件窗口、69条boundary GUID；special2376非空且未保护即被当前guard拒绝。旧state没有完整window/boundary及其消息／对象所有权表示，需保留并补producer/consumer。 |
| kind2拾取 | codec可保留全部56B，但仅在原几何guard保证不dispatch时允许idle；靠近时kind2回调未恢复。不能删两份kind2或改成XP／coin。 |
| world与移动 | 死亡placement、area producer、915及普通spawn仍硬传flat／terrainAbsent／navAbsent；真实world消费者虽已单独实现，尚未贯穿这些调用。W输入→968/2328、完整880前段/party也未接。 |
| ability／source／keyed state | 必须用实际class/race、owned/racial、passives、timed/active/modifier/definitions向量证明输入域；当前支持集合、活跃975 execution11/915/2602等遇未知即停。player其余key、其它实体所有权树／ECS容器与完整包交付仍未重建。 |

下一步应先用真实UI产生present／running Game并按本schema采集，再选择一个输入域明确的实际系统片段差分。该适配器不会把观察读回转换为独立producer，也不增加旧14尾切片的案例／帧数。原件完整active880与独立完整一局仍分别验收。

## 可重复的不可变输入回归

新增[`check_game_entry135_capture.py`](../scripts/check_game_entry135_capture.py)在每次新时间目录创建128KiB合成样本，验证bytes/连续不可变view等价、mutable-owner readonly view拒绝、原别名反例在读取前拒绝及CLI兼容；不覆盖历史证据，不执行原件。最近[回归结果](../evidence/game-entry0135-reader-check-20261101T140803.012230Z/regression-checks.json)来源为checker与reader两文件，0原件调用/0游戏帧。

```sh
python3 scripts/check_game_entry135_capture.py
```
