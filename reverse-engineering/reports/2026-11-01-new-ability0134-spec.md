# 官方0.134.0新能力tier初始化与完整1073差分

目标固定为 **0.134.0 / 983346a7**，原件SHA-256 `2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52`。独立 `core_spec/ability_state134.py` 对真实完整原件1073的最终差分为 **2,781例、0字段差异**，其中 **114个definition × tier0..4 = 570例**。非零tier不再作为未实现分支拒绝，也没有通过只选tier0缩小主覆盖。

| 覆盖 | 例数 |
| --- | ---: |
| 全114个definition的tier0..4、显式空modifier |570|
| 全114个definition的原件额外tier5表项 |114|
| modifier数值kind与binary32/u32边界 |690|
| modifier所有筛选分派的匹配与不匹配 |200|
| 全114个definition的7个额外word，tier0/4 |228|
| 有序f32累加后才round/clamp |280|
| 合成definition的完整tier分类分支 |270|
| 固定seed的混合有序modifier快照 |400|
| phase/kind/index入口guard |14|
| append保留已有owned记录 |15|

## 恢复的独立接口与顺序

`initialize_ability(DEFINITIONS[b'cleave'], tier=4, modifiers=())` 返回完整80B `AbilityRecord`。`modifier_additional_bytes` 独立返回28B额外字段。`AbilityModifier134` 显式描述20B输入及复制出的ID/ID列表；模型不加载原件或证据文件。`modifiers=None` 在tier0也明确报 unresolved，只有调用者已经确定为空的快照才能传 `()`。真实天赋/装备等producer如何产生该向量尚未恢复，不能把未知producer当成空向量。

新版1073先初始化level1、countdown0.5、基础乘数1和零kind计数，再调用 **26967(G+2016, definition)** 写owned+52..79，最后调用 **26591(record,tier)**。26967按20B输入顺序逐次f32相加；目标数先完成累加，再执行原 **85718** 的binary32有符号0.49999997偏置/位截断，最后 `i32.trunc_sat_f32_u`。冷却额外乘数按照原select顺序取 `max(0.4, 1-sum)`，NaN归0.4。其他float字段逐f32；全部u32字段精确比较，NaN浮点只比较分类。

26591的tier0不查表。非零tier按原件表读取有序f32：伤害 `damage * (tierBonus + 1)`；冷却 `cooldown * (1 - tierReduction)`。execution9按effect-tag bitmask8384（6/7/13）选择伤害；execution11按声明kind列表是否含0；其他execution按definition.baseDamage48>0选择。114个真实definition中103个走伤害、11个走冷却。候选生成的当前域为tier0..4；tier5仅是原件helper额外表项的验证，未声称生成器会产出tier5。

`accept_new_ability_selection` 使用新版phase2579/selection-kind2577与canonical新能力ID候选，独立执行入口guard及owned append；共享天赋/装备/通知后处理、1513统计重算、4600收尾均返回明确pending effects。本报告的原件oracle实际执行完整1073尾部及其到达的原callee；这不构成独立模型已经实现该尾部的声明。

## 原件约束与证据

仅通过既有approved builder增加1073 research export；只改export节7，其他节和全部body字节未变。真实原allocator91940、878个host函数全部throw、未调用应用start。固定Node v22.23.4，heap512MiB与memory512pages上限，60s owned PID/PGID截止；最终exit0、stderr0、host调用0，87个实例，实际峰值20,774,912B，执行2.974s。原件、research module/manifest、全部参与源码、fixtures/results均前后冻结复核；源码副本、连续唯一有序IDs和完整结果已落盘。

完整1073/26967/26591/85718的body/WAT、114个88B声明与tier表从新版原件重新提取。只读SQLite、完整WAT身份校验与20个连续指令guard保留在 `evidence/new-ability0134-static-20261101T025535.134684Z`。最终runtime与源码快照在 `evidence/full0134-oracle-20261101T025358.837028Z/new-ability134-full-20261101T025535.517706Z`；完整摘要见相邻JSON。

先后两次pilot均21例0差异。首轮full2783例原件exit0且全部80B记录匹配，但harness读回把definition override的tuple/list表示当成内容差异；另两个kind1/2成功样例错误套用了默认pending2368的收尾预期，实际进入2159下一轮候选（8个控制字段差异）。此轮完整fixtures/results/process与 `failure-diagnosis.json` 均保留于 `evidence/full0134-oracle-20261101T025358.837028Z/new-ability134-full-20261101T025412.398943Z`。修正JSON interchange后，最终只对已声明的kind0成功收尾与其他kind的入口拒绝域比较控制字段，全部114×tier0..4和modifier数值覆盖完整保留。成功kind1/2收尾、其他pending队列和下一轮生成仍pending。

复现：先运行 `python3 reverse-engineering/scripts/check_new_ability134_full_spec.py --phase pilot`，再以输出的 `full_module_directory` 运行 `--phase full --full-directory <目录>`。没有网络、存档、APK/安装游戏写入、Android WIP改动，也没有stage/commit/push。本结果不声明整核心等价或可玩替代。
