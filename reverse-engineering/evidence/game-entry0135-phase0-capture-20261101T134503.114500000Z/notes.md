# 真实phase0快照：固定采集API只读验收

输入为`game-entry0135-probe-20261101T134058.996329Z/original_game.memory`，718,995,456B。流式SHA与receipt.runtime.capture及result.capture一致：`6a90ac8797c954d2a9f520228e5826a40111ad338f7231fa57d34675b90256e4`。固定采集源前后SHA均为`a71c5f71a7d92d2e4a3b73f767c4618d8774b9ff827bb70856aff3049c48bfc0`。

按要求执行原CLI `--snapshot ... --app 22624720 --output capture.json`，未执行原件、未改采集源、未补任何数据。CLI退出0，耗时0.907s，`capture_complete_for_declared_schema=true`，boundary空；声明范围累计复制5,959,148B，未触发默认16MiB单范围／32MiB总预算。JSON为21,200,786B，SHA `241fee7fce6dd59f780a7cf5f49d25a562d414f009387330d2309032f04f6fb9`。[核对与字段摘要](summary.json) SHA `275c8ff9c0d26f0d9fa5b347530417216d282b4c33c82331934d96e2ecc31fcb`；[独立封装脚本](capture_and_check.py)可审阅实际执行与检查项。

- App22624720，内联G22624736，tag0；mode0、individual phase0、global phase0、clock0，running gate为false。与同份frozen copy的producer header一致。producer记录123次正常完整880返回，0次running返回、0次clock推进。
- 玩家class1／race1，level1、XP0、gold0，sourceGUID14443884；XYZ位模式`3323121664,3290316800,1116212265`即`(-9396,-633,68.02375030517578)`。owned cap1/count1；其余实体／pickups／companions／special／windows／boundary向量均空。
- owned实际definition5467428、ID`cleave`、execution5；racial definition5476580、ID`perception`、execution9。旧`headless135.supported:135-138`不能支持cleave的execution5，这是实际输入下确定的ability边界，不能绕成execution0/2。
- world Rc与App cache同为285646856，观察到strong2/weak1；flat byte0。tiles cap19/count9，bounds cap9/count9；9个tile各256个chunk，共2304个chunk，每个vertex cap/count145。nav为78,400B、width280；primary sentinel absent；secondary为313,600个f32、width560，共1,254,400B。原nav／terrain／secondary全部按默认预算成功采集。这是一份非flat world输入，不能因此继续向移动／死亡placement等旧接口硬传flat／navAbsent。
- player keyed tree原header为root0/depth1，当前无节点或key；保留原值，不推断player对象完整树已经产生。尚无opening NPC，故此副本不能验收NPC未写129B的后续liveness。
- transport vtable1495776，holder14549552→cell14549824；ring cap4/head0/count0，command232 cap0/count0、dangling pointer8。空队列只表示本时点为空，不能证明上游未产生消息。

`capture_complete`仅表示这份副本在声明schema及其预算内读取成功，不表示全对象图／owner生命周期已恢复。producer本轮仍有asset-file-budget触发的HTTP500及renderer boundary，并且Game停留phase0；此处没有修复或重跑这些边界，不能称为健康完整开局。`result.memory_bytes`是后续live尺寸；本次仅以capture.bytes、同冻结copy的header与文件hash绑定718,995,456B副本，未把后继live memory混入投影。
