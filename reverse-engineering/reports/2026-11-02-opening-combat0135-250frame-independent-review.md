# Fixed135 250帧组合的只读独审

**通过已声明范围的独审。** 固定 `0.135.1 / 90898d5e3` 的既有单 case 为250受控帧、3次选卡、3503阶段、3505原件入口，原比较0差异；本次只读取这些证据和冻结源，没有执行原件、producer或checker，没有新增差分case。最终[独审收据](../evidence/opening-combat0135-independent-review-20261101T164522.842290Z/review.json) SHA256 `556693d5bac9b86545dd89a57b042bdb54823e49d4f845b5547a3a978d7158c7`；[结构化报告](2026-11-02-opening-combat0135-250frame-independent-review.json)。

94份当前/冻结源的SHA一致，84份生产文件的AST导入闭包准确且没有直接文件、进程或eval调用。私有WASM除export section外逐段与原件一致。3757条原件记录和3504条expected记录的顺序由输入actions重新生成，外部f32 clock独立重算；三个select分别选择首张`thunder_clap`、升级`thunder_clap`、升级`cleave`。最终level4、XP3、gold14。原件进程70978/PGID70978退出0，27.395秒，小于60秒，审阅时PID/PGID均不存在。

原件gzip为99,283,327B，解压785,896,500B，最大记录477,556B；expected gzip为11,123,945B，解压117,402,696B。两条流均核对完整单gzip member、CRC、记录边界和预算，原件压缩/原始双SHA与runtime相符。[协议拒绝自检](../evidence/opening-combat0135-independent-review-20261101T164522.842290Z/protocol-guard-checks.json) 另验证拼接member、截断footer、缺末尾换行、超原始预算和超单记录预算均被拒绝。

| 独立重比项目 | 数量 |
| --- | ---: |
| 严格记录字节 | 13,656,156 |
| projection叶值 | 434,000 |
| vector形状字段 | 70,080 |
| 阶段身份字段 | 7,006 |
| 合计，与原comparison一致 | 14,167,242 |

未知字节位置13,983,204，其中原件实际非零8,873,226；另有7197个未写pickup arrival word。所有active None均受恢复的写入范围约束，inactive backing保留真实容量。guardian新增记录的72..108字节不得扩大未知掩码；U68只允许四个物理pointer字节未知，共11,248个位置，且必须有完整owner payload。原件每份2592B Game、19类vector header/count/capacity/full backing及SHA、App/world持有关系、候选语义和队列payload/backing均核对。

四个guardian首次同时出现在frame199、action201、special阶段、stage2800。共703份capture、2812份guardian payload逐一核对：单位GUID与当前index、raw U64..U96 header、唯一timer allocation、3个timer完整backing、两份44B ability slice、28B header、special槽owner GUID、projection和expected全部绑定。跨GUID、遗漏owner、timer/backing不符、expected timer错位、对已写字段扩大None掩码五项篡改检查均被拒绝。它们随后处于本case实际idle域；这不验收非空guardian施法/排队命中路径。

静态声明来自**原WASM初始零内存加全部active data segments的顺序覆盖**，不依赖snapshot创建，也没有模型literal fallback。[24个静态读取区间证明](../evidence/opening-combat0135-independent-review-20261101T164522.842290Z/static-memory-proofs.json) SHA256 `7de582e380375be8cab0ea0e2bdbf49b3b87772fb9109b6f474de35195cb81b5` 保留原件文件范围、段overlap、稀疏初始零区间与重建SHA。例如5477460的44B记录跨seg3570与3571，中间36B来自WASM初始零；5484048的28B header由seg3699覆盖；nested5426156的40B也按seg3004/3005及初始零重建。这里的零是原件静态image规则，不是向独立None填零。

中间收据`164121.884802Z/review.json`（SHA `be1f9c92081005f799f4c039ae3e7c781d4ad0ae82b3bf0cadf923f732d6df46`）曾因错误要求单段完整覆盖而使用冻结声明AST fallback，**不作为最终独审依据**；它保留不覆写。最终收据已经移除该fallback，并重新完成完整审阅。

units最大11、pickups7、special4、windows2、boundaries69、owned2、live32为2、candidates3。只比较count的effects120、delayed56、hits112、active84、timed12、deadline32、secondary112、XP/currency queue域最大值全部为0，没有用非空payload的count伪装验收。packet队列最大565条，完整payload保留并核对捕获结构，**其未建模的payload语义仍只作观察**。distance map另用独立Dijkstra重算，78,400格、seed39340、可达72,660，u16 SHA `66afda2e7f733aebcf4f9204bbaa989b8d9310b317a1bcd6b9a23c1d65c71d32`。

旧schema3的120帧证据也由同一最终脚本以显式`--historical-frozen-sources`模式[复核通过](../evidence/opening-combat0135-independent-review-20261101T164545.326307Z/review.json)，SHA `2f386940452b169dc719a034a7f4bee8b2ebc52de01bd9436a2d628cd14813b9`。它准确重比旧6,255,343叶值，明确当前3份源已有变化；不把旧90源身份换成新94源，也不与新case计数求和。

本结论限于一个human warrior、seed0、navFalse、静止约25秒的受控尾部组合，仍显式依赖独立预解析world、原件snapshot上下文和外部clock。不是完整880、native Windows执行或完整一局验收。最终审阅脚本SHA `eef4d27841357cd445bb250e0d60803d5efe965bebdf58d61d5fc7934f23c152`。
