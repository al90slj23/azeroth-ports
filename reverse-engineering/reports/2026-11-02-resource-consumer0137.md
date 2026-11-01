# 最新137资源拾取：2862→31727→10291

固定 **0.137.0 / `d171b8f9f`**，Web/WASM SHA `20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8`。本批形成资源**近身判定→反序移除与销毁→三类效果**的独立可执行组合，使用完整原2862/10291对照，内部1514、1151、10841、19971→82064等callee全部原样执行。

[最终新差分收据](../evidence/resource-consumer0137-oracle-20261101T190800.110757Z/comparison.json) SHA `5797efa62a4852134823656d80c92644b865234f975ab135ab456e217ba065b8`：**156 fresh cases／250阶段（171次完整10291直接调用＋79次完整2862调用），0声明差异**。32源、23production、82本地Python/JS导入边在预期前闭合并冻结；输入、预期、源码和模块执行前后相同。27个近身资源的实体移除与效果状态获得组合验证；它们是case内部事件，不另增加27例或27个已instrument的外部10291调用。

## 独立规则与接口

[`resource_consumer137.py`](../reconstruction/core_spec/resource_consumer137.py)提供`consume_resource137`及`collect_resources137`。生产模型不读原件、memory、文件、存档、网络或原件结果。

| kind | spell | 实际效果 |
|---|---:|---|
| 3 | 23451 | 稳定清除所有相同spell的live32记录，append effect0，expiry=f32(now+10)；1514统计移动倍率增加0.6，再执行1151 |
| 4 | 23505 | 同样稳定清理/append，expiry=f32(now+15)；1514统计伤害倍率增加0.5，再执行1151 |
| 5 | 23493 | 10841请求f32(maxHP×0.5)治疗，G387>4再减半，HP上限为maxHP；本分支不调用1514/1151 |

同spell清理不限制owner或是否已过期，与racial只清owner0的规则不同。压缩保留顺序和整个32B记录，append只写owner0、kind0、spell、expiry和尾word0；**+12/+16未写，完整保留目标槽原有已知或None字节**。容量满时才按原增长策略扩展，inactive backing不清零。共享135独立数值原语在本137空外部来源域重新差分，不能据此声称完整1371514迁移。

2862在入口快照玩家XY，资源kind3..5使用逐步binary32平方/相加/sqrt后`distance<=3`，不使用Z或amount。先确定下标，再反序分派；31727稳定移动后续56B记录、减active count，capacity及尾槽旧字节保留，发opcode170完整little-endian GUID8字节，然后调用10291。amount是opaque u32，不能解释为经验或金币。当前支持live marker0/1，claim向量为空、auxiliary GUID向量为空；远处kind2可保留，XP/金币及其他近身kind仍明确pending。

1371514的辅助池物理字段为**G764**，共享独立StatsInput中的旧semantic名字`pool768_bits`在本适配器明确映射到764；没有套用旧版全部物理偏移。RNG、G2408和G2412保持不变，速度变化超过原阈值时才递增G1644。

## 验证范围与完整原callee

语料包括9职业×8种族的空外部来源统计、重复spell/不同owner/过期记录清理、槽复用和容量增长、治疗0/25/75/100%血量与G387=0/4/5/255、资源XY距离0/2.9999998/3/3.0000002/4/100、高度一百万、混合资源反序处理、远处kind2和二次空收集。

逐阶段比较 **33,127个已知值、13,650个显式未知physical byte**，包括完整32B/56B capacity与active/inactive backing、HP、23派生词、3个已知对象字段、4个辅助词、speed、共享RNG/计数/序号，以及所有170销毁消息的完整payload和顺序。None只允许出现在预先声明的physical backing单元，不掩盖标量或结构差异。

完整原函数通过只新增10291、2862和global0导出调用，code/data/callee未改，不启动App。878导入全部拒绝、实际0host，WASM32MiB/Node heap512MiB、owned60秒。PID/PGID75893退出0/missing，9.256秒，峰值20,578,304B，全部调用正常返回且stack恢复1048576。

没有注入Once/locale上下文：138个case由真实19971→82064把locale状态0初始化为3；18个全远处case没有资源效果，locale保持0。这证明原初始化在此宿主域正常执行，不等于14语言全部行为已验证。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reverse-engineering/scripts/check_resource_consumer137.py --phase full
```

## 保留的真实反例

首个174输入批在near marker2处原件trap；[目标单例](../evidence/resource-consumer0137-oracle-20261101T190504.861930Z/stderr.log)保留真实WASM栈：`2862→31727→80657→90663→49510 unreachable`，stack从1048576变1048336，进程退出1。此前将31727的marker2理解为“不发170就成功return”是错误的：该branch跳到bounds panic，源码路径在此之前已经移动记录并减少count。这一部分压缩顺序是静态依据；失败批未动态比较trap后完整Game，不扩大成partial字节已验证。

失败批的`differences:0`只是因原件退出1而没有执行比较，不能称通过；也没有最终runtime可证明实际host次数，故不标0host。旧174和单例、3/6 pilot及旧115/171直接效果批各保留原身份，不与最终156计数相加。独立模型现在明确拒绝marker2，并保留该反例，而不是把它转换成普通成功拾取。

## 明确未恢复的输出

Game8192、空来源向量、初始BTree和物理backing均为手工隔离输入，不是完整Game constructor。当前验收为mode0、effect0 live、空装备/天赋/timed来源；其他模式和非空来源不外推。

每阶段完整保存raw Game、全部keyed字段、48×16B aura backing、所有packet/notification payload及locale状态。原件实际生成了Speed/Berserker/Restoration Rune banner和相应cast消息，但这些完整UI/aura/wire/本地化语义尚未由独立模型预测；观察不能替代恢复。报告中的789 packet和318 notification是累计队列的阶段snapshot次数，不是新增消息数量或覆盖比例。

与[137资源producer1420](2026-11-02-resource-pickup0137.md)互补，本批尚未将1420与2862在同一个完整游戏循环原件中连接。完整880、原生Windows执行和独立完整局仍为0；最终目标未完成。限定范围独立只读审阅已通过，收据登记见下。

## 独立只读复核登记

已实读并核对[独审报告](2026-11-02-resource-consumer0137-independent-review.md)与[机器报告](2026-11-02-resource-consumer0137-independent-review.json)：[最终review收据](../evidence/resource-consumer137-independent-review-20261101T191616.444214Z/review.json) SHA **`ccffb6c554356e6cb6eeaa6b75ae3310812dfb819a2c9d9ec3629f8c8481b001`**。状态为`passed_scoped_read_only_review`。复核156例／250阶段，27次近身消费是case内事件；789包／318通知是累计队列观察，完整UI/aura/其它wire仍未独立预测。

本次登记不执行模型、原件或原checker，新增原件用例／完整880帧／native执行均为0；旧批计数、输入前提及pending范围保持，不将组件通过转成650或完整游戏通过。
