# 0.139.0 敌人追击、接触伤害与历史：异作者独审

通过当前限定范围的只读独审。未执行作者生产模型、checker、builder 或原件；独审进程 PID 11299，exit 0，PID／PGID 均已不存在。作者 7 件和全部 72 个实验源保持原 SHA。

正式批为 3 个 fresh instance，每组真实 2945→1600→1108 产生四个原始 NPC，再执行完整 925：0.5×32、0.25×48、1×12，共 92 帧。共 101 个直接入口，剔除 2945／1600 setup 后为 95 个。未移动初始 NPC、清背景、重置血量、关闭感知或增加其他系统调度；这是独立 AI 组件批，未执行 2123 或完整主循环。

独参重新计算当前 925 的八邻接 BFS：每组完整 78400 个 u16 距离值、72660 个 visited，全量摘要均为 66afda2e…c71d32。初始 pathNone 之后确由首帧 925 生产 G2368 并保留，未固定为 None 或 uniform map。79 次实际追击均为 direct_clear，按当前 30179 的 0.3 间隔累计 2976 次导航采样；45 次 14 码截断、4 次 stop kind3、全部 83 条 movement221 完整一致。没有动态经过 blocked-flow，不把旧 135 的运行验收转记为当前通过。

52 次自然接触均解析到实际 NPC 名称 Kobold Vermin／classification0，经当前 1076 的 armor、非致死 HP、f64 总计／mob melee 分类、history48 与玩家字段 22／28 链。三组最终 HP 分别约为 169.080、187.621、195.567，均从 230 自然下降；未用回血或补满避开伤害。完整 925 消息增量为 135 条／6637B：83×221、52×330，全部字节与独参一致；开局另有 228 条完整消息一致。

全部 NPC 432B owner 原始存储共 158976B 从上一输出独立重放，已知运动／计时／角度写入严格匹配，未知部分严格继承，没有补零。NPC 共 111504 已知／47472 None，后者实际 43700 非零；history 共 18972 已知／15396 None，后者实际 12770 非零，资源指针及新分配未写字节继续保留未知。history 容量 4／8／16／32 增长、语义字符串和所有活动槽一致；本域最老记录恰为 10 秒时仍保留，没有覆盖 head 环绕、增长搬移或年龄大于 10 秒的修剪。

Game 非本入口写入域 230736B、其他背景 132480B 严格守恒；两 Rune、windows、special、69 boundaries、四 NPC owner、原有 owned80、23 属性、RNG、phase 与空 live/callback owners 全保留。每帧没有单独 pre925 捕获：守恒比较来自相邻输出，唯一时钟写入及未写 NPC 的约束绑定到冻结 driver，不能声称已额外捕获完整入口前内存。

72 个总源／59 个 production／237 条本地边、当前函数体、静态邻居／英文数据及所有非 export WASM section 均核对。作者两批失败（sequence／普通近战一 ULP 投影、stop221 不完整）与 2 帧 pilot 保留且排除，不叠加通过数。旧函数经有限替换整 WAT 相同只算静态补证，独参未执行旧模型或借其运行结果。

范围仍为当前默认普通近战、无 status／ranged／boss／guardian／pet、无 item／modifier／shield callbacks 的非致死域。blocked-flow、致死结算、动态新刷怪、AI 与玩家／移动／主循环 884 的联调、完整 UI／联机／存档、自然 bootstrap／externref／Windows 原生和完整游戏均未验收。研究与封装优化分开，目标未宣称完成。

详见[机器报告](2026-11-02-enemy-ai0139-independent-review.json)。
