# 真实开局到第四次选卡与Battle Shout继续战斗

固定 **0.135.1 / `90898d5e3`**，WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。human warrior、seed0、对象42、Elwynn、静止玩家、navigation false；维持“优先升级已有技能，否则第0张”策略。

最终新批 **400帧、4次选择、5604阶段、5606完整原件入口，声明比较0差异**。持续保留真实开局、普通刷怪/AI/死亡/拾取、20秒四守卫及其独立timer owner；第379帧实际第四卡为Battle Shout，随后完成其倒计时、6673施放、effect8/live32/23属性变化及继续战斗。最终等级5、XP6、金币53，模拟clock为f32 `39.999961853027344`。

[原件组合收据](../evidence/opening-combat0135-oracle-20261101T173256.931310Z/comparison.json) SHA `b5d9c546789401d738b43cc58cac1d7aeb117c94753ed4d63f60d923224520a7`。98源（85生产文件）执行前后相同；独立预期先生成，原件仅接收输入/动作，不接收预期。旧120、250及首个旧decoder400批均保留，不合计为新增帧数或成功case。

[400帧独立复核通过](2026-11-02-opening-combat0135-400frame-independent-review.md)，最终review SHA `376b09cd9ce10da25396d815824432e48eb456dbb1aeaea9674db95d25aa6482`。完整6008逻辑行、CAS与全部引用、24,443,084已知叶、严格未知mask、guardian归属、Dijkstra及Battle第6次tick的施放/owner0/CD均核；消息队列实际905包仍只保留观察。审阅器使用逐记录SHA已完整等价验证的私有快速传输副本，正式98源未改，原件/生产模型/checker均未由审阅器执行，不增加原件case。

## 运行与比较范围

`headless135`新增learned Battle Shout dispatcher，不把技能加进racial清单；1076仍拥有learned80倒计时和CD，selfbuff组件拥有effect8与1512数值更新。此前已恢复的顺劈斩、雷霆一击、racial、同一HP/RNG/计数/序号与guardian owner持续共享。guardian交战或动作生产仍是明确边界，当前走的是其真实待机路径。

[Battle组件](2026-11-02-battle-shout0135.md)134组/171次完整922、1076、2088调用与[只读独审](2026-11-02-battle-shout0135-independent-review.md)分别记录；真实第4卡的direct922输入与隔离1076计时夹具不混用。0.5秒remaining按f32逐次减0.1，实际第6次tick才施放。1202/aura/消息编码和外部proc仍未因此完成。

组合比较继承25秒批的状态、NPC/七vector已知字节、能力/候选/23属性/7numeric keyed字段、HP/XP/金币/RNG/时钟、距离场及完整guardian timer payload。未初始化allocator字节保持None，消费到未知则停止；计数投影向量在本域强制空。原件全部rawG/App、packets、物理backing及owner捕获仍保留，但未独立预测的runtime wire语义不计作已恢复。

原件继续依赖声明的历史完整线性memory snapshot、真实已初始化world/locale与外部f32调度；没有恢复externref虚拟机，也没有调用完整880。独立侧不读原件memory，组合使用先前独立资产producer的规范world查询输入。

## CAS取证与修复后重验

[CAS协议](2026-11-02-opening-combat0135-cas-protocol.md)对完整逻辑capture做内容寻址去重，而非删字段/阶段。6008条logical JSONL共 **1662490742B**；16316个唯一blob共 **83331346B**，gzip envelope stream **496272B**。逐logical record与滚动SHA、全部blob内容/父子边/出现次数均校验，完整原始record可重建。

原件限WASM256MiB、Node heap512MiB、878 imports全deny/实际0host、60秒owned子进程。CAS限逻辑8GiB、单logical record2MiB、unique blob512MiB/65536文件/单16MiB、gzip index256MiB。PID/PGID72778退出0且missing；`process-terminal.json`中`deadline_exceeded=false`。比较收据的161.865秒包含Node结束后的父进程档案/预期复核，不能把它当成Node违反60秒；本批未记录精确Node独占耗时。

[codec独审](2026-11-02-opening-combat0135-cas-codec-review.md)最初找出5个真实漏拒绝：目录或metadata symlink、bool-id与未独立核envelope原始字节。修复后的decoder SHA `16ca91ea52fdb107988d2f9c0c7b8d3b069d21df13f5a1b6091dd8ddb1199049`重新通过两组无损正例及26/26负例拒绝；最终独审收据SHA `5e27cf0fd619a8a5c315ac00bb4e8d803ba17c89ca8e5ba9af19c42a7b543839`。首400批`171633.375141Z`保持历史，不当最终依据；本报告使用修复后新原件运行`173256.931310Z`。

旧headless的[当前源码回归](../evidence/full0135-oracle-20261101T180102.862909Z/headless135-comparison.json)另有8seed／1614帧／22607阶段／11select，0差异；它保留自己的历史夹具与截短build alias，计数不加进本400帧验收。

## 原始资源独立入口

[raw400模型收据](../evidence/asset-combat400-owned-20261101T174254.757426Z/model400/receipt.json) SHA `9015386c3de810f2493622fe619b22b425162c4e1d710ce0f6930a58d4f80c94`：实际451资源/67281330B、92源和资产前后同；从原始文件构造world，再完成400帧/4选择，未读取原件memory、WASM或预解析world。四guardian GUID、None指针及timer归属核对通过，三个world产物SHA与之前独立构造一致。owned94234退出0/missing，209.573秒/300秒限。

[终态衔接核对](../evidence/asset-combat400-owned-20261101T174254.757426Z/projection-bridge.json)35项共同字段/backing/owner/source检查一致。这些是独立生产能力与已有原件差分的衔接证据，不新增原件case或完整880帧。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reverse-engineering/scripts/check_opening_combat135.py --phase full --frames 400 --capture-format cas
```

## 下一真实边界

纯模型尝试继续1000帧，在完成400帧后下一帧返回`pending_due_event`：G2444初始40秒的资源生成到期，不能继续拿“其它事件未到期”的普通947假设。该资源组件[另完成64组1417/947差分](2026-11-02-resource-spawn0135.md)，尚未接入本400帧组合；资源拾取效果、60秒其它事件、guardian交战/技能/死亡、Boss、终态/保存、UI/渲染/音频与联机继续待恢复。

最新0.137的432B伤害投影及原生声明静态互证继续使用独立身份和收据；本135结果不转记新版。本批完整880、Windows原生执行及独立完整游戏局数仍为0，最终目标未完成。
