# 固定135：开局、60秒事件与升级提示连续650帧

本批将已恢复的波次2424、补给2448和逐级成长提示接入同一份独立状态。固定 **0.135.1 / 90898d5e3**、human warrior、Elwynn、seed0、navigation False，真实开局后运行650个受控尾阶段帧并完成5次自然选卡，9105阶段／9107次原件入口，声明范围0差异。[只读独审通过](2026-11-02-opening-combat0135-650frame-independent-review.md)。旧135、137结果均不转计最新138；本批不是完整880、Windows执行或独立完整一局。

[原件差分收据](../evidence/opening-combat0135-oracle-20261101T200425.298468Z/comparison.json) SHA256 `16a86a82820ee8f737b256a458b252546336b20b6cd887d3c45e755f9ba538b1`。实际原件WASM SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`；历史`0898d5e3`仍只是旧截短alias，不覆写旧证据。

## 规则与独立生产

- 每帧沿用同一份玩家、单位、拾取物、世界、RNG与counter。ordinary947之后依次处理2424波次、2444资源、2448补给，再继续special2376。Boss与未恢复的活跃分支仍有明确守卫。
- [波次组件](2026-11-02-event-wave0135.md)恢复swarm／stampede／wall／pack及排除上次样式的选择。初始last-style是构造器实际写入的255。默认轨迹60秒后的首次swarm实际产生8只怪，连同坐标、完整已知记录、RNG与消息继续进入后续帧；未在本轨迹触发的stampede冲锋AI不算通过。
- [补给组件](2026-11-02-supply-kind2-0135.md)恢复本地模式70秒后续deadline、外层数量上限3、内层创建与最旧记录移除。kind2的+12来自计数循环残留地址，不能当成奖励数值。生产模型保留四个None字节及按GUID绑定的来源表达式，不读取原件malloc地址。
- 新只读验证器在第601帧、stage8416核对原件补给出生：旧pickup owner指针21189360，原数量3，地址增量176，实际+12值21189536。随后689次观察必须保持同一GUID的原始词；只允许这一已证明来源，未扩大通用None掩码。同步发生2444/2448、空owner模式0等域仍未覆盖。
- [成长提示组件](2026-11-02-level-banner0135.md)按每次升级前后真实属性计算damage／最大HP／regeneration增量，并按选定语言生成150字节。成长事件从4630经拾取、选卡收尾传入headless，不能硬编码每级固定文本。组件英文／简中各自验证；本组合使用明确英文输入。
- 主比较新增全部opcode150，并按独立模型生产的GUID核对actor169完整payload和队列顺序。其他未恢复wire仍只观察，不称全部协议已恢复。初始Defias副标题由已有开局规则显式提供，没有取原件输出来填expected。

## 新执行差分与独立复核

expected先于原件执行生成，104源／90production在冻结前后不变。原件侧保留合法历史snapshot，从完整6730／1089开局后调用14个完整组件入口；使用外部f32时钟推进，没有调用完整880。650帧约64.99958秒，最终level6／XP32／gold77，拥有cleave、thunder_clap、battle_shout。

严格比较47,780,952个已知叶；35,198,032个物理None字节、18,986个未写arrival词和689个来源绑定地址词分别统计，不能称这些字节全部独立恢复。CAS保留9759条完整逻辑记录、3,952,877,407B、28,155个唯一blob／215,567,259B，完整性核对所有blob与出现次数，没有删阶段或字段。

原件Node80706在63.705秒exit0，PID／PGID均missing，峰值166,395,904B／256MiB上限；878个host导入全部拒绝，实际没有宿主调用。180秒是有记录的执行预算，不是本次实际耗时；父流程含解码与比较199.691秒。

[独审收据](../evidence/opening650-independent-review-owned-20261101T201707.724375Z/review/review.json) SHA256 `2800b894f8ebdb7decf5c9cc1443996d8d8d5594c843ff1d949ce5a04c7feeea`：不执行生产模型或原件，重比全部9105阶段，独立核对5条growth提示、wave／supply同帧顺序、GUID与地址关系、拒绝样例。独审进程99094在167.376秒exit0，PID／PGID均missing。

[成长事件转发后的新回归](2026-11-02-growth-integration0135-regressions.json)分别保存level1151状态序列／3450调用、selection660／1090、death-pickup204／871阶段。旧selection主报告及其独审保持历史原貌，新批不覆写旧批，也不与连续650相加。

## 原始资产入口及终态衔接

[新raw资产运行](../evidence/asset-combat650-owned-20261101T201232.800315Z/model650/receipt.json)实际读取451文件／67,281,330B，独立构造world、开局并运行650帧／5select／9106摘要。97源及资产hash前后不变，不读取原件memory、WASM或预解析world；owned92341在289.810秒exit0，PID／PGID均missing。这是modelselfcheck，新增原件case为0。

[50项终态衔接](../evidence/asset-combat650-bridge-owned-20261101T202159.503837Z/projection-bridge.json)核对共享90production、3份world产物、7个物理owner的完整已知／None backing指纹、成长150、声明actor169、guardian与opaque来源等均通过。桥接明确只比较两个模型运行的终态，不新增原件执行，不称raw资产逐阶段原件差分。

## 失败与下一真实边界

- 旧60秒与120秒预算的新650采集超时原样保留：[191825](../evidence/opening-combat0135-oracle-20261101T191825.767720Z)、[195003](../evidence/opening-combat0135-oracle-20261101T195003.943753Z)。这些批没有完成比较，不计通过。
- [192229完整650采集](../evidence/opening-combat0135-oracle-20261101T192229.881707Z/comparison.json)确实执行完成，但旧模型缺成长150，出现8581差异。修复后重新执行本批，不把该失败倒改为通过。
- [旧raw650的300秒超时](../evidence/asset-combat650-owned-20261101T195035.127301Z/process-terminal.json)保留。改为串行、有限480秒预算后，新raw650实际289.810秒完成，未缩减资产或比较字段。
- [当前纯模型延伸](../evidence/opening-event135-model-boundary-20261101T201809.896133Z/receipt.json)到665帧／6select后因自然选中demo_shout停止；另两张真实候选为bloodrage、whirlwind。没有跳过该卡或重抽以延长轨迹。665是模型边界，原件差分仍只到650。

下一步恢复demo_shout与真实资源消费并接入当前状态，再继续实际流程。完整输入／App与880前段、Boss与全部AI、完整技能／来源／proc、其它地图、存档、渲染音频、UI和联机及最新138迁移仍未完成。现有安装包与存档未改动。
