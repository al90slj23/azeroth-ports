# 0.139.0 玩家更新、Human 感知与 live/Aura：异作者独审

通过当前限定范围的只读独审。未执行作者生产模型、checker、builder 或原件；独参进程 PID 78168，exit 0，PID／PGID 均已不存在。作者 11 件保持原 SHA。

正式原件批为 5 个 fresh instance／155 次完整 2123，每组先完整 2945→1600→1108→显式 5XP 的 4677→首次新 thunder_clap 的 1093。共 180 个直接入口，剔除 2945／1600 setup 后为 170 个；旧失败、pilot、旧 155 批和本次前一版只读核查均未叠加覆盖。内部 1238／1542／1173 没有插桩，其路径由当前函数体和实际结果证明。

独参从当前原件静态数据及此前独立 raw 派生 canonical world 重建开局、三卡与选择，再逐帧重算五种 cadence（8／10／10／116／11 帧）。四个原始存活静止 NPC、两 Rune、windows、special、69 boundaries 完整保留；实际 30 码查询有两个目标，未清 NPC、伪造无目标、关闭 racial 或使用无限冷却。Human 在 0.5 成功施放 perception：kind8 的 value12 为 0.15、有效期至 14.5、冷却 42；并非复用 cleave 的目标封包。原有 live12／1020 在 1.0 到期，perception 在 14.5 到期。5 次 racial 成功、6 次到期路径全部一致。

160 份玩家状态的完整 72 个逻辑字段（11520 值）、23 个派生属性（3680 值）、25600 个 owned80 字节、12800 个 racial80 字节，以及 RNG、技能计时、三套施法集合、phase 和 full BTree 解码一致。所有帧输入继承上一步完整 Game 2592B，仅显式写入当前时钟；共核对 401760B，另有 355725B 非本入口写入域的 Game 字节严格守恒。完整开局五类 owner 已与独参已知字节／None 对齐，后续 491040B 背景原始字节严格守恒。

live32 的移位复制、容量及 stale tail 从真实输入独立重放，共 19840B；其中新分配 perception 的 5 个 scratch word 共 20B 仅观察以继续物理链，独立确定的物理重放字节为 19820B，模型仍保留 None。live 共 8172 已知／12308 None，后者实际有 11543 个非零字节；Aura 共 32880 已知／90000 None，后者实际 77298 非零。1173 每次另分配 768B，inactive payload 属于新 owner，不能要求与旧 payload 守恒，也未用真实值补齐未知。

本域 2123 发出的 15 个包／240B 完整增量与独参一致：5×306、5×308、5×309；self 306 为 mask0 的 20B 消息。开局另有 380 条完整消息一致。45 个源文件／35 个 production／128 条本地边、当前函数体与全部非 export WASM section 均绑定核对。作者 postcapture audit 只作哈希绑定，没有用作独参。

该批使用既有合法 v2 资源上下文并新建 Game；显式 5XP、组件时钟与满血是输入条件。它未验证自然 App／world Rc／externref bootstrap、主循环 884、AI／移动输入、近距离主动伤害、正数治疗、其他技能或 live8／9、perception 无目标与精确 30 码边界、重复施放、完整 UI／联机／存档、Windows 原生或完整游戏流程。研究与封装优化保持分开，目标未宣称完成。

详见[机器报告](2026-11-02-player-update0139-independent-review.json)。
