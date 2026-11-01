# 0.135.1 原八种子真实915插入观测

[原件观测收据](../evidence/full0135-oracle-20261101T071318.558372Z/effect-system135-probe-receipt.json)保留8seed与064308的全部动作/固定选卡策略，只在3757之后、921之前插入完整915；不向原件填0、替换队列或覆盖clock。该阶段复用旧独立expected，属于**观察加旧no-op假说比较**，不是新915独立模型验收。后继[072329](2026-11-01-headless-effects0135.md)才用独立915模型重新产生预期并验证。

11309个逐入口snapshot中两Vec始终(cap0,ptr8,len0)，clock2364=0，effect counter2356=0，action sequence1644=1。真实915调用1614次，前后所列状态、双backing和消息均无变化；旧9695个模型阶段仍0差异，8case全部返回、host0。全量捕获2763条packet与22条notification的descriptor和原payload，未声称已恢复这些wire codecs。raw G2592的constructor/final快照及完整队列/backing、玩家动作/位置都保留在原件JSONL。

[独立复核](2026-11-01-effect-system0135-probe-independent-review.md)核对66源/57core、9role/原body/仅export变化、旧expected逐byte身份、从快照重生固定policy、原件消息长度与索引、双storage及三域原始读回；不能从这个有限流程推断所有915分支为空或没有玩法效果。NPC为何不产生动作的额外静态依据见[NPC声明](2026-11-01-npc-effect-producer0135-static.md)。

固定Node22.23.4、512页/512MiB堆/60秒进程组；878导入全部拒绝，未执行应用start、EXE、网络或存档。完整880、真实进场、活跃120B/普通910和独立完整一局仍pending。原始SHA、artifact和各seed观测见[JSON](2026-11-01-effect-system0135-probe.json)。
