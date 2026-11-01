# fixed135 玩家移动2328：异作者只读独审

范围内通过。对象是0.135.1 / `90898d5e3`，不是latest138；同一原件函数2328的38例原件差分，不能解释为完整移动输入系统、完整主循环或完整一局。

## 新冻结批与来源拒绝

- 新批：`evidence/player-motion135-oracle-20261101T231448.187735Z/comparison.json`，SHA256 `840a034fc87e98a1b537924c1c1c99835a5b7bd424ad233089b8f9157afabd3e`；38/38完整原件调用，0差异，20冻结源、42本地导入边。审查者另写AST跨包闭包检查，逐一比对冻结/当前/运行前后SHA，未执行作者的closure工具。
- 旧17源批`230726.438946Z`缺少terrain135顶层执行导入的entry_resources135及dbc，已拒绝其“完整来源闭包”资格。旧证据保留，未事后补hash。作者先修闭包、核导入，再重新生成期待并完整重跑38例。
- 游戏和world输入来自历史真实after_begin1089快照（166395904B，SHA256 `23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf`），加明列标量patch。它们是显式实验输入，不是本批独立构造Game/world的成果。期待值由冻结生产模型在原件子进程启动前形成；审查者另从原件WAT、静态数据与快照独立重算，未调用该模型、原件、checker或builder。

## 独立核对

从原件2328恢复本批实际到达的Elwynn policy0/圆边界/terrain命中分支，并另写binary32、terrain三角形、次级半格高度采样、包序列化与Game赋值重算。原件WASM仅新增导出，原有其他section和完整函数体逐字节保持。

- 全38×8192=311296 Game字节、返回XYZ的f32相等语义、全部改变偏移和写集以外309936字节均相等。
- 30普通接受、6纠正、2 pending拒绝；pending清除4例；3例动作序号u32回绕；3次圆边界向内4单位夹取。低于ground−15触发纠正，恰等阈值接受。
- 完整6个199与3个150新增包逐字节相等，包括GUID掩码、旧动作序号、坐标/朝向和边界提示双尾零。队列容量/指针保持，计数与新增包数一致。
- 独立解码2318个快照world/terrain/secondary/nav来源范围，原始124B world前后相等。几何范围和既有78条queue prefix的后态不变依靠冻结原件runner逐范围hash/逐包断言；原件结果没有导出完整postmemory/既有包前后明细，审查者不能把它说成另一次原始后态重读。
- canonical byte/None输入的独立遮罩重算保留309086未知字节，2210已知字节与原件后态一致；未知464读显式拒绝。它是独立消费者重算，新增原件调用数为0，不给原件38例加计数。

## controller单独静态审查

`headless_motion135.py`的2592个cells从None开始，只将实际1560构造器写集的416/440/448/456/464/1744/1764/2496/2500设零。朝向链为map(5456016+152×zone)+116→local33→frame1516→frame+88复制→G1428；12区静态词与ZONE_ENTRIES逐一核同。

motion owner只持久化motion字段；位置/时钟/GUID/动作序号在每次边界临时绑定。416必须与headless的player_action_tag416相等，之后用实际结果收回；没有清416绕过_effects_phase的活动动作拒绝。queue1880/1884/1888保持未知，纠正需要读到它们时应拒绝，而不是造容量。入口保留phase1/mode0/本地peer/primaryNone限制。这一层仅静态核代码和原件构造器，不增加controller原件差分。

## 边界

未覆盖primary/aux/nav/polygon、计时纠正、无高度半径12扫描与ring-rescue；未执行完整968/17726/broadcast/peer路由；phase0到1089未覆盖。不能外推所有地图或完整输入生产者。原件38例：Node7750，exit0，3.8965s/60s，PID/PGID消失，878导入全拒绝、host0，内存166395904B/256MiB。

最终独审收据：`evidence/player-motion135-independent-review-owned-20261101T231757.215408Z/review/review.json`，SHA256 `9cf4dd7ad3cc8436d090efc558e1279fff15f08732eebd01738907b3cd1cdc22`。独审子进程12127，exit0，0.6015s/60s，PID/PGID消失。静态proof、controller源快照、所有失败独审尝试和终止收据均保留；生产代码与原件证据未改。
