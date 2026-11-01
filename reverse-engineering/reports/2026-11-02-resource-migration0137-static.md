# 固定0.137.0资源生产静态迁移

已找到固定 **0.137.0 / `d171b8f9f`** 的G2444资源链及Windows静态对应。结论属于**函数定位、指令形状与声明/局部字段互证**；本报告新增原件调用、137模型差分与完整880帧均为0，没有实现137资源模型或宣称动态迁移通过。0.135.1的64组资源差分不转记137；后续137实现与新差分另出收据。

[可复现trace](../scripts/trace_resource_migration137.py) SHA `09cb7d0208e156061fe101b41892ded1ac8926b3725a96c7d294754d6c373527`；[静态映射收据](../evidence/resource-migration0137-static-20261101T182241.791715Z/mapping.json) SHA `59b088cea0c3a7e1779cd3283c80ec864bcea603b20740dcade59bbbedff2e65`。原件身份：Web SHA `20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8`；Windows147,844,608B SHA `aa6b254f905e2f7a4cbc7c2c8f11af822ec362e3d2b8e84cabd8c38893a10dc8`。Windows未执行，WASM未实例化；macOS仅使用Python RO SQLite/二进制读取与LLVM objdump有界解码，没有Wine、Windows虚拟机或游戏启动。

## 对应入口与差异边界

| 0.135.1入口 | 0.137.0入口 | 实际静态比较范围 |
|---|---|---|
| 947 | 947 | G2444资源225行；不含947其它分支 |
| 1417 | 1420 | 完整函数2560行，明确记录call/data重定位 |
| 13516 | 13502 | 完整函数424行，明确记录call/data重定位 |
| 1821 | 1827 | 完整函数1913行，明确记录call/data重定位 |

947仍使用G2352时钟和G2444资源deadline。其资源段依次执行：`now >= deadline`；先写`now+45`；在实际pickup活动前缀中合计kind3/4/5，上限2，计数不读marker；xoshiro乘3拒绝`lowProduct & 0xc0000000 == 0xc0000000`；选中kind后把当时state[0]留作amount，再调用13502推进同一RNG取15..40半径位置，最后1420创建资源。这个225行窗口只需两处call索引重定位，没有其它指令差异。完整947在窗口之外已有432B Unit步长和其它地址变化，本报告没有将整个947判为同义。

最终trace额外保存了三条WAT `i64.const(display | scale_bits<<32)` 到相邻visual写入的实际指令窗口及绝对行号，避免只把参考表抄成结论。1420的三种资源仍为`(kind, visual, display) = (3,9006,5931), (4,9007,5995), (5,9008,5991)`，scale为binary32 `0x3f800000`。区域clamp仍为`max(radius-2,1)`，随后实际高度/nearest查询，再1827产生actor kind5、flags0及GUID/消息。13502完整函数与旧13516除了callee和数据地址重定位外形状一致；1827完整函数与旧1821只有callee索引变化。**137的数值1821已经是另一个三参数函数**，不能直接复用旧入口号。

22对直接callee的原始body SHA逐一保留，只有`38323→38342`、`49503→49511`、`85719→85702`三对raw body完全相同。其它callee body不同可能包括调用索引/数据地址重定位，其完整语义未据此自动验收；指令形状相同也不等于动态通过。

## Web字段与静态数据

G字段在本链保持：时钟2352、资源deadline2444、RNG1720/1724/1728/1732、pickup Vec cap1868/ptr1872/count1876、World指针2348、共享counter2408。Web pickup仍56B：marker0；kind8、amount12、GUID16；aux Vec24/28/32；visual36、XYZ40/44/48、time52。+4..7未写区不能当0。

Zone152B表从135的`5456016`迁移到137的`1665968`；centre位于+104/+108，radius+120，12行三字binary32与旧135逐位相同。1420通过World+8地形、+56 primary、+116 fallback工作；primary存在但nearest miss的分支仍有原kind参数相对+116的低地址读取，不能发明fallback。真实451查询world的无primary域与其它World域应分别构造合法输入。

## Windows同分支证据

三个`display+scale1`八字节literal各唯一出现，均在`.text`且属于同一`.pdata`范围 **`0x145ce99e0..0x145cea51d`，2,877B**。不是仅凭散落常量配对：kind参数由edx移到r15d，再通过jump table `0x1477f8568`（文件偏移125791592）按实际kind索引，得到下面三个分支；各分支将visual与display/scale写入同一个临时actor定义，再汇合调用`0x145cfc9e0`。callee本体未在此恢复。

| kind | visual | display | 分支VA | 文件偏移 | 同分支20B原始字节 |
|---|---|---|---|---|---|
| 3 | 9006 | 5931 | `0x145cea217` | 97424919 | `c785900000002e23000049bf2b1700000000803f` |
| 4 | 9007 | 5995 | `0x145cea243` | 97424963 | `c785900000002f23000049bf6b1700000000803f` |
| 5 | 9008 | 5991 | `0x145cea201` | 97424897 | `c785900000003023000049bf671700000000803f` |

[有界反汇编](../evidence/resource-migration0137-static-20261101T182241.791715Z/native-resource.objdump.txt)由固定`/usr/bin/objdump`读取该.pdata函数范围；工具SHA与输出SHA、PID/PGID及终态均在mapping收据。Windows zone stride240、centre+200/+204、radius+216也由本函数寻址确定，12行对应三字段与Web137逐位相同；不能因此认为完整zone结构在两个平台相同。

该Windows producer的数组寻址为`9*i*8`，记录实际步长 **72B**，不是Web56B。静态写集可定位aux Vec0/8/16、marker24、kind32、amount36、GUID40、visual48、XYZ52/56/60、time64；未写padding仍未知。该局部函数还读World指针3552、时间3720及pickup Vec1768/1776/1784。它们仅为**本生产者的局部静态字段证据**，不是完整Windows Game/Unit ABI或原生运行验收，禁止把Web偏移直接套给Windows。

## 复现、保存与未决

```sh
python3 reverse-engineering/scripts/trace_resource_migration137.py
```

脚本只按RO SQLite查询出的`wat_start/wat_end` seek目标函数；实际读取135 WAT 496,384B、137 WAT 496,512B，未全文读取约1.3GB WAT，未重新hash整份SQLite。所用profile manifest/identity、选中SQL结果、函数body/WAT SHA与只读index stat均落盘。静态初始memory使用隐式0加全部active data segments，仅用于已定义静态声明；没有给动态未知记录补0。

源码/原件/元数据前后保持原身份；owned trace PID/PGID 87707，exit0、均missing，4.467秒/60秒；objdump另有30秒限制与终态。全部输出位于4T研究区，没有修改135冻结生产源、入口文档、targets、安装包或存档。

未决项包括137资源模型及完整1420/947新原件差分、各变动callee完整迁移、资源拾取效果、其它due事件与完整947/880；Windows创建callee、完整物理ABI、浮点跨平台行为及原生动态运行仍未验证。

初次静态收据`181921.968921Z`原样保留；最终`182241.791715Z`补齐上述三条WAT声明窗口，均为静态读取，不能累计成原件case。
