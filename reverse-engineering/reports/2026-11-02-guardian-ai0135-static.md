# 固定0.135.1：guardian AI静态接续记录

固定build `90898d5e3`（历史别名`0898d5e3`）；原WASM SHA256：`c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。

本批 **0 dynamic / 0 diff**。只读SQLite索引并定点读取16个函数，共1,878,986B WAT片段；不运行原件、不读memory/snapshot、不全读1.3GB WAT。静态binary/data段SHA已校验；完整WAT SHA沿用索引meta，本批未重算。以下是待实现、待差分的规格候选，不能作为完整guardian AI验收。完整函数身份与字段见[JSON](2026-11-02-guardian-ai0135-static.json)，本报告不复制函数正文。

## 关键链与owner字段

`921 → HP阈值 → 按index扫描timer → 全NPC规划结束 → 稳定44B临时队列 → 910`。主尾段先915、后921、再2376；guardian出生后下一frame才进入AI，921新造的120/56由后续frame的915消费。915先处理到期delayed56，再处理120几何/type；普通type正伤害按记录顺序f32累加，最后以最后命中的GUID/spell调用一次1073。

| 字段 | 契约 |
|---|---|
| U64/U68/U72 | 3个f32技能timer的capacity/未知物理pointer/count；由独立语义owner持有payload，不能清空或改U64=MAX |
| U76/U80、U84/U88 | 默认/当前44B技能声明pointer/count，leash reset恢复默认 |
| U92、G1920/G1924 | special40 home索引和向量，home XYZ在记录+16/+20/+24 |
| U96+16/+20、U104 | 52B HP阈值声明pointer/count；one-shot位图 |
| U100、U108 | exclusive技能busy-until；aggro byte |
| U288/U292、U352 | current/max HP；共通近战timer先减dt |

U108=0时，受伤可接战；满血则要求距home<=3且玩家距单位<=20。未接战会idle/返窝，**三个技能timer不减**。已接战且玩家距home>97.5则清U104/U108、回满HP、恢复默认能力、timer重置为CD×0.5并返窝。U352仍按共通顺序先减dt，不能把idle理解成整条记录不变。

## 三套技能与额外静态依赖

下列初始timer/源CD均按技能列表顺序；timer累计的是活跃技能时间，不是出生后的绝对墙钟。

| index / entry / name | 三项raw tag与参数摘要 | 初始timer / CD |
|---|---|---|
| 9 /609 /Kobold Taskmaster | raw7 Charge100；raw10 spell133三圆/radius3.5/spread7/delay1.6/×1.2；raw5增援4 | 4.5/9；5/10；7.5/15 |
| 10 /610 /Gruff Swiftbite | raw18双Charge间隔1.6；raw8 spell15284锥体/radius7/90°/delay1/×1.4；raw5增援3 | 5.5/11；3.5/7；8/16 |
| 11 /611 /Bellygrub | raw19 spell20549圆/radius7/delay1.3/×1.3/额外参数12；raw11 spell6524圆/type2/duration6；raw7 Charge100 | 4.5/9；6/12；4.5/9 |

九条timer并非全部依赖：610 raw18指向`5426156/5426196`两条40B raw7，首项立即递归910、次项在now+1.6经56B队列再次910。611 header的`+16/+20=5477880/1`是一条52B HP阈值：HP/max(maxHP,1)严格<0.5、U104 bit0未置时，先排同一双Charge并产生文本`%s squeals and charges!`。独立实现必须携带这些本地声明，不能沿原WASM地址读取。

活跃timer到期后，reset为源CD×(HP严格<30%?0.7:1)，不携带负overshoot。U100与`0xa0180006`仲裁位图控制排队；本组只有raw5/norm2允许并行，其余技能若同NPC已有exclusive项则等待且不reset。故611初始同为4.5秒的raw19先于raw7，不能同帧一起施放；HP阈值也先于timer参与仲裁。

## 910生产与下一域

- raw7：4865预测→46304碰撞→57528高度→21024锁定→61441通知→34693矩形120→63687 delayed35。需要真实world，不能直接复用flat raw9验收。
- raw8：4865→21024→61441→34693锥体→66966输出。raw10直接生成三圆，并消耗canonical RNG采样扩散点。
- raw18：递归910与56B delayed。raw19的record100=12还进入玩家动作，raw11带type2/周期payload，raw5实际调用5736生成NPC；这些不能只用HP数字代替。
- descriptor spell与120+84不同：raw7/raw8的120伤害spell为0；raw10/raw11/raw19分别写133/6524/20549。1073的完整registry/history/aura/反击/死亡尾部仍待恢复。

静态追踪时的headless依次会遇到`ai135._validate`拒绝U64 family、`cleanup_ordinary_corpses`连存活guardian也拒绝，以及`_effects_phase`拒绝非空56/120。这些guard不能删除后直接套ordinary追玩家。

最小下一切片：显式检查`U108=0、HP==maxHP、unit-home<=2、player-unit>20、canonical其他状态`，支持实际stationary idle，更新共通U352并保留三个技能timer、None指针及完整backing；live cleanup接受这一精确存活域，guardian死亡仍停。随后分别恢复engage/leash、HP阈值与timer队列，再逐组完成910/915生产与消费。**idle支持不等于完整AI**，这些域均尚未由本批动态验证。

## 16个函数身份

下表body SHA只显示前12位；JSON保留完整body/WAT SHA与索引范围。

| index | 静态角色 | body SHA前缀 |
|---|---|---|
| 910 | NPC action dispatch / busy / effects production | `2763f92fecd4` |
| 914 | outgoing NPC damage and protection gates | `13da39eca945` |
| 915 | delayed56 and effect120 consumers / accumulated incoming | `7eec05b5e91c` |
| 921 | guardian home / aggro / leash / HP threshold / cooldown scheduler | `5c2c1cdc75e8` |
| 1073 | incoming damage prefix and later callback boundary | `ae8055c998f7` |
| 4865 | predicted player target over explicit world | `f1b6fd384121` |
| 5736 | ordinary NPC creation for raw5 reinforcements | `59e98d191a6d` |
| 21024 | caster movement stop and lock | `b744dc54456d` |
| 31733 | descriptor busy duration | `e280d7d04f9c` |
| 32653 | spread-radius RNG helper | `3bc2af5d41a7` |
| 32969 | default guardian declaration header lookup | `4d0e83992e77` |
| 34693 | effect120 allocation and record production | `10cdfbc68a51` |
| 46304 | collision-limited target segment | `281d6b748bff` |
| 57528 | target point world height | `61ae650d69b7` |
| 63687 | delayed56 producer | `f0091ed4244a` |
| 66966 | spell target or animation output | `90f750090d25` |

## 本机证据与接续限制

本机证据目录：`reverse-engineering/evidence/guardian-ai0135-static-20261101T155959.325284Z/`。该目录保留bounded WAT；本报告只引用，不复制。

- `analysis.md` SHA256：`7e80c089776121d5228cba8765d34614135d07ece425428e3e49916d425560b4`。
- `guardian-declarations.json` SHA256：`8f18406bb11fb21e5b02236b790bffbd5eaa67aeaf9db03c946230dbcaa49b71`。
- `seek-manifest.json` SHA256：`32d0ea9cbe418c8e134e5e9920c3b7e1f566a1e2641e436d125f1c40365fdb66`。
- 只读索引：`reverse-engineering/evidence/wasm0135-profile-20261101T031028.877964Z/index.sqlite`。

本机证据路径及其SHA也保存在JSON；新checkout需先核固定原件身份，再使用只读索引定点读取。该批没有修改core、冻结脚本、生产声明或已有验收收据；guardian尸体timer释放、全部技能效果、完整1073和880仍未知/未验收，不能与既有120帧整合差分相加。
