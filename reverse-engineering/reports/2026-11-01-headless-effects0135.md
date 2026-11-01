# 0.135.1 独立闭环加入真实915阶段

[最终原件收据](../evidence/full0135-oracle-20261101T072329.149731Z/headless135-comparison.json)：**8个固定种子、1614帧、11309阶段、11次选择、11317次入口调用，0差异**。独立预期在原件启动前生成并冻结，65份源码含58个core模块及包入口，前后无漂移。固定原件为0.135.1 /0898d5e3，WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。

现在同一真实1560构造状态依次运行 `2088 →1754 →3757 →915 →921 →2862 →947`，选卡调用1072。915阶段调用[独立时钟/延迟队列模型](../reconstruction/core_spec/effect_system135.py)，范围、伤害/死亡、拾取、成长和选卡共享既有HP/RNG/counter。原件只加export，真实内部callee全部保留，878宿主导入拒绝且实际0次；不调用应用start、原生EXE、网络或存档。

本批是后继阶段；[先前064308](2026-11-01-headless-area0135.md)仍保留，不相加为新的1614帧覆盖。先前[915插入观测](2026-11-01-effect-system0135-probe.md)也单列，它复用旧预期，不能冒称当时已有新915模型。

## 实际新验收域

真实构造器及本批915输入始终为clock2364=0、delayed56/effect120两Vec cap0/len0；action sequence1644=1、effect counter2356=0。此批没有向原件写这些状态。模型独立从1560的明确store恢复初值，并逐阶段比较时钟、序号、两向量capacity/完整active records、416动作tag与玩家XYZ。

1560的scratch+1728写i64(1<<32)，经scratch+88复制后给出G1644=1；2356/2364的0来自明确的scratch store。416仅有inactive tag0，420..436的未建模payload、物理Vec指针和facing另存unmodeled-effect-fields，不假定它们为零或纯显示。适配器仅在队列空且tag0的未读路径使用payload代表值，不写原件，也不把这些代表值复制回独立状态；没有新增mask。完整original raw观测在probe中保存。

非空56的35/36/37等消费者有[500组/2121阶段独立组件对照](2026-11-01-effect-system0135.md)，含383正常case与117预期255 trap，并通过[组件独审](2026-11-01-effect-system0135-independent-review.md)；该组件的非空行为尚未接入本headless域。当前adapter遇到非空56/120或active player action明确停止。不能把500受控组件或八种子空路径外推为全部915已恢复。

8seed/策略及停点保留：0/2/4/5/7仍在第一次选到未支持能力后停止，3在257帧第二次选到cone_of_cold后停止；1/6各400帧，两次选择后继续，下一纯模型步是pending_due_event（没有第401帧原件）。仍优先第一张upgrade、否则第一张，不换卡、不删种子。

## 独立运行与未知

[复制运行](../evidence/headless-effects135-standalone-20261101T072549.178656Z/receipt.json)仅含59份生产源码，无原件/WAT/SQLite/资源/Node/WABT，全部core导入实际位于复制包：默认停0帧真实进场边界，seed1/6各400帧，seed3到257帧。它是模型自运行，不新增原件差分。[41角色保守性证明](../evidence/builder135-role41-review-20261101T072424.422022Z/review.json)重建旧8-role模块字节不变，仅静态构建。

完整880仍缺916、975、38007、2602、2573、49037等真实入口组合，还包括2376特殊事件及前段/party/终态门控，这不是穷尽列表，见[NPC与主调度清单](2026-11-01-npc-effect-producer0135-static.md)。915的120B效果/普通910、ranged/Boss/宠物、非空proc、真实进场/地形/资源、全部对象键与消息、终局、存档、UI、联网和独立完整一局仍未恢复。显式phase1及128×424B/128×88B初始zero槽仍是研究输入；现有安装包和存档不变。

[独立复核](2026-11-01-headless-effects0135-independent-review.md)已通过，最终review SHA `466b8875ee910f9cbf7ae067a5be0042888dd8eadab58dc5beef866edab0a8f8`。逐阶段重建并核对613762048B单位与127384576B范围backing，旧八种子/动作/legacy预期不变。7组payload poison和3项active-source guard核对代表值边界；90472个未建模u32只作sidecar观察。未重跑原件或改作者生产模型。精确SHA、逐seed信息和边界见[JSON](2026-11-01-headless-effects0135.json)。
