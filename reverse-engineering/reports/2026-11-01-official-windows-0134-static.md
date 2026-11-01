# 官方 Windows 0.134.0：已取得并完成原生静态拆分

日期：2026-11-01（Asia/Taipei）。本次官方 Windows 更新入口公布 **0.134.0**；已取得其 EXE，大小与官方 SHA-256 完全一致。静态证据确认这是 **x86-64 Rust / Bevy 原生程序**，可以作为后续游戏规则研究的主要 Windows 目标。现有 Web 0.126.0 与旧 Windows 0.102.3 的成果仍各自绑定原件，不能把它们的地址、布局或算法结论直接标成 0.134.0。

## 来源和身份

来源是[官方网站](https://wow.aethus.pl/)的[Windows 更新清单](https://wow.aethus.pl/exe/latest.json)。清单将三个官方分片列为 `0.134.0/part-000.bin` 至 `part-002.bin`。分片拼接为 gzip 流，解压过程校验 CRC/ISIZE；最终 EXE 与清单同时匹配：

- 版本：`0.134.0`。
- 大小：`147,793,408` bytes。
- SHA-256：`ed7dc687778ef7a613531f1eb6e25766fe06a63552115ebbd024fdede7d1a3f6`。
- EXE 内另有两处 `0.134.0` 字面，与清单一致。未确认独立 build 短哈希；不据此补造 build。

全部下载、解压原件、工具调用输出和证据均保存在 RuiRui4TB 外盘。这里验收的是**官方更新 EXE**；完整资源 RAR 的下载与验收另行记录。本轮未执行 Windows 程序、Wine 或虚拟机，也未修改安装包。

同一官网的[常规 Windows RAR](https://wow.aethus.pl/download/AzerothSurvivorsWindowsNew.rar)另有明确结果：从已逐段核验的连续 33,554,432-byte 前缀中，完整解包并通过首文件 CRC 的 EXE 为 **139,691,008 bytes**，SHA-256 `2c2f3926e1f8f8092809f5de0624ac8f2197bb341a2870d408ce0250f13f094a`，与已固定的 **0.102.3 / f78e6fab** 原件完全相同；其版本字面也包含相邻的 `f78e6fab0.102.3`。因此常规资源 RAR 中的首 EXE 仍是旧版，官网更新清单才提供本报告的 0.134.0 EXE。首文件解包成功不等于完整 RAR 已下载或资源包已验收；完整 RAR 尚未完成。来源回执、身份和版本候选分别保存在 acquisition 目录的 `rar-first-exe-receipt.json`、`rar-first-exe-identity.json`、`rar-first-exe-version-candidates.json`，哈希见本报告 JSON 附记。

## 原生架构证据

系统 `file` 与 `objdump` 均识别为 PE/COFF x86-64；本地只读解析得到 PE32+、GUI subsystem 2、ImageBase `0x140000000`。共六个常规 PE section，`.text` 原始大小 `103,535,104` bytes；`.pdata` 为 `4,343,808` bytes。未发现 section 末端 overlay 或 CLR directory。

导入表成功解析 **33 个 DLL / 425 项符号**，包括 Win32 窗口、输入、GDI、OpenGL、Winsock 等原生接口。EXE 保留 **779 个项目 crate 源路径字面**，包括 `wenilla-rogue` 的游戏模块；还保留 Rust 标准库编译路径，以及 `bevy_app`、`bevy_ecs`、`bevy_render` 0.18.1、`wgpu-core` 27.0.3、`wgpu-hal` 27.0.4、`winit` 等依赖源路径。这些是原生 Rust 游戏引擎的正面证据。

本 EXE 未命中 WebView2、Chromium、CEF 等运行时标记，也没有 WASM v1 魔数。扫描中两次出现的 `Electron`，完整上下文均为根证书名称 **Agence Nationale de Certification Electronique**；不属于 Electron 框架证据。上述检查不能排除尚未检查的压缩资源中的任意内容，但足以说明不能把这个 EXE 当成由后缀猜测的网页壳。

## 与已固定核心的可映射入口

| 比较项 | Windows 0.102.3 | 新 Windows 0.134.0 | 固定 Web 0.126.0 基准 |
|---|---:|---:|---:|
| 与 Web 共有的 crate 源路径字面 | 684 | 735 | 按完整路径归一化比较 |
| 113 个能力标识的字面存在 | 112 / 113 | 113 / 113 | 113 项 |
| 9 个职业标识的字面存在 | 9 / 9 | 9 / 9 | 9 项 |

新原生与 Web 共同保留 `game/abilities.rs`、`game/enemy.rs`、`game/upgrades.rs`、`game/talents.rs`、`save.rs` 和 `screens/cards.rs` 等路径，可以继续沿同一模块定位。这里比较的是**字面存在**，没有宣称恢复了新版目录表或证明所有技能行为相同。

已把五组已知升级表的完整二进制序列重新定位到**新版自己的** `.rdata`。下表列第一组连续候选地址；伤害、冷却等序列另有重复，完整位置见 JSON。

| 字节序列 | 新版候选 VA | 原文件偏移 |
|---|---|---:|
| f32：0.18、0.25、0.34、0.46、0.65 | `0x147113594` | 118561684 |
| f32：0.07、0.10、0.13、0.17、0.23 | `0x1471135c0` | 118561728 |
| u32：1、1、1、2、2 | `0x1471135f0` | 118561776 |
| f32：0.12、0.18、0.25、0.35、0.50 | `0x147113620` | 118561824 |
| f32：0.15、0.22、0.30、0.40、0.60 | `0x147113650` | 118561872 |

数值相同只建立定位入口，不能代替调用者、状态写回与消费者的重新验证。官方 0.134.0 说明还明确包含增强萨满重做与 Ice Barrier 上限变更，说明即使若干表未变，也不能将旧版全部规格视为最新版规则。

## 继续研究的版本路线

采用 Windows 0.134.0 作为新的原生主要目标，并为它新增独立 SHA 绑定。既有 0.102.3 原生脚本的哈希/偏移拒绝机制应保留；既有 0.126.0 Web 数值规格和原件对照也保留，以供回归比较。

后续从上述新地址、共同源码路径和**本版** `.pdata` 选择少量函数，再在 Ghidra 12.1.4 中建立各函数的新边界和调用关系。没有必要为切换研究主目标重建一个项目；需要的是新增本版证据和逐项验证差异。Web/Mac/Android 的核心版本升级属于独立变更，必须先确认其原件身份，再迁移现有补丁和测试。

## 复现与检查

```sh
python3 reverse-engineering/scripts/inspect_official_windows.py \
  reverse-engineering/originals/official-acquisition-20261031T235700.049192Z/windows-0.134.0
```

脚本只依赖 Python 标准库；静态扫描不会执行目标。输入和输出必须位于 RuiRui4TB，输出必须是新的 ignored evidence 目录。目录中的每份原件在扫描前后都计算 SHA-256。

本次正式证据：`evidence/20261101T000304.822273Z-official-windows-inventory/`，包含完整目录清单、PE/导入/资源解析、路径交集和固定 Web 对照。PE 解析错误为空，EXE 与 Web 原件前后 SHA 保持一致。旧版实跑验证保存在 `evidence/20261101T000031.347137Z-official-windows-inventory/`。

机器可读摘要和证据哈希见 [2026-11-01-official-windows-0134-static.json](2026-11-01-official-windows-0134-static.json)。本报告只完成原生身份、结构和比较入口的静态拆分；没有宣称整份原生自动分析、反编译、原始源码恢复或游戏行为验收已经完成。
