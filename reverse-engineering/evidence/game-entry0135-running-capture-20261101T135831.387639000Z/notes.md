# 真实自然running Game：固定采集API投影与独立交接阻断

输入`game-entry0135-probe-20261101T135403.797895Z/original_game.memory`为1,378,877,440B；文件流式SHA与receipt.runtime.capture及result.capture完全一致：`c461b2f5efb1399127d22c04fbe5efed15f8b8411ceeefe22a05b4dce45bfd15`。采集源固定SHA `a71c5f71a7d92d2e4a3b73f767c4618d8774b9ff827bb70856aff3049c48bfc0`前后不变。

只执行固定CLI `--snapshot ... --app 22624720 --output capture.json`，通过Path.read_bytes取得不可变bytes。未执行原件／独立模型、未改源或补数据。[capture.json](capture.json)为21,535,323B，SHA `43cf55ee67df72ef588d6ae080646bda31900d1b33388b3cffd552183e937991`；声明范围累计复制6,120,808B，`capture_complete_for_declared_schema=true`，boundary空，无默认预算失败。[summary.json](summary.json) SHA `7c35affad088682c7284f256cfccf4ac1eaa9a3e4c71e88a9b980f43b2593909`；[entity-details.json](entity-details.json) SHA `04a179e5f52420916ca7eefbe04a005d0c70ea8504414a4ef569326ac327a5bc`，包含逐实体字段、8个running回调摘要与12份当前模型来源冻结。

## 实际状态

- App22624720／内联G22624736，tag0、mode0、individual phase1、global phase0、clock bits1049109516，即0.26590001583099365。receipt记录603次完整callback，其中8次running，后续7次clock推进；stack1048576、borrow0。同份冻结header与投影phase／clock／world指针逐项相符。
- 第一个running返回index595已经clock0.026且units7；此前phase0、units0。该880已完成进入及后续系统，**此副本不能标为1089刚返回或time0 opening**。
- class1／race1、level1、HP230、XP0、gold0；sourceGUID16251607。owned cap1/count1为cleave，definition5467428、execution5；racial为perception，definition5476580、execution9。XYZ为`(-9396.1064453125,-629.3634033203125,68.37271881103516)`，保留真实移动后值。
- NPC cap8/count7，全为活marker0、ordinary tags40/64/244=-1、definition5415572。前4个GUID低24位11..14，后3个86..88；结合constructor counter10、4NPC、2pickup、69boundary的来源顺序，与先生成4NPC再经过普通spawn产生3NPC相符。这是源顺序加GUID的推断，不是新增独立880验证。全部7条原424B／第8条inactive backing均保留。
- pickup cap4/count2，均kind2、amount分别2与1，GUID低24位15/16。到当前玩家的XY距离约32.64／29.70，仅为double诊断；未执行独立几何或kind2消费。两条arrival+4均为非零原字节，不能清零或当作已赋值到达时刻。
- companion/claim cap0/count0；special cap4/count4；window cap4/count3；boundary cap128/count69。不能把旧声明“两条零tag装备slot”的opening模型输出2companion强套此后继真实状态。
- RNG四word为`1410023936,3514236404,3278874267,3096624426`；spawn counter88、message sequence7、generation0，spawn-budget bits1041443813。各值均来自同一副本，未重置到opening／constructor输入。
- world Rc与App cache均24229960，观察strong2/weak1、flat byte0；tiles cap19/count9、bounds cap/count9，2304个chunk，每chunk cap/count145顶点。nav78,400B／width280；primary absent；secondary313,600 f32／width560。distance map为78,400个u16、field24=72660。完整世界范围在默认预算内成功采集。
- transport vtable1495776，holder14549552→cell14549824，ring cap4/count0/head0、commands232 cap0/count0；原G packet／notification队列亦为空。它们是本时点已交付之后的观察，不能拿来否认opening消息产生。

## 当前真实输入对应的独立交接阻断

| 阻断 | 当前真实证据／具体代码 | 下一步需要保持的状态 |
|---|---|---|
| 仍无from_opening交接 | `headless135.from_initial:112`只接受constructor phase0；当前phase1／clock0.2659。它还重建空unit／pickup／tail | 增加明确的opening/running交接结构，保留phase、clock、RNG、counter、7条NPC与2kind2、special／window／boundary及其真实capacity；不能先from_initial再覆盖或清向量 |
| backing被固定成128 | `HeadlessState135.__post_init__:98-99`要求128条area backing；`from_initial:117`同时预置128条zero424/88。真实unit cap8、area cap0 | 独立storage表示与增长策略必须接受实际capacity及未知inactive bytes；不能预填128个零slot |
| starter dispatch不支持 | 实际cleave execution5；`headless135.supported:135-138`仅常见execution0/2、RACIALS及已恢复area3；`step_frame:417-418`会直接pending_selected_ability | 在此case中，交接结构打通后的第一个确定语义阻断是execution5；恢复它比再增加旧尾切片样本更直接 |
| 普通NPC未知字节表示 | 当前7条U4旧值有6条非零、Q32有7条非零，但均marker0且tags=-1；旧decoder／UnitState／area finite／patch把这些字段eager读写 | 采用[已有required-read静态结论](../npc424-liveness135-static-20261101T133622.446797000Z/notes.md)，独立producer保留U4/Q32及其余未写cell为None；只在tag/dead实际消费时要求。观察副本有具体字节不等于独立allocator预测 |
| active special2376 | special count4且protection2576=0；`headless_tail135.guard_special2376:62-63`明确拒绝该输入 | 保留4条事件及window、boundary，恢复实际producer/consumer；不能清special或设保护位绕过 |
| 实际world未贯穿旧组合 | 此副本非flat、含真实nav/terrain/secondary；`headless135._cast_phase:194-195,211-214`死亡／area仍硬传terrain/nav absent，`step_frame:450-453`仍组装flat spawn输入；完整W→880前段也未接 | 已有world consumer可作为显式纯输入接入这些调用；不能用单一flat-height替代真实地形或将自然移动位置重置 |

在这份最终副本上，claims为空，不能再把“非空claims”列为当前立即阻断；timed／active／delayed／effects／deadline／secondary／hits亦为空。kind2当前较远，可保留idle输入，但其靠近后的真实回调仍未恢复。due计时器尚未到达，不能把未来due域当作本时点已触发错误。

本轮原件自然UI进入、完整880返回与clock推进的证据已取得；上述工作仅完成真实快照读取与问题定位，新增独立case／完整880独立帧数仍为0，未把观测状态导入称为独立producer或独立完整一局。renderer receipt为`no_renderer_error_reported_not_visual_acceptance`，本次没有额外宣称截图／视觉验收。
