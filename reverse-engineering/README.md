# REA 逆向研究

与 [封装优化](../ports/README.md) 并行，研究原作实际发布的程序、资源与计算逻辑。现有安装包继续由 `android/`、`macos/` 构建，实验文件放在本区；当前没有恢复完整原作源码。

用户提供的 [bbylw/rea-cn](https://github.com/bbylw/rea-cn) 是中文文档站，真实工具是 [morluto/rea](https://github.com/morluto/rea) 的 npm 包 `rea-agents`。这里固定 **REA 6.8.0 + Node 22.23.4**，直接使用其 CLI；与 MCP 使用同一分析工作流，不要求本次对话先注册全局 MCP 或重启。工具、运行时及分析器安装不会进入游戏 APK。

## 已实际运行

- 原版网页核心 **0.126.0 / 3e72472a**：REA 已静态解析七个原版 JS 文件并保留完整 Evidence 和摘要。动态导入、WASM 内部行为与部分语义仍未知，不能把关系图称为完整源码。
- 原生 Windows 参考 **0.102.3 / f78e6fab**：REA 已读取 PE 导入表并检查 Rust 元数据；未发现 `.dep-v0` 依赖表，只读到编译器路径线索。它与当前封装核心版本不同，不能直接套用偏移或规则。
- 具体记录见 [首轮分析报告](reports/2026-11-01-initial-rea.md)；后续工作见 [研究问题](QUESTIONS.md)。

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
```

`analyze_web.py` 将七个逐字节相同的原文件复制到新建证据目录，声明选取范围后交给 REA；不会递归分析工具目录、大型游戏数据或用户存档。每次运行生成独立 `evidence/<UTC时间>-web/`，包含原文件哈希、完整 `application.json` 和 `summary.json`，后续查询复用完整 Evidence。原生脚本同样只读，并校验独立版本的大小与 SHA-256。

更多命令可通过 `python3 reverse-engineering/scripts/rea.py --help` 查看。将来需要 MCP 时，可使用这份固定安装执行 REA 的针对客户端设置预览；当前 CLI 可直接工作，尚未向 Codex 注册 REA MCP。

## 当前工具边界

| 目标 | 状态与下一步 |
|---|---|
| 原版 JS 启动层、资源路径、存档／插件桥 | 已跑通 REA 静态分析；动态值须进一步追踪或运行观测。 |
| 90,116,970 字节的原始 WASM | REA 6.8.0 的 WABT 适配器单文件上限 8,388,608 字节，不能直接接收完整核心；同时要求外部 WABT 1.0.42。当前没有声称完成其反编译，也不把随意切片当完整模块。后续研究原生对应逻辑，或单独扩展、验证大 WASM 分析能力。 |
| 原生 Windows EXE 的导入表／Rust 元数据 | 已运行无目标执行的 REA 检查；元数据不是函数实现或源码。 |
| 原生函数、伪代码、调用关系 | 需要配置 REA 的 Ghidra／Hopper 等提供方，目前未就绪。优先确认目标版本，再接入引擎并追踪具体函数。 |
| 模型／特效与真实战斗数值 | 已有资源入口可作为线索；实际加载、计算位置和修改效果仍按问题逐项验证。 |

依据固定发行包中的 `dist/wasm/WabtRelease.js`、匹配工作流及 [官方 WASM 指南](https://github.com/morluto/rea/blob/main/docs/wasm-artifacts.md)。说明文档 main 可能领先发行包，执行以本地 6.8.0 的 `--help` 和实际结果为准。

## 文件安排

- `toolchain.json`：工具版本、包完整性和能力限制；`.toolchain/` 保存本地工具。
- `targets.json`：明确区分网页核心与旧 Windows 原生基线；`local.sources.json` 只保存本机文件位置，不提交。
- `scripts/`：固定版本启动器和可复现分析入口。
- `reports/`：可进入 Git 的精简结论，保留 Evidence ID、范围及未知项。
- `evidence/`：原始报告与只读输入副本，仅本机保留；`originals/`、`work/` 也不提交。

研究结果接入正式封装时，固定原始 SHA-256、记录精确补丁和回退方式，并运行对应回归。单机规则实验与官方合作同步分别验收；显示数字的变化不能当作真实伤害／生命值修改成功。
