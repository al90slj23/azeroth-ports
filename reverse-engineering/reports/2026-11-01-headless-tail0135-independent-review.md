# 0.135.1 十四阶段主尾段独立复核

**8个固定种子、1614帧、22607阶段、11次自然选卡通过，0差异。** 从冻结独立模型重生完整fixture，再逐action重放原保留输出；没有重跑原件或修改作者源。67源/60个core模块含包入口、16个入口签名与body、全部非export字节及导出绑定均通过，当前无源码漂移。

原件输入严格限定为`id/input/region_id/controlled_phase1/zeroed_unit_capacity/zeroed_area_capacity/actions`七个字段，Node另检查精确key集合。独立预期与边界、最终等级等结果元数据均留在进程输入之外。旧082530开发批保留；新082927完整预期、实际结果和模块与旧批逐字节相同，只有checker/runner两源及输入schema变化。除去七个新增阶段和tail/timed字段，原072329固定动作与旧预期仍逐项相等。

每帧实际顺序为player→extra→owned_effects→hits→area→effects→deadline→secondary→ai→collect→claims→spawn→special→terminal。五套新增向量在22607个阶段均观察到capacity0/count0；916两来源为空、975实际调用时无execution11、2376空40B来源、49037为false条件，是本批精确范围。最终选卡后可以留下execution11等未知技能状态，下一帧前停止；不能把组件已恢复的活跃能力直接算入本主循环。

完整128槽NPC与area backing分别独立还原并逐阶段比较1,226,927,104B和254,645,248B，包含52次NPC槽复用及416个非零未写字节。新增975的700817个原始word（135642次非零）与113035个指针（全非零）均保留为sidecar，未预测为零、未写回原件。None放宽仍只限既有pickup arrival与inactive live字段，完整NPC/area backing无mask。

本批实际只有6个area出生、34次tick、4次末槽expiry、4次area复用；未触发非平凡area压缩，19个未写字节的非零复用为0。唯一area死亡来自flamestrike/effect0；blizzard产生151次slow且没有死亡，不能扩展成effect1致死整链验证。Counter独立增量199=122NPC+6area+71pickup，初值总和80、终态总和279。

6个未支持能力停点和2个400帧上限全部保留。seed1/6第二次选择后各继续143帧；seed3第一次选择后继续152帧，最终未支持选择后均未继续。两个预算种子的下一纯模型步骤为pending_due_event，没有新增401帧原件证据。NightElf action sequence2/其它种族1，另与既有416次真实构造、72个职业/种族组合核对，未新增原件调用。

显式phase1研究边界、两套128零槽输入、flat world仍保留。真实1089、4NPC+2kind2进场、资源/碰撞、活跃tail生产者、完整880前段/多人/传输与完整游戏仍未恢复。原件观察器的3038帧/42550快照另列，不追加本独立重建帧数。

[基础复算收据](../evidence/headless-tail0135-independent-review-20261101T083835.290797Z/review.json) SHA `538e2086544aee0f3f911dcb9b2fc612369c8880a20f0d2313add67a19069cae`；[范围补注](../evidence/headless-tail0135-independent-review-20261101T083835.290797Z/coverage-addendum.json)及[机器报告](2026-11-01-headless-tail0135-independent-review.json)记录具体数值。旧review脚本已保存并与Git c4bb83e逐字节吻合。
