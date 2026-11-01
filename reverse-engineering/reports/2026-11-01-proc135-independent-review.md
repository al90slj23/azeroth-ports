# 0.135.1 proc事件独立只读复核

最终受限规格独立复核通过。审查发现的context774和致死顺序边界已由作者增加生产守卫；当前仍不支持致死proc组合。

新060138批次855组/1004入口阶段用冻结snapshot模型重算，与保存预期及新原件读回均0声明差异。分项为512个8157 gate返回值、300个984事件阶段、144个914命中阶段、48个922/空2862阶段；这些不是855个完整游戏流程。

36份源码/数据快照和全部artifact摘要匹配，包含core_spec包入口与升级依赖；生产导入闭包完整，未发现生产代码读取原件/结果、网络或子进程。原WASM除export7外逐字节一致，原36导出保留，五个新增研究角色映射正确。此次最终复核时当前文件与冻结来源无漂移。没有重新执行原件。

kind27只更新第一条匹配index：active或NaN expiry按u32加1，过期则1，再unsigned cap。首次append不受cap约束；重复及无效index记录保留。定义有序循环结束后，dirty只重算一次1512。NaN仅在明确浮点路径按分类比较，本批64处原件NaN payload/sign位不同；index/stack/1592/1608/原definition字节严格。额外政策负例证明NaN样式的整数差异不会被放宽。

全部12旧负例的level/cast/definition/owned/ops逐项与新输入一致。新预期由模型生成，新原件也重新调用；没有把旧结果当预期。新验证通过后，独立更新旧预期中的属性、HP、pool、speed和player-key字段，保留的旧48个完整stage对象没有剩余差异。最终855全部预期与此前经纠正855预期一致；旧失败记录和中间收据保持原样，不叠加计数。

## 已解决的输入边界

- `after_accepted_damage`要求显式`context774=0`，缺省None和非0在修改状态前拒绝。真实914的primary+29来自`G774==1`，context0时恒为category0；secondary若发出，则category2、flag34明确写0，与critical无关。因此此零gate域不需要critical参数，但不能推广到其他事件元数据。旧12重放含36次命中，其中24次critical；cap0/duration0终态本身不作为通用critical证明。
- 当前回调要求显式`nonfatal=True`。原914先18353自疗，再death/1417掉落，最后984。组合回调不可直接放在致死的predeath位置；缺省None和False现在拒绝。未来需拆分并验证致死顺序。

全部16项拒绝负例已在最终snapshot中独立重放且与保存拒绝原因一致。生产模型最终SHA `f181d5a9043e7792726ecf8976314dc41e01a493a27421962e433266f2df0e13`。物理Vec容量/allocator、packet/account元数据、其他gate/producer、任意cast系数变化及完整1076流程仍未验收。

最终原件收据：[`proc135-comparison.json`](../evidence/full0135-oracle-20261101T060138.356947Z/proc135-comparison.json)，SHA `92b84ed2ef7588776e510cdda2ffaacfbfe8b18c4b08c983d4fbe9c8f6da1bae`。独立审查：[`review.json`](../evidence/proc135-independent-review-final-20261101T060304.789265Z/review.json)，SHA `d8202bf2a3e8fe0318b9d574133f65ce81e3d0f9adb0f7085f6ccef15d0c3cd2`。旧开放发现保存在此前独立review目录。
