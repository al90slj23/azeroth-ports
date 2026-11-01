# 固定0.135.1：资源消费所需的1202光环投影

新增独立纯函数 [resource_aura135.py](../reconstruction/core_spec/resource_aura135.py)，恢复声明域内的48×16B光环cache及逻辑字段更新。这里只做了静态恢复和7项纯模型控制检查／3项显式拒绝，**0次原件执行、0个原件差分case**；完整13510298/2862资源消费的后继原件差分另由主任务负责，不能把本报告当作其通过收据。

固定原WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`，实际9字节build `90898d5e3`，历史alias `0898d5e3`。135的光环重建入口是1202，不能使用1351151代替它。

## 接口和输入域

`ResourceAuraState135(storage, initialized2569)`保存显式empty或完整48行16B cache，字节可为None；`rebuild_resource_aura135(live_storage32, live_count, now_bits, previous, player_fields)`返回新的aura、完整逻辑字段tuple、events及按原顺序的field_writes。

events仅为`('aura_field_write',key,value)`逻辑写描述，不宣称原ECS消息或packet投递。物理BTree和malloc指针不进入纯模型。

调用者必须证明其它1202来源未激活。本切片支持未过期kind0，以及唯一spell、有限非负magnitude的kind8（包括正常Battle Shout正增益）；负/控制效果、kind7、外部definition38、active owned/shield kind12等其它生产者均未恢复。重复包含kind8的同spell dominance逻辑显式pending。

## 已核原规则

1202先比较`live.expiry24 > now`；NaN或过期行不再读其它字段。普通重复kind0同spell的有效比较值均为0，因此去重阶段稳定保留first，**其expiry也保留first，不能取later maximum**。774绕过此去重检查，随后合并计数并取最大expiry。kind0的原magnitude+12可能物理load，但在该比较路径被覆盖为0，模型不要求其未知字节被填值。

按原live顺序，前32个正增益聚合项进入slot0..31；声明域内的负/控制vector为空，slot32..47未激活。每次新cache都重新分配，inactive行只有tag+0的4字节为已知0，后12B保持None。active行完整四个u32为`(1,spell,expiry_bits,count)`。

旧cache不是完整48项时，原件另建空比较cache、清initialized2569，再强制写出所有本切片字段。旧cache48项且initialized bit0已置位时，只按所比较的值变化写逻辑字段；expiry-only刷新仍更新cache，但不凭空新增相同spell/flags/application字段写。

| 逻辑字段 | 规则 |
| --- | --- |
| 47..94 | 48个slot的spell或0 |
| 95..100 | 每字段8个nibble；present正slot为9，负slot为8，其它为0 |
| 113..124 | 每字段4个byte；present且count>0写`min(count,255)-1`，其它为0 |

1202不写101..112。最后新cache cap/count均48，initialized2569置1。

## 证据和边界

[trace_resource_aura135.py](../scripts/trace_resource_aura135.py)通过RO SQLite按函数seek读取1202/29629/30834/23583，共114,472B WAT，逐一核原body边界/SHA；没有全文读1.3GB WAT。

[静态收据](../evidence/resource-aura0135-static-20261101T202129.769026Z/resource-aura135-static.json) SHA `d0b94f68904d3c0be82436b4119a6a308e3a3b47a8685ea9213ba4b702d62e33`；[纯模型控制收据](../evidence/resource-aura0135-static-20261101T202129.769026Z/local-selfcheck.json) SHA `2a76fc098e395547d6734467e5c931f096e87598823a023f21a4f0a991d000ac`。控制项覆盖精确未知allocation字节、expiry equality、expiry-only更新、普通重复与774区别、正Battle+资源顺序和NaN expiry短路；拒绝重复kind8、负kind8和kind7。

模块SHA `4fc720ee1d13d931f2d9f94f271ea4c6bf44a11833cbe3701ddd5e3c86ec8536`，trace SHA `2ab4fdbe3c37783e8139795df91996d4a7770d08db2ec799aedf58942ffc2ac3`。AST、单EOF与尾空白检查通过，未修改既有生产源、原收据、安装包或存档。

仍待后继验收：完整原件差分、其它aura来源及dominance分支、物理BTree/分配身份，以及wire/UI消息。机器字段见[JSON](2026-11-02-resource-aura0135-static.json)。
