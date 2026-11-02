# fixed135：死亡recap1367独立实现与103例原件差分

**103例完整1367差分及异作者只读复核通过。** 新增`core_spec/player_death_recap135.py`，没有修改旧冻结源或shared headless。恢复完整1367的受控显式history48输入域；尚不代表1073历史生产者、5620死亡转换或1938完整通知集成通过。

最终原件收据`evidence/player-death-recap135-oracle-20261101T234514.840259Z/comparison.json`，SHA256 `05c30dcb209a287d5a722f80fa5e10207c8b173fcb8f0866210677157da8d090`。103个fresh实例各调用完整1367一次，0差异；先前3例pilot保留且不加进103计数。模块SHA `8becf091edef1fe406818b89b3b83b52ed7490cf96d10e1810a9226cc453d895`。

## 可执行接口与输入边界

`death_recap135(history: IncomingHistory135, reference_time_bits: int)`返回`(capacity, raw_hex)`；`recap135`返回相同内容及selected_slots、hit_groups、source_groups、原始f32合计词诊断。

原件签名为`(retptr:i32, history_header:i32, reference:f32)->void`，函数体9079788..9086305、6517B，SHA `f5b307b9d13c9e9c899ddca880349c2ba03815cf12508b3669dc02c37db502d7`。借用ring header为capacity/pointer/head/count四词，每行48B：source/name/icon为三组pointer+UTF8字节长度，timestamp24、damage28、absorbed32、HP36、maxHP40、classification44、avoidable45，46..47为未写padding。

输入ring及UTF8内容由调用者显式提供，不声称复建App、资源指针或1073。纯模块不读pointer词/padding，不把未知补零；仅消费已知标量和解析的UTF8三切片。缺timestamp拒绝UnknownRecordRead135；缺UTF8或rank超0..4拒绝UnknownDeathRecap135；UTF8字节长度不匹配拒绝。4项纯model拒绝自检另列，新增原件调用0。

## 恢复的规则

1. 按逻辑ring顺序选`timestamp >= f32(reference−10)`，等号包含，NaN比较失败，未来记录也包含；输入不裁剪、不修改。无selected输出`{}`，实际capacity8。
2. 全部selected分别按原顺序从负零起做f32 damage/absorbed合计；avoidable只计byte45**恰等于1**。输出使用原85719的round：先加带符号的0.4999999702，再按指数清尾数；不是Python的round。JSON数字沿用已恢复52241规则：非finite输出0，普通整数不带小数，其余固定3位。
3. `hits`只合并**相邻**source/name字节相同且f32新timestamp−上一timestamp≤1的行（时间倒退也可满足）。合并后代表指针更新为最新行，damage/abs按新值+旧合计计算，count累加；最终只保留最后8组。
4. `by`跨全部selected按source/name聚合damage/count，代表metadata保留第一行；按damage的f32 total_cmp降序稳定排序，取前6组。icon/rank/avoidable不参与组身份，不能用它们把同source/name拆组。
5. `killer`来自最后selected原始行，`n`是其damage round，`overkill`是round(max(−HP,0))；maxhp也来自最后行。`secs`是reference−第一selected timestamp夹0..10；每个hit的ago≥0，hp=f32(HP/max(maxHP,1))夹0..1。
6. JSON字段顺序为secs,total,absorbed,avoidable,maxhp,killer,hits,by。metadata顺序who/rank/what/icon/mechanic，rank原表为mob/elite/boss/object/none，mechanic按byte45是否非零，所以值2会呈现true但不计avoidable。
7. 每次字符串追加保持原growth `max(capacity×2, required, 8)`，完整UTF8转义、字段次序和capacity与原件比较。结果只给JSON和容量，不预测分配地址或未初始化output backing。

## 验证范围

12个冻结源、7个production、20条完整静态本地导入边，期待先于原件运行，inputs没有期待字段。只新增1367与stack导出；原件非导出section和原函数体不变，878 host imports全部拒绝。

103例覆盖空/过期/恰10秒/未来/NaN时间、1秒与1.0001合并边界、时间倒序、metadata随行改变、全局非相邻归组、最后8/前6、20/21/22/25/33组排序及相等稳定性、负数/半值/−0 round、f32抵消、HP比例和下限、中文/控制字符/emoji UTF8、5个rank、avoidable=2、400行跨环以及部分NaN/Inf数字。完整JSON payload和精确capacity逐例一致，输入header/完整48B backing/字符串在原件前后保持；输出未初始化尾部只观察，不当作已重建字节。

Node63836 exit0、2.3879s/60s、PID/PGID均消失；4447次stack guards，host0，峰值14,614,528B/32MiB，JS cap512MiB。无旧快照、Game/App生产、用户存档或联网访问。

主要边界仍是输入历史的真实生产与所有权、rank超表域、极大metadata/分配失败、1938/5620实际集成、完整880/native/完整一局。此作者报告不冒充异作者审查，也不把已有135或138组件次数搬进本批。

## 独立复核

[异作者只读独审](2026-11-02-player-death-recap0135-independent-review.md)已通过：103份完整JSON／120,301B及容量全部匹配，重新计算1291条选中记录、last8／top6、稳定排序和400环形。78,480B history backing、1648B头、3270B padding保持。原件未落盘字符串原backing；独审绑定实际JSON消费文字，完整strings不变只沿用冻结runner断言，不扩大为rawreadback。没有新增原件或生产执行。
