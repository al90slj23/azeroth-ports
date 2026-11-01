# 固定0.135.1：近身资源消费、属性、光环和消息

已形成[resource_consumer135.py](../reconstruction/core_spec/resource_consumer135.py)与[resource_aura135.py](../reconstruction/core_spec/resource_aura135.py)两个独立纯模块。最终 **130例／244阶段，完整原10298直接调用163次＋完整原2862直接调用81次，0差异**。本批同时验证资源数值、持续时间、完整live32/pickup56/aura48×16、全部pending字段map、170/306/226/150消息与英文通知JSON，31份源及84条本地import边均冻结。[只读独立审阅通过](2026-11-02-resource-consumer0135-independent-review.md)；尚未声称主循环组合或完整游戏通过。

实际固定原件是0.135.1／9字节build `90898d5e3`（历史8字节alias `0898d5e3`），WASM SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。135的真实链为 **2862→31732→10298→1512/1202，或27960/10847**；137的31727/10291/1514/1151不能直接套编号或转记动态成绩。辅助pool在135的G768，137的对应字段曾是G764，本次按135实址打包并重新验证。

## 可执行行为与接口

`consume_resource135(state, kind)`恢复单个已选择资源的效果。`collect_resources135(ResourceCollectionInput135)`额外恢复资源专属近身选择、逆序处理与稳定移除。两者返回更新state、packet元组、通知JSON字节、消费/光环字段写/治疗等事件描述；后者还返回完整pickup backing及移除GUID序列。

| kind | 名称／visual | 行为 |
| --- | --- | --- |
| 3 | Speed Rune／9006 | 删除旧23451 live，append kind0／spell23451，expires=`f32(now+10)`；真实1512使有效speed multiplier增加0.6，保留原上限2.2 |
| 4 | Berserker Rune／9007 | 删除旧23505 live，append kind0／spell23505，expires=`f32(now+15)`；真实1512使damage multiplier增加0.5 |
| 5 | Restoration Rune／9008 | 请求`f32(maxHP*.5)`；G387>4时再乘.5；真实10847夹取HP并更新字段，spell23493 |

3/4的刷新按spell删除所有owner的匹配行，不能只删player GUID0。完整32B稳定移动并保留inactive尾部；append只写`+0/4/8/20/24/28`，`+12/16`保持原槽内容或新分配的精确None。容量扩展与原件一致。实际1512/1202以及本地化、serializer均完整执行，没有跳过。

2862在入口保存玩家XY，以原f32 `sqrt(dx²+dy²)<=3`判断接触；Z和amount不影响该资源消费分派。选择结果倒序执行，31732稳定移动完整56B、减count、保留尾部，先发170再应用效果。所有padding和未读字节按各自known/None来源保留；far kind2的未知`+12`四字节也完整保留。当前这个collection接口拒绝XP/coin、nearby其它kind、非空claim及removed aux owner，不能拿它直接替代通用混合拾取循环。未来主循环可在统一2862选择/移除顺序内调用单个`consume_resource135`，与已有其它消费者组合。

state必须提供显式StatsInput、23个derived words、pending字段map、完整live owner、G387、RNG、counter、message/action sequence、player GUID、aura owner、外部aura源不存在的证明条件，以及`notification_next_id14340336`和`locale_code='en'`。通知计数属于跨生产者共享的独立owner，原静态初值是 **1**；不得每消费一次就重新置1。0及FFFFFFFF回绕也有受控原件验证。模型没有读原memory、malloc指针、文件或网络。

## 光环缓存与字段写

新aura helper恢复真实1202的受控live-only域：kind0、唯一且有限非负的kind8（含真实Battle6673）及显式空的其它aura生产源。普通重复kind0在dominance前置检查中保留first expiry；774绕过去重，才按spell合并count并取max expiry。duplicate涉及kind8、负kind8、kind7/其它live、owned/default-kind12、definition38、shield等外部生产域仍pending。

输出为完整48×16 cache。前32槽是按live顺序聚合的正buff，后16槽在本域为空；active四个word为`1/spell/expiry/count`，inactive仅tag word0已知，其余12字节为新分配存储的None。不能为了比较而填零。

对应pending字段map写为：47..94的spell，95..100每8槽按nibble9（正）/8（负）打包，以及113..124每4槽按`min(count,255)-1`字节打包。1202不写101..112。首次或旧initialized2569 bit0为0时写全部66字段；已有48-cache且bit0为1时只写发生变化的值，expiry-only变化不重写spell字段。cache与pending字段map分开，前一次字段队列已排空时可合法只保留cache。

3/4均执行recalculate及aura，5保留既有aura。全量比较返回字段，而非只核HP/speed三个key。独立aura的前置静态/纯模型规格保留在[静态报告](2026-11-02-resource-aura0135-static.md)；那里0原件的历史分类不变，当前动态依据是本批完整10298/2862的新差分。

## 全部包与英文通知

本受控域原件产生的包全部进入独立比较，没有删掉150以过绿：

| opcode | 独立payload规则 |
| --- | --- |
| 170 | removed GUID的u64le |
| 306 | caster packedGUID两次，spell u32，flags256，hitcount1，target GUID u64，miss0，targetflags0 |
| 226 | packed playerGUID＋旧action1644 u32＋新speed f32 bits；仅速度变化时发送并增加action sequence |
| 150 | type6、u32 FFFFFFFF、playerGUID u64、UTF8长度＋1、`AZSBANNER`及制表符/字段文本、两个NUL |

42920从原14340336取当前u32作为消息id，再写id+1；10434生成有固定字段顺序的紧凑UTF8 JSON：`type,id,kind,text,name,boss`。15915生成`id=...;kind=rune;boss=0;name=...;text=...!`，22747加`AZSBANNER\t`前缀并封装150/type6。该路径是150提示，不能沿用早先137切片中的“JSON905”待恢复命名。本模块只支持原英文常量label，它们没有需要15915净化的tab/newline/分号/等号；其它语言明确pending，未做泛化假设。

例如Speed Rune的通知JSON为：

```json
{"type":"banner","id":1,"kind":"rune","text":"Speed Rune!","name":"Speed Rune","boss":false}
```

其完整150字节为：

```
06ffffffff2a0000000000000041000000415a5342414e4e45520969643d313b6b696e643d72756e653b626f73733d303b6e616d653d53706565642052756e653b746578743d53706565642052756e65210000
```

模型根据原静态label、显式notification owner和GUID计算全部字节，不读取原执行结果。默认计数1的原data bytes、三个label地址、格式描述与完整函数SHA均已记录在manifest。真实19964冷本地化初始化保持原路径，不注入locale/Once。

## 受控差分与终态

最终[comparison](../evidence/resource-consumer0135-oracle-20261101T203315.893397Z/comparison.json) SHA：
`970e32ef5af326ffd665b488a43f949eb8bd9e3192d6ffd7e2c121b78636c963`。

130例包括9职业×4个race的独立属性输入，全部3种消费，10/15秒刷新、所有旧owner移除、满槽/growth与重复消费，G387=0/4/5/255和HP上限，XY距离3的相邻f32边界、marker0/1、极大Z、混合资源逆序、far kind2 opaque amount、Battle到期/未到期、prior48-cache bit0、774聚合及GUID/通知id边界。

比较82,981个known值与101,062个精确未知物理byte cells。实际新产生192次消费效果及192条JSON，独立packet数量为306×192、226×42、150×192、170×29。按每阶段保留累计队列比较时，计840个包／39,758字节和346条JSON观察；累计旧包不当作额外生成，也不把旧批次数相加。

known面包括全live32/pickup56/aura48×16 backing、全部pending字段map、23个derived words、HP、辅助pools、speed、RNG/counters、action/message sequence、notification计数以及完整packet/notification字节。完整8192B Game、真实queue headers、pointer/cap及locale缓存另有raw观察；本批不预测所有分配地址、BTree物理形状或全部Game写集，也不声称手工fixture就是合法完整构造器。

原件仅改export section7，出口为10298/2862及原stack global0宿主只读观察；原body/data/其它section全部相同。878个host import deny，实际0调用。预算WASM32MiB、Node512MiB、单alloc4MiB、input/expected各4MiB、输出16MiB、owned60秒；实际peak20,578,304B、输出5,433,601B，578次含malloc的stack检查全部恢复。PID/PGID30502，exit0，二者missing，耗时3.958秒。没有EXE、Appstart、用户存档、网络、历史原件memory输入或新650采集。

复现入口：[check_resource_consumer135.py](../scripts/check_resource_consumer135.py)，`python3 reverse-engineering/scripts/check_resource_consumer135.py --phase full`。新[builder](../scripts/build_resource_consumer135_oracle.py)与[runner](../scripts/run_resource_consumer135_oracle.mjs)独占，不改shared host或已有104份源。31份Python/JS闭包与84条import边、input/expected/labels/module/WAT均在Popen之前冻结并终态读回。RO SQLite仅seek12个函数范围，共279,236B，不全文读取1.3GB WAT。复用名为source_closure137的工具仅做通用AST闭包检查，不执行或转记137原件。精确SHA与字段见[机器报告](2026-11-02-resource-consumer0135.json)。

旧6例pilot、首130例错误0.135.0摘要、随后正确version但只比较170/306的130例均保留，未覆盖。它们不作为最终完整wire结果，不累加。当前最终130重新加入显式notification owner、完整226/150及JSON后fresh通过。

marker2不是本域的成功变体。31732的compaction/减count及异常路径有静态指令依据；[同版历史1417失败收据](../evidence/full0135-oracle-20261101T190005.927219Z/supply-kind2-comparison.json)只证明原件调用失败，其旧finally的Stack not restored断言遮住了原trap，不能据此声称已动态定位具体异常路径、0host或0diff。本批130没有新marker2原件执行，纯模型拒绝不增加原件case；也不借137失败转记135验证。

仍待验收：mixed XP/coin/kind2的通用消费交织、claim/非空aux释放、其它/负/duplicate-kind8 aura及item/talent/timed来源、其它语言、全部allocator/queue/BTree物理身份、主循环组合与独立完整游戏/Windows原生执行。

独审收据SHA `e4fea3e425135d6db469e5261749ff843f1e86b3a19fe2a82a250e909a7a8036`：31源／24production、84依赖边、全部244阶段、23派生词、48×16 aura、66逻辑字段写规则、完整170/306/226/150及JSON由独立复核器重建；未执行模型或原件。192实际效果与346累计通知观察分别记账。审阅进程39480 exit0／双missing／0.808秒。
