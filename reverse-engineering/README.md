# REA 逆向研究

与 [封装优化](../ports/README.md) 并行，研究原作实际发布的程序、资源与计算逻辑。现有安装包继续由 `android/`、`macos/` 构建，实验文件放在本区；当前没有恢复完整原作源码。

最终目标是拆清全部逻辑与数据，形成能够独立重造的核心。**主研究目标现已切到官方0.134.0**，同版Windows原生程序与Web`983346a7`互证，见[版本策略](VERSION_STRATEGY.md)、[官方原生身份](reports/2026-11-01-official-windows-0134-static.md)和[新版原生定向反编译](reports/2026-11-01-latest-native-focused.md)。当前仍未形成可玩替代核心，进度与验收见[重造覆盖清单](RECONSTRUCTION.md)。

此前0.126.0已恢复主循环主干、9职业/113能力定义、选卡/施法/伤害、12区域及账号存档主干，并建立若干独立模型。它们保留为历史验证和新版迁移参考，不能直接计为0.134.0已支持；[核心还原图](CORE_MAP.md)明确区分两者。

HP对象更新经主机发送、客人解码、事件通道和注册系统到客户端字段写入已静态追通，见[事件投递](reports/2026-11-01-ecs-delivery.md)、[伤害计算](reports/2026-11-01-damage-core.md)和[合作同步](reports/2026-11-01-coop-sync.md)。该静态路径和离线codec尚未经过真实跨端联机验收。

用户提供的 [bbylw/rea-cn](https://github.com/bbylw/rea-cn) 是中文文档站，真实工具是 [morluto/rea](https://github.com/morluto/rea) 的 npm 包 `rea-agents`。这里固定 **REA 6.8.0 + Node 22.23.4**，使用 CLI 和项目内的持久 MCP 会话，不要求注册全局 MCP 或重启客户端。工具、运行时及分析器安装不会进入游戏 APK。

## 已实际运行

- 官方当前0.134.0：Windows更新EXE已按官方大小/SHA验收；Web同版快照已取得。原生PE身份、五表及两函数已重新定位，257条LLVM/Ghidra指令字节独立一致，未执行EXE。官网资源RAR首EXE精确匹配旧0.102.3，最新版程序走官方更新清单；完整RAR验收另记。
- 新版[完整WASM profile](reports/2026-11-01-wasm0134-profile.md)已完成验证、完整WAT和独立SQLite索引，覆盖175316个defined函数与824546条直接调用。它提供新版定位入口，不等于恢复全部游戏逻辑。
- 新版[114能力/9职业目录](reports/2026-11-01-catalogue0134.md)已从原件初始内存提取，并与旧版逐字段核对；新增stormstrike/rockbiter、移除call_of_flame，stoneform参数变化。定义计数不代表全部效果已实现。
- 新版独立实现对照：[升级原25368](reports/2026-11-01-upgrade0134-spec.md)11560例、[完整选卡原1073](reports/2026-11-01-selection0134-spec.md)779例、[完整扣血原914](reports/2026-11-01-combat0134-spec.md)454例均0差异。后两者保留完整原件内部callee、仅增加研究导出；所有878宿主导入拒绝且实际调用0次，未启动完整游戏。选卡比较80B+5标量，扣血比较HP/有效统计/死亡主字段；完整后处理、触发与掉落仍未实现。
- 新版[选卡→拥有记录→施法→扣血](reports/2026-11-01-selection0134-chain.md)已重新定位；[实际伤害链](reports/2026-11-01-combat0134-chain.md)确认单位改为424B，并新增按技能ID和目标状态累加的36B记录。新`combat134`独立实现该加区，旧`combat.py`仍只作历史参考。各模型的版本范围见[支持清单](reconstruction/version-support.json)。
- 新版[拾取XP→等级→候选入口](reports/2026-11-01-progression0134-chain.md)已定位，新版自然上限为120级；独立`progression134`与[完整新4630的2197例对照](reports/2026-11-01-progression0134-spec.md)0差异。phase3只由原末尾守卫跳过2159，属性/消息/治疗原callee仍执行；只验4字段，不称完整成长/候选生成已实现。
- 以下0.126.0结果是历史已验证参考；正按新版profile逐项迁移，不继续把旧版当主目标扩展。
- 原版网页核心 **0.126.0 / 3e72472a**：REA 已静态解析七个原版 JS 文件并保留完整 Evidence 和摘要。动态导入、WASM 内部行为与部分语义仍未知，不能把关系图称为完整源码。
- 首轮完整WASM解码：官方WABT验证并解码得到约1.3GB WAT；最初保留八个完整函数，关联原件范围和哈希，并使用REA Evidence库校验记录，定位 `presence` 发送实现。原版REA大小限制保持不变，历史快照见[WASM报告](reports/2026-11-01-wasm-deep.md)，后续函数与逻辑见核心还原图。
- 升级数值起点：找到五组分档系数、按状态计算的函数25242和调用者1065的字段写入，详见[升级数值报告](reports/2026-11-01-upgrade-values.md)；后续已独立追到实际伤害消费者。
- 后续伤害追踪：934中能力倍率进入命中基数和暴击，再调用933实际扣敌人HP、累计有效伤害并触发死亡状态；1107处理玩家减伤、盾和生命。随后已确认1065更新实际拥有的技能记录，由22136读取并送入施法，见[能力报告](reports/2026-11-01-abilities.md)。
- 主循环及世界规则：[阶段/计时/暂停](reports/2026-11-01-game-loop.md)、[地图/敌人/刷怪/经验](reports/2026-11-01-world-progression.md)、[账号存档与RSE1](reports/2026-11-01-save-schema.md)已形成可读静态规格，保留完整函数和未覆盖项。
- 独立可执行规格：[升级值](reports/2026-11-01-executable-spec.md)11560组、[两条生命成长曲线](reports/2026-11-01-world-progression.md)24636组、[半径helper及外层组合](reports/2026-11-01-radius-spec.md)29041组对照均0差异。这里执行了隔离原件数值函数；半径外层为重组，没有执行原934。完整游戏未启动，有限样本不代表全部输入或对局通过。
- 后续独立规格：[四字RNG/区间拒绝重抽](reports/2026-11-01-rng.md)18144组返回/状态一致；[经验舍入helper及XP投影](reports/2026-11-01-progression.md)30125组对照0差异，其中5482组为重组，未执行原3231。
- 技能和属性继续细分：[113能力的12kind/14tag与Fireball延迟命中链](reports/2026-11-01-cast-dispatch.md)、[9职业/8种族和真实属性重算](reports/2026-11-01-derived-stats.md)均保留具体入口/原始分派；未形成完整施法或属性替代实现。
- 历史可执行模型继续保留：[属性重算](reports/2026-11-01-stats-spec.md)完成原1573及原内部callee8495例；[选卡应用](reports/2026-11-01-card-apply.md)包括2345卡+1初始化片段及5例完整原1065；[战斗投影](reports/2026-11-01-combat-spec.md)包括9153片段及32例完整原933。完整模块研究副本只增导出、拒绝所有宿主调用，没有调用应用start；这些实验均属0.126.0。
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
| 当前0.134.0 / 90,953,762B WASM | 完整验证/解码/独立索引，新版升级值、拥有记录和扣血投影已做限定域原件差分；完整游戏未实现。REA原版大小限制未修改，本地扩展单列。 |
| 历史0.126.0 / 90,116,970B WASM | 保留完整WAT和已验证局部模型作迁移/回归参考；WAT不是原始Rust源码。 |
| 原生 Windows EXE 的导入表／Rust 元数据 | 已运行无目标执行的 REA 检查；元数据不是函数实现或源码。 |
| 原生函数、伪代码、调用关系 | 两个完整解码函数支持旧版系数与字段写入结论；其余三个候选不能等同为可靠行为还原。完整REA分析尚未完成。 |
| 真实战斗数值 | 已追到一条完整命中与敌人HP/死亡，以及玩家受伤主干；反伤、全部技能和逐帧一致性尚未恢复。 |
| 独立重建 | 历史0.126.0已有升级、成长、半径、RNG、经验、属性、选卡与战斗投影模型；正向0.134.0逐项验证和迁移，尚不能独立完成一局。 |
| 合作同步 | 已追通HP结果到客户端对象字段写入的静态路径；同一事件通道、注册表和系统回调已闭合。真实送达、渲染和全部权限/异常仍待验证。 |
| 模型／特效 | 资源入口已有线索；实际替换与效果验证仍未开展。 |

依据固定发行包中的 `dist/wasm/WabtRelease.js`、匹配工作流及 [官方 WASM 指南](https://github.com/morluto/rea/blob/main/docs/wasm-artifacts.md)。说明文档 main 可能领先发行包，执行以本地 6.8.0 的 `--help` 和实际结果为准。

## 文件安排

- `toolchain.json`：工具版本、包完整性和能力限制；`.toolchain/` 保存本地工具。
- `targets.json`：明确区分网页核心与旧 Windows 原生基线；`local.sources.json` 只保存本机文件位置，不提交。
- `scripts/`：固定版本启动器和可复现分析入口。
- `reports/`：可进入 Git 的精简结论，保留 Evidence ID、范围及未知项。
- `RECONSTRUCTION.md`、`reconstruction/`：全模块覆盖/验收清单和独立规则实现。
- `VERSION_STRATEGY.md`：当前0.134.0目标、历史参照、平台分工和增量迁移策略。
- `evidence/`：原始报告与只读输入副本，仅本机保留；`originals/`、`work/` 也不提交。

研究结果接入正式封装时，固定原始 SHA-256、记录精确补丁和回退方式，并运行对应回归。单机规则实验与官方合作同步分别验收；显示数字的变化不能当作真实伤害／生命值修改成功。
