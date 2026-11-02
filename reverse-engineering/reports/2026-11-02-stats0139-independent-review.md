# Fixed139 属性重算 1542：异作者只读独审

**本批 fresh139 的 10,569 次完整 1542 调用、359,346 个声明数值全部通过独立重算。** 独审没有运行 production、作者 model/checker/builder/tracer、原件 WASM 或客户端，新增原件调用为 **0**。此前 135/138 的通过记录和单独 12-case pilot 均未计入。

- [作者正式比较](../evidence/stats0139-oracle-20261102T020320.478498Z/comparison.json)，SHA `9f667e74d304eed1b36dd56e06c1d17e941ab87e29e558e0dd6b3fec4c316de8`。
- [独审程序](../scripts/review_stats139.py)，SHA `175667eded3461b118ddc2b7e47ee29517434b0bee7dfe77d4e388a9cc327473`，仅 Python 标准库。
- [完整独审收据](../evidence/stats139-independent-review-owned-20261102T023549.515551Z/review/review.json)，SHA `772dee0e4e70f9e9b4af463ecd8473b33cddc19706dccaf6a9c1d556c1b7ffb7`。
- [结构化报告](2026-11-02-stats0139-independent-review.json)。独审 owned PID 83104 在 10.06 秒正常退出，PID/PGID 均消失，期限 240 秒。

## 当前版本绑定

对象是固定 **0.139.0 / f79c5e2b4**，原件 92,511,151 字节、SHA `71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299`。1542 为 `(i32)→void`，body 4,745 字节、SHA `43d5e3cd844d1cf156dd0cb058dc05c0a33ce41280649000a7a2b2d3a8f0a72c`。

直接解析当前原件和 export-only 私有模块：除 section7 外所有段逐字节相同，只新增 1542 与 stack global0 两个导出。malloc 93344、1542 的八个直接 callee 身份／签名／完整 WAT 重新绑定；未替换 callee。这里不声称八个 helper 的所有分支分别获得了动态覆盖。

职业默认 `5877920`／表 `1601376`，种族默认 `5874636`／表 `1601216` 均从 **139 本体**重读；核全部 256 个 byte selector 的查表和 fallback，9 份职业 HP/armor、8 份种族声明、14 条种族 modifier 与当前模型常量一致。

数学 reference 的语义 accumulator 代码允许复用，输入数据和结果必须重核。独审自己的 alpha／静态地址 relocation normalizer 重新核对了 **1,959 条当前 numeric 前缀指令**，涵盖七类来源、derived/HP/pool/speed 输出；normal form SHA `58f0c46e1ad5e2a25c42093cb90f81f3b2aaa423bb30b15836b115e13ce3b218`。只读旧二进制／WAT 用于静态结构对照，没有读取旧 expected、actual 或通过收据。这个结构依据不等于完整函数语义证明，更不转移旧版本动态验收。

另核当前 BTree 尾部三处 low0／high-local2 的双 u32 临时写法及键 22、28、1109；与捕获数值一致。完整 BTree 节点和 heap 所有权仍不在本批恢复范围内。

## fresh139 结果及范围

每 case 的 34 个数值包括 23 个 derived、HP、4 个 auxiliary、3 个对象字段、speed、sequence 和 queue count。合计 **295,932 个浮点词、63,414 个严格整数词**匹配；NaN 只按类别比较（1,060 次），其余有限值、无穷和 signed zero（含 442 个负零）均逐词精确。armor cap1572 从原件的单次有序 accumulator 出发重算，没有在 wrapper 中再累计一次。

原件 raw Game 共 **27,394,848 字节按已声明字段绑定**，包括 **73,983 组七类 source vector header**。实际 timed pointer/count 为 **596/600**，reserve 为 **764**；legacy 参数名中的 768/2574 只是语义标签，实际 flag byte 为 2582。不能把这些 fieldwise 绑定写成整个 Game、vector backing 或 heap 逐字节相等。

矩阵实际覆盖 selector、class/race/level、passive/adjustment/item tags、有序混合、soul_link、timed expiry/index、live dominance/expiry、HP select、movement threshold 及 pool clamp 等受控分支。独立诊断包含 1,056 次 pool excess、494 次 conditional pool clamp、1,605 次 timed append、2,550 次 live dominance。它们是重算分支诊断，不能另外加算原件 case。

**1,537** 是真实 movement queue 条目和 sequence 决策数量；9,032 次未变时 header 保持 `0/4/0`，1,537 次变化时观察 capacity4。包 payload、完整队列 backing 和网络送达未捕获，继续保留未知。

331 个 fresh WASM instance，每 32 个 case 重建 instance，每个 case 仍单独分配零化 synthetic Game8192。独审从每 case 的 Game／七个 vector／adjustment definition／owned ID 分配数量重新计算 **101,736 次 stack guard**，与记录一致；另逐项核全部 10,569 个 1542 before/after stack=1048576。882 个实际导入名称／次序与原件完全相同且全部 deny，host calls 为 0，峰值内存 15,007,744 字节，32MiB WASM／512MiB JS heap 限制保留。原件 PID 43442 正常退出，PID/PGID 均消失；本独审未重新运行它。

13 个 current/frozen 源、5 个 production、19 条完整本地导入边和作者 handoff 的 7 个文件 hash 均核对；没有修改作者源、primary 或 registry。expected-first 的依据是冻结 checker 控制流和 prepared 记录，不是外部签名时间线。

七类来源仍是显式受控 snapshot：natural constructor/profile/talent/equipment/live producer、完整 BTree／物理包、自然 App／完整 880／连续整局，以及 Windows 原生 ABI 和执行仍须另做验证。本矩阵不代表 latest139 整局或跨版本迁移已完成，complete games 保持 0。

交付格式修整仅删除程序文件尾部一个多余空行，保留单个换行；完整 AST 不变。在同一冻结 10,569-case artifact 上重新只读独审通过，旧 `021851 / 8304ff72…` 收据、原程序与报告字节均保留在 `evidence/stats139-format-only-refresh`。没有新增或重复累计原件 case。
