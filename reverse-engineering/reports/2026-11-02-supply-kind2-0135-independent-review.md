# 固定135 G2448 kind2补给：75例独立只读复核

最终75例受控组件证据通过独立只读复核。复核者不是补给模块作者，只读取冻结输入、预期、原件输出、源码、WASM字节及RO索引；没有执行原件、生产模型或原checker，也没有新增原件用例。

- 原批：[supply-kind2-comparison.json](../evidence/full0135-oracle-20261101T192704.946829Z/supply-kind2-comparison.json)，SHA `716b3d327aa5fcc05ed85911b5da869fa6af3e2ee8c3e83056523f1c4d0f1c76`。
- 最终[审阅收据](../evidence/supply-kind2-135-independent-review-20261101T193915.933213Z/review.json)，SHA **`bb56ba2213d54912521deb390f131db1205bf9fc7ad82adb51802c6131827c98`**。
- [审阅脚本](../scripts/review_supply_kind2_135.py)，SHA `6028a522c34bd994e80ff9ef84d2dc538c8ba8e4ad934707a968ff2bc72b9bb3`；[机器报告](2026-11-02-supply-kind2-0135-independent-review.json)保存计数、产物SHA、历史失败及范围。
- 审阅进程PID/PGID46579，exit0，二者missing；1.390秒，60秒deadline。[终态](../evidence/supply-kind2-135-review-owned-20261101T193915.807175Z/process-terminal.json) SHA `2ee7f391a735843bea0efe4c9630e4c76f66861b43264cfaf61132100eb4bd1d`。

## 复核结果

| 项目 | 实际复核 |
| --- | ---: |
| fresh受控原件实例 | 75 |
| 完整直接调用 | 1417×15、947×60 |
| frozen与当时current源码 | 61份；51份production，247条本地依赖边 |
| 严格相等known值 | 143,945 |
| 有来源的None物理字节 | 86,120，其中34,173个原件字节非零 |
| 未允许写入的Game守卫字节 | 608,460 |
| 完整有序包 | 249包／38,376B；169×239、170×10 |
| 精确新GUID与pre-G2448 owner地址词绑定 | 40 |

61份源在审阅开始和结束均与冻结副本一致。之后root获准继续集成，报告不要求这些历史源永远等于后续current。补给core SHA为 `e765fd68b5615a76a084e6f02b7f94ddbbc48dc944e2a3d323c0fbcbb5f2ae13`。审阅递归验证全部61份闭包，扫描production不含文件/host/动态执行入口，并校验原输入、预期、标签、manifest、world四文件及输出SHA。

独立重建了每个pickup的完整56B backing、active count/capacity、稳定删除、inactive尾部及append写集，再要求该重建结果与冻结expected完全相同。None只来自明确旧物理字节、新分配未写区和新GUID的四字节地址词；没有扩大到整行、整个amount字段族或已有known字节。生成时`+4..7`保留，38个known padding字节通过严格比较。实际发生20次capacity growth和10次完整稳定删除。

1417的inner cap为mode0的5，947的outer cap为3；mode1保留`u32(G2140+1)`、减`G2548`的unsigned underflow guard、至少1人的夹取、逐步f32 factor与70/factor deadline。原85719的`+0x3effffff`及指数mask舍入已独立实现复核，没有换成ceil。到期写deadline先于cap判断；44次spawn、12次cap、4次future分支均核对。cap/future只停止补给子分支，前面的ordinary消费仍保留。

按timestamp total-f32-order选择最旧行，等值保留first；非单调`[7,3,9,3,1]`实际选择最后一行，`[5,5,7,8,9]`实际选择第一行。删除包170严格为被删GUID的完整8B little-endian，先于新169。59个补给169均解析完整字段集合、GUID、visual9005、display259、scale1、kind21=3、XYZ和共享RNG产生的yaw；180个ordinary169另核其原有请求/GUID/位置。所有249个包的原始payload逐字节与expected严格相等。quaternion12/13另外用独立sin/cos容差检查，未声称另写了bit-identical trig实现。

## 地址词与mode1前提

新amount不是常量2。对于pre-G2448 active count `n>0`，独立核对实际word为：

```
pre_owner_base + (n%4 ? 8+56*n : 176+224*(n//4)) modulo 2^32
```

40个word全部绑定到raw Game before中的G1872、对应新GUID及实际新行`+12`。模型仅返回owner/count/delta表达式与四个None，没有接收原件malloc地址。四个mixed-resource输入case16/31/46/61确有两个kind2和一个预先独立生成的kind3/4/5，active count3，实际`+12=preowner+176`；它们不是三个kind2，也不是cap。40秒资源准备只属于独立fixture输入，不增加原件G2444调用或自然40秒历程。

24个mode1案例均提供显式有限peer-position16B rows，绑定G2232/G2236；复核为96个原有NPC逐一证明至少一个peer距离不超过55，并逐字节确认四个原有NPC未重定位。4例触发unsigned underflow guard。旧缺peer批产生的5,127处差异仍保留，不能通过省略原NPC或跳过远NPC前置分支消除差异。当前正例只覆盖明确near-peer前提。

模式0空vector的earlier947 local2来源仍pending；模式1空vector已知amount为guarded remainder。marker2在原31732中先完整memory.copy、减count，之后进入panic；不是正常skip。模型拒绝该未恢复partial-trap域，不能把旧异常批的differences0或缺失runtime解释为通过或0host。

## 原件、输入与终态边界

固定原件SHA `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。从WASM active data及1465实际pointer/length guard重新核对build为9字节 **`90898d5e3`**；`0898d5e3`保留为历史8字节alias，未覆写旧manifest或收据。192619错误元数据批、旧69/71/75批和marker2异常均没有加入最终75计数。

私有模块仅增export section7的1417、947及原global0观察出口，所有其它section和所有原函数body/callee完全未改，没有隐式start。[静态证明](../evidence/supply-kind2-135-independent-review-20261101T193915.933213Z/static-proofs.json)重新以RO SQLite有界seek核12个函数窗口，并保存947 factor/count/iterator顺序、1417 oldest规则及31732 panic顺序；没有读取整1.3GB WAT。1560的scratch2536常量60写入也保存，输出Game基址为scratch+88的构造上下文来自既有静态恢复。

输入是独立451资产的预解析terrain/nav/secondary四文件，在fresh原件中手工打包已知Game8192、Rc124字段与完整物理backing；未消费元数据有显式fixture零输入。不是完整Game/Rc构造器证明，没有使用原件memory snapshot。本审阅重核文件和来源收据，未重跑资产parser或query模型。直接1417的XY夹取另行复算；最终Z、完整XYZ/输出包与冻结预期严格核对，terrain查询数值以已声明的query输入/expected为依赖。

原件PID/PGID17171，exit0，二者missing，1.837秒/60秒deadline；878个deny imports，实际0host，2,123条allocator/entry stack检查全部恢复1048576。WASM cap32MiB、实际peak20,578,304B，Node heap512MiB；完整输出3,052,607B，逐行2MiB、累计16MiB预算均满足。原件未调用Appstart、网络、EXE、用户存档或snapshot。审阅自身两次断言修正均保留失败终态，未执行原件/模型，不构成新增通过数。

尚未验收：mode0空vector、marker2完整partial-trap状态、非空aux释放、primary-present/nearest-miss fallback、mode1远NPC重定位、同次G2444/G2448均到期的owner交接、完整kind2消费/UI效果。组件尚不证明自然60秒、完整880、Windows/native或独立完整游戏；本复核新增这些层的数量均为0。
