# Fixed135 开局的 guardian counter 与 endless 起始时间

固定 `0.135.1 / 90898d5e3`（历史截短 alias `0898d5e3`）的最小契约是：**G1092 由 constructor 显式产出 0；G404 保留未知，直到实际写入或进入会读取它的分支。** [静态追踪收据](../evidence/opening-context0135-static-20261101T162606.918252Z/trace.json) SHA256 `23cd5c4c313bd7406ad589a250f86be4d4750cbd18d96fce734bd0d0d6f9824d`；原 WASM SHA256 `c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2`。

1560 的 Game 源区域从 scratch+88 开始。它先把 scratch2811..2818 写为零，再以 i64 把 scratch2812..2819 复制到 scratch1177..1184。因此 G1092..1095 对应 scratch1180..1183，精确来自已经写零的 scratch2815..2818。6730 调用 1560 后复制完整 2592B Game；其后置配置写入没有覆盖这两个目标字段，1089 的相关字段也没有另行写入。

G400 来自 scratch488 的显式 u32 零。相邻 G404 对应 scratch492..495，在该构造路径没有初始化写入；selected-profile376 的复制止于 scratch479，不能把它解释成 profile 提供的零。完整 Game 复制会保留其物理字节，但独立状态应保留 `None`。16341 与 42327 都先检查 `G400 == 1` 和 `(G2568 & 1) != 0`，满足后才读取 G404；未进入该分支时 `endless_start404_bits=None` 合法。914 的首次终 Boss 胜利分支先把当前 G2352 写入 G404，再设 G400=1。

G1092 是累计击杀 guardian 的计数。1938 读取该字段并输出原数据段的 `guardians` 键；914 的 U64≠MAX guardian 死亡分支递增它，并重置对应 special 槽和下一次到期时间。16341/42327 使用当前值提高后续 guardian 的生命与攻击。这是本次核实的真实改变路径；完整模块所有别名、批量复制和存储位置的 writer 分类没有在本次小追踪中穷尽。

[既有捕获对照](../evidence/opening-context0135-static-20261101T162606.918252Z/observations.json) 检查了 16 个显式空 profile 的完整 6730→1089 case（constructor/final 共32份）和既有120帧批的1683份完整 Game 捕获：G1092、G400、G404 的实际字节均为零，mode2582/endless2568 也均为零。G404 的观察值不能成为独立 producer 的初始化规则。受控批 G2540 实际为1，G2532为0；两者不能混用，本次没有恢复 G2540 的 producer，mode0 的未读域仍允许 `None`。本追踪只读取旧证据，没有执行原件或新增差分 case。

新 runner 只增加 `projection.field1092` 和 `projection.mode2582`，不增加 G404 的比较值。其 [单帧原件观察 pilot](../evidence/opening-combat0135-context-pilot-20261101T162919.589476Z/pilot.json) SHA256 `a03ca6a654c26a38dbd64086f9f637e54d52d1d194b3ec76739809c16fb6e90b` 验证 constructor/opening/14阶段的16份投影均为1092=0、mode=0，gzip流完整、进程 exit0 且已消失；这不是模型验收。冻结 runner SHA256 为 `6b1d777f8bae01f87d1e6cc99c7d2bea0246f57069111d87fbac9390f444eddb`。
