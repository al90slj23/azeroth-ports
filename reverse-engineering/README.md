# REA 逆向研究

与 [封装优化](../ports/README.md) 并行，研究原作实际发布的程序、资源与计算逻辑。现有安装包继续由 `android/`、`macos/` 构建，实验文件放在本区；当前没有恢复完整原作源码。

目前已将一条技能命中追到真实HP扣减与死亡状态，并把HP对象更新追到主机发送和客人客户端字节流入口。先看[核心还原图](CORE_MAP.md)，具体依据见[伤害计算](reports/2026-11-01-damage-core.md)和[合作同步](reports/2026-11-01-coop-sync.md)。这些是静态还原与离线协议验证，尚未完成真实联机验收或全部客户端字段应用追踪。

用户提供的 [bbylw/rea-cn](https://github.com/bbylw/rea-cn) 是中文文档站，真实工具是 [morluto/rea](https://github.com/morluto/rea) 的 npm 包 `rea-agents`。这里固定 **REA 6.8.0 + Node 22.23.4**，使用 CLI 和项目内的持久 MCP 会话，不要求注册全局 MCP 或重启客户端。工具、运行时及分析器安装不会进入游戏 APK。

## 已实际运行

- 原版网页核心 **0.126.0 / 3e72472a**：REA 已静态解析七个原版 JS 文件并保留完整 Evidence 和摘要。动态导入、WASM 内部行为与部分语义仍未知，不能把关系图称为完整源码。
- 首轮完整WASM解码：官方WABT验证并解码得到约1.3GB WAT；最初保留八个完整函数，关联原件范围和哈希，并使用REA Evidence库校验记录，定位 `presence` 发送实现。原版REA大小限制保持不变，历史快照见[WASM报告](reports/2026-11-01-wasm-deep.md)，后续函数与逻辑见核心还原图。
- 升级数值起点：找到五组分档系数、按状态计算的函数25242和调用者1065的字段写入，详见[升级数值报告](reports/2026-11-01-upgrade-values.md)；后续已独立追到实际伤害消费者。
- 后续伤害追踪：934中能力倍率进入命中基数和暴击，再调用933实际扣敌人HP、累计有效伤害并触发死亡状态；1107处理玩家减伤、盾和生命。上轮1065的写入仍可能是预览副本，不能混为即时战斗修改。
- 后续联机追踪：已区分WebSocket、中继、按peer确认层和应用层，找到主机/客人工厂及HP结果的实际封包/接收通路。纯离线工具覆盖8/11种中继标签、19/25种应用标签，以及opcode169值更新子集；未实现变体明确拒绝。
- 内嵌 Lua：逐字节提取 API 源模板和角色面板，共50个命名函数、22种消息前缀；仅作语法编译，未执行目标。它们是辅助提取结果，详见 [Lua 报告](reports/2026-11-01-embedded-lua.md)。
- 原生 Windows 参考 **0.102.3 / f78e6fab**：REA 已读取 PE 导入表并检查 Rust 元数据；未发现 `.dep-v0` 依赖表，只读到编译器路径线索。它与当前封装核心版本不同，不能直接套用偏移或规则。
- Ghidra 12.1.4/JDK21 已接入，REA doctor九项通过；上次原生全量分析会话因用户重启电脑中断，尚不能宣称完成。遗留响应含 `provider_timeout`，配置期限为1800秒；这不能证明分析连续运行了30分钟或必然会超时。详见 [提供方安装记录](reports/2026-11-01-native-setup.md)。
- 旧原生定向分析：另用项目内Ghidra辅助脚本得到五个候选函数输出，其中两个完整解码函数支持系数与字段写入结论；一个存在错误控制流，已排除。此路线不冒称原版REA完整分析，详见 [原生函数报告](reports/2026-11-01-native-focused.md)。
- 历史起点见 [首轮分析报告](reports/2026-11-01-initial-rea.md)；后续工作见 [研究问题](QUESTIONS.md)。

## 使用

在仓库根目录运行，需要已有 npm 和 Python 3.11+：

这些脚本已在本机 macOS 验证；其他分析主机尚未验收。

```sh
# 只安装到本研究区 .toolchain/；不注册客户端、不替换系统 Node。
python3 reverse-engineering/scripts/rea.py bootstrap
python3 reverse-engineering/scripts/rea.py --version

# 需要原有已验证官方快照；先校验原始 WASM 和每个 JS 哈希。
python3 reverse-engineering/scripts/analyze_web.py

# 显式指定已建档的旧原生参考；也可填本机 local.sources.json。
python3 reverse-engineering/scripts/analyze_native.py --exe /path/to/original/AzerothSurvivors.exe

# 本地辅助工具：完整当前 WASM 解码、指定函数 Evidence 与内嵌 Lua 提取。
python3 reverse-engineering/scripts/wasm_setup.py
python3 reverse-engineering/scripts/wasm_focus.py
python3 reverse-engineering/scripts/extract_embedded_lua.py

# 可选原生分析提供方；固定 macOS ARM64 工具，只安装到 .toolchain/。
python3 reverse-engineering/scripts/setup_native.py
python3 reverse-engineering/scripts/decompile_native_focus.py --exe /path/to/original/AzerothSurvivors.exe --timeout 180
```

`analyze_web.py` 将七个逐字节相同的原文件复制到新建证据目录，声明选取范围后交给 REA；不会递归分析工具目录、大型游戏数据或用户存档。每次运行生成独立 `evidence/<UTC时间>-web/`，包含原文件哈希、完整 `application.json` 和 `summary.json`，后续查询复用完整 Evidence。原生脚本同样只读，并校验独立版本的大小与 SHA-256。

更多命令可通过 `python3 reverse-engineering/scripts/rea.py --help` 查看。`rea_native_session.py` 通过标准输入 JSON Lines 驱动一份 REA MCP 进程，保留每次请求与响应；它也不会向 Codex 注册全局 MCP。原生工具诊断通过不保证大型目标的完整自动分析会完成。

## 当前工具边界

| 目标 | 状态与下一步 |
|---|---|
| 原版 JS 启动层、资源路径、存档／插件桥 | 已跑通 REA 静态分析；动态值须进一步追踪或运行观测。 |
| 90,116,970 字节的原始 WASM | 已完整验证／解码；只对选定完整函数作局部逻辑恢复。REA原版接口不能容纳该核心及1.3GB输出，因此本地扩展明确单列，未修改上游限制。WAT不是原始Rust源码。 |
| 原生 Windows EXE 的导入表／Rust 元数据 | 已运行无目标执行的 REA 检查；元数据不是函数实现或源码。 |
| 原生函数、伪代码、调用关系 | 两个完整解码函数支持旧版系数与字段写入结论；其余三个候选不能等同为可靠行为还原。完整REA分析尚未完成。 |
| 真实战斗数值 | 已追到一条完整命中与敌人HP/死亡，以及玩家受伤主干；反伤、全部技能和逐帧一致性尚未恢复。 |
| 合作同步 | 已追通HP结果到远端客户端字节流的静态路径，部分协议已有离线转写；最终客户端应用、真实送达和完整权限仍待验证。 |
| 模型／特效 | 资源入口已有线索；实际替换与效果验证仍未开展。 |

依据固定发行包中的 `dist/wasm/WabtRelease.js`、匹配工作流及 [官方 WASM 指南](https://github.com/morluto/rea/blob/main/docs/wasm-artifacts.md)。说明文档 main 可能领先发行包，执行以本地 6.8.0 的 `--help` 和实际结果为准。

## 文件安排

- `toolchain.json`：工具版本、包完整性和能力限制；`.toolchain/` 保存本地工具。
- `targets.json`：明确区分网页核心与旧 Windows 原生基线；`local.sources.json` 只保存本机文件位置，不提交。
- `scripts/`：固定版本启动器和可复现分析入口。
- `reports/`：可进入 Git 的精简结论，保留 Evidence ID、范围及未知项。
- `evidence/`：原始报告与只读输入副本，仅本机保留；`originals/`、`work/` 也不提交。

研究结果接入正式封装时，固定原始 SHA-256、记录精确补丁和回退方式，并运行对应回归。单机规则实验与官方合作同步分别验收；显示数字的变化不能当作真实伤害／生命值修改成功。
