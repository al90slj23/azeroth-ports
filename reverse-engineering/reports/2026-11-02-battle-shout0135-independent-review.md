# Fixed135 learned Battle Shout组件只读独审

**通过声明范围的独审。** 原组件为134个case、外部922入口129次、1076入口37次、2088入口5次，共171次完整入口；本次没有执行原件、模型、checker或builder，没有新增original case或完整880帧。[独审收据](../evidence/battle-shout135-independent-review-20261101T173350.218015Z/review.json) SHA256 `7f035a8d9bc7ceca0a936ba067e9a9a7cc9eddb61383ea872f4ed8e38529ed26`；[结构化报告](2026-11-02-battle-shout0135-independent-review.json)。原[组件收据](../evidence/full0135-oracle-20261101T170642.056245Z/battle-shout135-comparison.json) SHA `df8d400630d16afdeb917d7a0b988ff8e9ac81e42ad856edde653d3d1452a740`，固定`0.135.1 / 90898d5e3`。

旧批94份冻结源的SHA全部匹配，85份生产文件的AST闭包准确。当前差别仅为root之后集成修改的`headless135.py`；不要求它仍等于旧快照，也**不声称旧94份源全部等于当前集成源**。Battle核心SHA仍为`a6ce932dfcc3271bdd8583094f4765b5cd5e50df8a41700716abd05dfa4f661a`，racial/self-buff、player、owned、stats及query helper当前均与冻结版本一致；审阅未改这些源。

原件静态内存像重建确认完整88B定义pointer5467956、effect8、execution9、spell6673、school0；它在learned80中持有，未加入`RACIALS`，与G1256独立。私有模块仅追加922、1076、2088和global0四个export，所有非export section与原件逐字节相同，八个静态函数窗口及原body SHA均核对，原callee没有替换。

独立重比原expected与实际输出，严格对齐9476个已知叶、162个明确未知word，其中18个原件值非零。另以审阅器自写f32运算和状态过滤核对142次直接/内部施放尝试、136次buff追加、6次target30失败、12次同spell owner0稳定替换，以及2次expiry pass。13840个learned80字节、13680个basic80字节及171阶段×23=3933个派生字均严格比较；HP、pools、speed、keys22/28/1109、RNG、三序号与1628 timer也完整落在声明投影中。

三套attempt ledgers在目标检查前更新；busy488或context bit0只抑制第3套，已有6673不重复追加。目标30距离包括严格前/等于/后边界。成功只稳定删除同6673且完整64-bit ownerGUID为0的记录；非零高/低word owner均保留，直接922不会先做全局expiry。新kind8仅+16是未写scratch的未知word；输入type12原有+12/+16按声明保留，独立重建其稳定过滤和到期后的index重映射，没有扩大None掩码或预测其为零。

直接922保留完整owned80/CD。1076逐步f32减dt，到期的施放、失败0.2重试、成功的CD乘数及0.25 floor均独立核对。0.5连续减0.1后，第5步仍为正残量，第6步才实际追加buff。2088先expiry再stat/regen与1076；到期本身不清owned CD，也不自行重施。source gate要求显式无外部来源、六类非live来源为空、raw/semantic live owner一致、支持的live族、有限继承context；icebarrier后续仍pending。9项拒绝只核对既有收据和源逻辑，本次未执行模型重跑。

379帧、第4次选择的Battle Shout tier1记录来自**独立opening/world/gameplay replay输入**，不是新的379帧原件观察。保存的完整80B同时匹配case132的direct922输入和case133的隔离1076输入。前者保留3个learned槽，后者显式只留选中的Battle Shout80，并以Infinity basic/prelude隔离其他工作；两类证据没有混称完整主循环验收。当前root之后的组合批属于另一证据层。

134个fresh实例，878导入全deny、host0；每项外部入口/allocator栈都恢复1048576。32MiB cap，峰值20,578,304B；512MiB heap、独立PGID/60秒预算。原件PID/PGID30375退出0、5.113秒，审阅时均不存在。input/expected/module/world SHA保持；未启动App、未加载原件snapshot。

本结论只覆盖learned effect8的数值、自buff、CD、expiry及所列字段。实际1202原callee存在，但其物理aura/display字段、packet wire和外部proc没有独立完成；非空外部source、完整880与完整一局仍不在该组件验收中。未将本批计数与250/379/400帧组合证据求和。
