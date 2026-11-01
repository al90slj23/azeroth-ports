# Windows 0.134.0：两段原生升级数值语义

日期：2026-11-01（Asia/Taipei）。本轮从官方新版 **Windows 0.134.0** 独立定位函数，已经取得原生指令级数值证据：一个五分支升级数值函数与 Web 0.126.0 的 25242 在已检查的有效输入路径上采用相同运算结构；另一个函数直接写回伤害/冷却浮点字段。没有执行 EXE、Wine、VM 或游戏，也没有修改原件、安装包、存档或既有版本配置。

输入为官方 acquisition 留存的 `AzerothSurvivors.exe`：147,793,408 bytes，SHA-256 `ed7dc687778ef7a613531f1eb6e25766fe06a63552115ebbd024fdede7d1a3f6`。官方来源与架构核验见 [新版静态清单](2026-11-01-official-windows-0134-static.json)。分析前后 SHA-256 一致；所有输入、证据、Ghidra 临时项目、JVM 临时目录、设置和缓存均在 4TB 外接卷。

## 新版独立定位与解码

脚本从本次输入重新读取 PE 节表、原始文件映射及 `.pdata`，搜索 `.rdata` 的五组完整 20 字节系数，再扫描 `.text` 中 `48/4c 8d`、RIP-relative ModRM 的 LEA 候选，匹配表基址及 ±4 字节。原始字节搜索先只视为候选；选中的七条 LEA 之后均通过两种反汇编器确认是真实指令边界，且原始字节一致。未使用旧 0.102.3 的函数地址。

| 本版 VA 范围（末尾不含） | 原始文件偏移 | 函数体 | 完整解码 | 结果 |
|---|---:|---:|---:|---|
| `0x145bb5e70..0x145bb6071` | 96,162,416 | 513 B | 108 条 / 513 B | 五路数值返回，五组表均有真实引用 |
| `0x145d6b220..0x145d6b482` | 97,953,312 | 610 B | 149 条 / 610 B | 读取两张表，乘法写回两个浮点字段 |

LLVM objdump 与 Ghidra 对所选范围逐条指令的地址、长度和字节完全一致，两个范围均连续覆盖、无缺失字节、无跨末端指令、无未解释的间接跳转。`.pdata` 边界和函数体哈希另存于 JSON。覆盖率本身不证明完整程序语义。

采用本项目专用 Ghidra 12.1.4 脚本，`-readOnly -deleteProject -noanalysis`，最大 JVM heap 4G，总 owned 进程期限 240 秒、每函数反编译期限 60 秒；正常退出，未触发期限。没有启动全量自动分析，也没有更改 stock REA。

首轮已经完整解码，但 Ghidra 将五项枚举跳转表继续扩展到无效 case，产生了范围外坏指令；**该轮 513 B 伪代码被拒绝**。第二轮按照本机 Ghidra 自带 `SwitchOverride.java` 的 `JumpTable.writeOverride` 接口，只指定从原件 `.rdata` 的五项 signed-i32 相对偏移解出的五个合法入口。表在 `0x147134110`，入口按分支 0..4 为 `0x145bb5e88`、`0x145bb5fa8`、`0x145bb5eec`、`0x145bb5f80`、`0x145bb5ec1`；五者均在本函数内并已解码。

第二轮没有坏指令、指令重叠或无法恢复跳转表的控制流警告。仍保留 globals 重叠、人工 switch override，以及 getter 的 unknown calling convention 提示。getter 的 `float(state, byte kind, u64 tier)` 是依据 RCX/DL/R8 输入和 XMM0 返回所作的分析者标注，并非恢复的 Rust 类型。结论同时核对实际 SSE 指令，不单凭 C 文本；Ghidra 的 C 条件未完整呈现 MAXSS 的 NaN 选择规则。

## 五分支与 Web 25242 的交叉证据

下表仅描述 `kind=0..4`、`tier=0..4` 的有效分支，计算全部为 binary32。`positive_or_zero_non_nan(x)` 由本版 `XORPS XMM1,XMM1; MAXSS XMM0,XMM1` 实现：负数、NaN 和零取 +0。tier 越界路径调用错误处理并落到原始 `0f0b` UD2 陷阱；UD2 被单独记录，不冒认为尚未解析的游戏间接跳转。

| 分支 | 本版表 VA，五档值 | 本版数值结构 |
|---|---|---|
| 0 | `0x147113594`：.18, .25, .34, .46, .65 | `A[tier] / (1 + .5 * u32(state + 0x24 + 4*kind))` |
| 1 | `0x1471135c0`：.07, .10, .13, .17, .23 | `B[tier] * positive_or_zero_non_nan((f32(state+0x14) - .2) / .8)` |
| 2 | `0x1471135f0`：1, 1, 1, 2, 2（u32） | `f32(min(saturating_sub_u32(cap, u32(state+0x18)), C[tier]))` |
| 3 | `0x147113620`：.12, .18, .25, .35, .50 | `D[tier] * positive_or_zero_non_nan((5 - f32(state+0x1c)) * .25)` |
| 4 | `0x147113650`：.15, .22, .30, .40, .60 | `E[tier] * positive_or_zero_non_nan((6 - f32(state+0x20)) / 5)` |

分支 2 直接读取 `*(state)` 指向记录的 `+0x75` 字节：不为 11 时 cap 为 12；为 11 时，仅 `seal_fate`、`soul_fire`、`lightwell`、`faerie_fire` 四个精确 ID 的 cap 为 2，其余为 0。这些 ID 比较可从原生立即数和字符串长度分支独立还原，未靠名称相似推断。

五组表的原始字节哈希与 [Web 升级数值报告](2026-11-01-upgrade-values.json) 中 A..E 全部相同；五分支运算结构、cap 选择和非 NaN 正值截断也一致。对应字段依次为冷却f32、数量u32、范围f32、持续时间f32；原生偏移为20/24/28/32，WASM为16/20/24/28；分支次数首偏移原生为 36，WASM 为 32。不能把 Web 的 80 字节记录布局、调用者索引或地址直接搬到 Windows。

本版五条 bounds-error 源位置记录均指向 `crates\\wenilla-rogue\\src\\game\\abilities.rs`，行号依次为 202、204、211、214、217；Web 对应为 195、197、204、207、210。五处均增加七行，进一步支持函数对应关系；仍不能由此证明两版本其余能力行为没有变化。

本轮完成的是静态操作与字段对应核对，**没有运行原生数值 oracle，没有取得跨版本 bitwise 输出对照**。已有 Web 的执行规格验证不能改称为 Windows 执行验证。

## 第二个函数的真实字段写回

`0x145d6b220` 对输入档位 1..5 读取另外两份相同系数表：伤害表在 `0x1477ff758`、冷却表在 `0x1477ff6f0`。两个互斥分支分别执行：

```text
0x145d6b2fb MOVSS XMM2,[RAX + RCX*4]   ; RCX = tier - 1
0x145d6b300 MOVSS XMM0,[0x1462c45a8]  ; 1.0f
0x145d6b308 ADDSS XMM0,XMM2
0x145d6b30c MULSS XMM0,[RDI + 0x10]
0x145d6b311 MOVSS [RDI + 0x10],XMM0

0x145d6b339 MOVSS XMM6,[RAX + RCX*4]
0x145d6b33e MOVSS XMM0,[0x1462c45a8]  ; 1.0f
0x145d6b346 SUBSS XMM0,XMM6
0x145d6b34a MULSS XMM0,[RDI + 0x14]
0x145d6b34f MOVSS [RDI + 0x14],XMM0
```

即输入记录 `+0x10 := old*(1+x)` 或 `+0x14 := old*(1-x)`。输入档位为零时另有复制分支；还观察到生成结果记录/文案的流程。此函数尚未追到调用者和实战消费者，不能断言它就是上述五路 getter 的写回方，或把这里的冷却乘法等同于 Web 1065 的另一种减法写回路径。

## 本地证据与复现

```sh
python3 reverse-engineering/scripts/decompile_latest_native_focus.py --timeout 240
# 仅原始PE定位与LLVM解码，不启动Ghidra：
python3 reverse-engineering/scripts/decompile_latest_native_focus.py --scan-only
```

成功 evidence：`evidence/20261101T000726.720192Z-latest-native-focus/`；被拒绝的首次 getter 输出：`evidence/20261101T000618.049027Z-latest-native-focus/`。完整指令、C、PE 映射、表字节、跳转表、来源行记录、日志及函数哈希均保留在 ignored evidence。公开 [JSON 摘要](2026-11-01-latest-native-focused.json) 记录每项证据哈希、边界校验、公式与限制，不加入原始 EXE。

接下来需要独立追本版 getter 的调用者、五类升级实际写回及战斗消费路径，再针对官方 0.134.0 的完整能力与吸收改动补证。本轮尚未恢复完整程序、全部调用图、原始 Rust 类型或所有战斗公式。
