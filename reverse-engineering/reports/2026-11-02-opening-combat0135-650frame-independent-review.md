# 固定135连续650帧的只读独立复核

本次对[新650帧主收据](../evidence/opening-combat0135-oracle-20261101T200425.298468Z/comparison.json)完成限定范围独审。收据 SHA256 `16a86a82820ee8f737b256a458b252546336b20b6cd887d3c45e755f9ba538b1`；原件为 **0.135.1 / 实际9字节 build `90898d5e3`**，历史截短 alias `0898d5e3`不改写。完整原件 WASM SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。

审阅器没有执行原件、生产模型、builder或原checker，没有新增原件case。仅执行独立审阅器、此前的只读审阅辅助函数及明确声明的冻结CAS格式解码器。审阅源码和6个本地文件的前后SHA见[独审源码来源](../evidence/opening650-independent-review-owned-20261101T201707.724375Z/reviewer-source-provenance.json)；CAS解码器 SHA `f9ace95818b6384ad2663d293a07d036efc0aac52c8cd75fdabb3ec82065cd2c`，引用[2正例/26负例格式验证](../evidence/opening-cas-codec135-review-20261101T200414.243123Z/review.json)，其收据 SHA `079deca782201acd886c713ce8a3eb462189f1d9ca16233d140a81a1edc42115`。

## 已核实的范围

- 原件650受控帧、5次实际选择、9105尾阶段、9107个原件入口（含1560/1089），声明投影0差异。终态level6／XP32／gold77；这是1个人类战士seed0、navFalse、静止轨迹，不能推广为全部职业/地图或完整一局。
- 重读全部9759条CAS逻辑记录，共3,952,877,407B，逐条逻辑SHA、节点依赖、2,182,919次完整逻辑引用、28,155个blob及所有出现次数均核对。unique blob215,567,259B，完整单成员gzip806,177B。未删除阶段、字段或队列。
- 104冻结源与当前源在审阅两端完全一致，90份production由独立AST闭包重建。每份production禁止文件读取、动态执行和子进程调用。私有研究WASM只增加export，全部非export section与原件逐字节一致，原函数体、callee、数据与启动行为没有替换。
- 47,780,952个已知叶重比：44,639,760个物理记录字节、2,940,862个投影叶、182,120个vector形状字段和18,210个stage身份叶。35,198,032个None物理字节保留其明确未知身份，其中23,343,519个原件实际非零；18,986个未写arrival词单列，未清零或混作已知值。
- 四个guardian按GUID绑定真实timer owner、静态ability/header和物理范围，共6,305个owner快照、25,220个payload比较；5种已有损坏拒绝检查通过。所有packet/notification完整metadata、payload/backing关系、内存范围与增量队列前缀逐阶段检查。包队列峰值1649，其它未恢复的wire语义不扩张。

## 本次新增的组合核验

**所有150完整payload及指定actor169。** 每阶段比较原件队列中全部opcode150，不能按模型声明的消息子集过滤。opcode169按模型明确声明的GUID集合绑定完整payload和顺序，另外保留所有9006/9007/9008资源创建包的严格子域；未声明的其它169及其它opcode不冒称恢复语义。初始提示中实际包含 `The Defias Uprising — survive the onslaught!`，不再把副标题当空串。

**真实逐级成长提示。** 从原件静态字典取得英文模板；独立使用实际前后23词派生属性的damage/maximumHP/regen差值、按顺序binary32计算与Decimal ties-to-even格式化，重建5条实际growth150及完整长度/终止字节。在collect导致逐级增长时，其完整新增150与预测一致。这里继承[93例/110次成长UI组件独审](2026-11-02-level-banner0135-independent-review.md)的明确范围，未重新执行该组件，未宣称本连续650覆盖中文、全部格式化边界或所有UI。

**60秒同帧wave与supply。** 零基frame600、stage8416、now60.09965秒附近，真实947先生成8个swarm NPC，再发wave150，最后产生kind2补给，新增opcode顺序严格为`169×8 →150 →169`。独立审阅辅助算法从固定原件静态敌人数据、实际world查询、输入RNG及当前位置复算wave选择、8个位置、创建payload与19次RNG；其中选择有1次拒绝抽样。其后独立继续补给2次位置抽样及1次yaw抽样，最终RNG为`[1324166826,1156906973,3709864032,744815207]`，counter226→235、units16→24。

wave内部RNG是审阅算法重建的中间值`[861164204,3615226568,1841833356,3262009105]`，原件本次只在完整947后提供一次组合快照，不能把它说成额外观察到的原件内部阶段。8个创建包和wave150还与[25例wave组件已独审](2026-11-02-event-wave0135-independent-review.md)的固定case24逐字节互核；该组件当时隔离了G2448，本650则验证其后真实补给连接。其它三种wave的生成组件验证不能当作已接入三种AI的连续验收。

**kind2 +12精确地址来源。** 本次新补给GUID `17370383913846833387`的+12不是奖励数值，而是原947计数循环的残留地址。独立审阅器没有导入生产binder：在claims→spawn的首次出生，读取前一原件vector owner和count3，核算owner`21189360`+176=`21189536`；模型只持有GUID绑定的符号表达式和4个None字节，未收到原件pointer。之后689个阶段都核同一实际4B值，并严格检查semantic None、physical四None与GUID/producer/offset对应。

11种纯审阅器损坏检查全部拒绝，包括错误实际词、GUID、producer、offset/addend、阶段、空owner、同时G2444到期、缺少声明、部分None和绑定后漂移。这11项不是新原件case。mode0空owner、同时G2444/G2448生产路径仍拒绝；本case未消费该新kind2，不据此宣称消费者已经接通。[75例补给组件独审](2026-11-02-supply-kind2-0135-independent-review.md)为显式依赖，不加到本650的计数。

## 进程与证据

原件Node80706实际63.7048秒，exit0、180秒期限内完成；父验证总耗时199.6906秒包含模型生产和重比，不能拿总时长当Node超时。审阅owned进程99094实际167.3759秒、exit0，360秒外层期限内完成；两组PID/PGID均实际检查为missing，stderr均空。审阅内部执行预算300秒，原件的8GiB逻辑/2MiB单record/512MiB blob/256MiB gzip等数据预算未缩减。

最终[只读审阅收据](../evidence/opening650-independent-review-owned-20261101T201707.724375Z/review/review.json) SHA256 **`2800b894f8ebdb7decf5c9cc1443996d8d8d5594c843ff1d949ce5a04c7feeea`**，机器可读摘录见[JSON](2026-11-02-opening-combat0135-650frame-independent-review.json)。既有60秒/120秒超时、90秒完整采集但旧模型缺growth150而有8581差异的批次继续保留，不与本次通过合计，也不回写成成功。

## 仍未证明

模型使用独立预解析world；本审阅未重新跑451资源解析。原件从合法1089前后环境snapshot恢复，locale是已初始化原件English状态，clock由外部f32调度，调用14个尾入口及选择入口；full880、前段/party/transport、全App资源所有权、Windows原生执行和完整独立一局均未验收。非空effects120/delayed56/hits/active84/timed12/deadline32/secondary112/XP与currency队列在此轨迹仍为空，不扩张到其活跃消费者。

最新137的组件与新版迁移继续单独记账，本135通过不转计137。完整资源入口、移动交互、近身资源消费、其它wave AI、Boss、死亡结算、存档、UI/渲染/音频及联机等缺口继续按总目标推进。
