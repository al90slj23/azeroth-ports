# 0.135.1 真正的胜利终态与完整消息

新增独立[terminal_transition135.py](../reconstruction/core_spec/terminal_transition135.py)，恢复 49037 真正触发后的完整声明域行为。[最终原件收据](../evidence/full0135-oracle-20261101T081314.600878Z/terminal-transition135-comparison.json)为 **416 组、832 次完整 49037、0 差异**；每组还执行真实 1560，合计 1,248 次原件入口。315 组实际进入 true 终态，213 组有非空移动来源，保留原始控制条件与再次调用的幂等行为。[机器报告](2026-11-01-terminal-transition0135.json)保存 SHA、范围和历史证据，不改此前 573 组或其他旧收据。

真实顺序是：`field400!=0 && phase2587==1 && !(flag2568&1)` → **先写 phase5** → 17119 逐个停止 marker 恰为 0 的移动 NPC → 17217 停止辅助 112B 对象 → 16340 停止未完成移动的 88B claims → 54810 发送 **232** 包 → action sequence 自增 → 1938 生成完整 victory 通知。这里实际 opcode 是 232；915 时钟的 234 不能与它混用。

三个 stop helper 各自保持原向量顺序，重复 GUID 不去重；每次停步更新当前与目标 XYZ、起始时间和 duration，辅助/claims 还分别写自身 +68/+76 时间。NPC marker、duration>0、结束时间比较与 claims 的反向 `!(now>=end)` 条件保持原差异。完整 424/112/88B backing 均保留，包括未触碰尾部；只处理实际 active prefix。非空真实控制验证得到 355 份完整 221 停步包，其 packed GUID、三个原始坐标 word、递增 movement sequence、stop flag 与 capacity 全部逐字节一致。

终态 232 包包含 packed source GUID 与自增前的 action sequence；315 份完整 payload/capacity 通过。两个序列均覆盖 u32 wrap。packet/notification 向量 capacity 增长也独立预测，既有消息不会被清空。

1938 victory 通知的字段顺序和内容完整恢复：type、time、level、kills、elites、guardians、bosses、damage、taken、gold、chests、class、hero、race、bg、left、recap。非 death 的 recap 是原件真正生成的 `{}`，没有将未知 death recap 伪装为空。52241 的数值行为是：非有限值写 0；绝对值小于 1e15 的整数用十进制整数；其他值按三位小数格式化。UTF8 中文、emoji、引号、反斜杠、换行、所有低位 control 字符、负零、±Infinity、NaN、舍入与整数阈值均有对照。71,417B 通知完整 payload 及每份字符串容量严格一致；9 职业、8 种族、12 地图的默认英文 fallback 标签与原始 data 对照，29 项[字符串证据](../evidence/terminal-transition0135-static-20261101T075941.450411Z/label-evidence.json)已保存。

本轮发现真实 constructor 的另一条消息来源：空 profile 的暗夜精灵速度与初始 7 不同，1560→1512 因 `abs(newSpeed-oldSpeed)>0.01` 更新速度并递增 action sequence，48066 发送 **226** 包。该包包含 packed source GUID、旧 sequence1、速度 f32。本轮从已恢复的构造数值独立推导并验证 19 份原始前缀，完整保留后再追加终态消息。旧 initial151 只投影数值/owned 与 raw2592，不能将本轮新增消息验证倒算为旧批已验证的范围。

最初 [080227 观察批](../evidence/full0135-oracle-20261101T080227.520452Z/terminal-transition135-probe-receipt.json)只捕获真实构造器→终态，明确不是独立模型验收。[080958 失败批](../evidence/full0135-oracle-20261101T080958.210753Z/terminal-transition135-stderr.log)在 race4 终态执行前由“构造消息应为空”的断言拦住，保留失败及其源码快照。修复方式是恢复 226 来源与队列续传，没有删除该种族、清空原件队列或修改旧证据。最终 081314 是新 expected、新源码冻结后重新执行的完整 416 组。

最终比较覆盖 2,451,456B backing、10,608B 首阶段完整 packet payload 与每次 2,592B 游戏状态的所有 byte 变化。仅 1884/1896 两个已知堆地址 word 归一化，原始物理字仍保留在 sidecar；capacity、计数、字段、其他原始 byte 不加 mask。19 个相关原函数 body/签名、20 份生产/检查源码闭包（含包入口）、fixture/输出/artifact SHA 均冻结。878 个 host import 全部抛错且实际调用为 0；60 秒独立进程、512-page/32MiB 上限，实际约 3.85 秒，最大内存 20,578,304B。

当前完整行为域是**显式 absent terrain/collision 与有限 processed movement，flat height 开/关两种路径，以及默认英文 fallback 标签**。未知真实地形、其他本地化与被处理的非有限运动数据明确拒绝，共 5 项边界检查。没有伪造 SELF、Once、VFS，也没有调用 app start、网络、存档或 EXE。本成果恢复胜利终态这一组件，不宣称完整 880、真实 1089 开局或 death recap 已恢复。
