# 0.135.1 辅助移动对象 owner：G656 / G660 / G664

新增 `core_spec/motion_aux_owner135.py` 独立维护 auxiliary112。它与 secondary112 的 G1856 / G1860 / G1864 是不同向量，不能互换。现有 headless、AI、terminal、death 和其它共享模块没有在本批修改。

1560 原文的 Game 是 scratch+88：scratch740 写入 i64 0，覆盖 G656 容量 0；scratch748 写入 i64 8，给出 G660 指针 8 和 G664 数量 0。8 是对齐的空向量哨兵，不是新分配 backing。独立 initializer 从真实 `InitialState135` 空 profile 构造物建立这个 owner，不读取原件内存、快照或存档。允许真实 phase1 opening handoff 的构造物，但仍须验证 opening 继承，不通过修改 phase 伪造构造。

## 可接 API

- `from_empty_profile1560_aux135(initial)` 返回 `MotionAuxOwner135(capacity656=0, pointer660=8, storage112=(), count664=0)`。应在构造/opening 入口持久保存，不能到 fatal 才临时创建。
- `inherit_motion_aux135(owner, before, after)` 返回同一个 owner 对象。缺 owner、非空或重新分配的 owner，以及未知 producer 都会明确拒绝，不会清空记录。
- `MotionAuxAdmission135` 必填：`event, phase2587, mode2582, flag2576, class360, race361, definitions88, source_counts`。`definitions88` 是全部实际 owned 与 racial 的 `(pointer, raw88hex)`；只接受 cleave、thunder_clap、demo_shout、battle_shout、perception 的固定完整定义 SHA。选择事件另需实际 `selected_kind2585=0`。
- `source_counts` 固定顺序：`604, 652, 2032, 2056, 1804, 1852, 1816, 1828, 1840, 1864, 2116`。必须取同一独立 canonical state 的真实 source owner，不能从泛化的 level 空 tuple 猜测。
- 支持 opening1089、当前十四阶段、kind0 selection1072、已恢复的 local motion2328 / correction199。phase4 只准许同帧余下 `collect / claims / spawn / special / terminal` 保持 4→4；不能重新进入 player、AI 或 extra 规划。

## 原件静态依据与边界

真实新增函数1680会在 G664==G656 时对 G+656 调用65336，写入112字节记录并递增G664。索引中的全部直接调用来源是984、5745、10146。984在G2056修饰器空时提前退出；5745仅来自916/984/1089/10146；916受空G604定时源、空G652 active84及空aux约束；1089的直接5745路径受flag2576约束，而10146的两段均由G2032物品源约束。当前五种精确技能分别走已恢复的 execution5/effect0、execution2/effect1或11、execution9/effect8，不进入召唤路径。1072与4600无直接auxheader访问，保持kind0技能选择的明确来源边界。

phase4的2573与49037有真实phase1 guard；其它剩余步骤只允许其已恢复生产域，不把phase改回1。915原件没有416读取：现有headless的416==0仅属组合实现边界，本aux接口不把它当作原件必要条件。

保留未恢复项：非空召唤、物品/修饰器 proc、active timed/extra、未支持技能、网络/远端替换和一般全程序 alias 分析。已列36个完整原件函数及其body/WAT SHA与窗口；这不等于恢复所有全局写入者。

## 历史验证

新模型先以独立构造规则和已冻结旧模型期待生成全部aux header期待，冻结后才完整读取历史moving460 CAS。原件观察的0没有喂入模型。旧模型未包含此新owner模块；历史边界和新模型来源分开记录。

- 原460帧中6490个header快照、19470个header字段/77880字节，以及71390个来源guard字段，全部0差异。
- 覆盖1次constructor、1次opening、14×460个阶段、44次local motion、4次实际kind0选择。CAS完整finish 6952记录、2139516743逻辑字节。
- 历史只实际出现cleave、thunder_clap、battle_shout、perception；demo_shout有固定定义/分支静态依据，未追加原件运行或把它算入该460的动态覆盖。
- 2032/2056/1840/1864在旧投影中缺省：新期待来自明确构造及无已支持producer证明；随后与原件rawGame逐阶段核对。没有用actual回填。
- 五项phase4尾续只属静态规则与模型检查；历史460只有phase1/2，未提升为原件fatal验收。
- 20个来源、48条导入边保持一致。受管进程62018在180秒期限内以0退出，用时18.16秒，PID/PGID均消失，stderr为空。

新增原件调用与帧数均为0。前两次同数据探索收据保留但不累加覆盖。最终证据 `evidence/motion-aux-owner135-20261102T005437.610338Z/comparison.json`，SHA `572c0a668e89bd03b966be6a8b8aff970a76812a640b0f882e16c08220879c9a`。尚待异作者独立审查；这不代表同状态完整fatal或全局游戏行为已经重建。
